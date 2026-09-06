import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.profile import Profile
from app.models.interview import Interview, Question, Answer, Evaluation, PreparationPlan
from app.models.interview import Resume
from app.schemas.schemas import (
    InterviewCreate, InterviewResponse, QuestionResponse,
    AnswerSubmit, AnswerResponse, EvaluationResponse,
    FollowupRequest, ReportResponse,
)
from app.services import granite_service, rag_service, evaluation_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interview", tags=["Interview"])


# ── Create Interview ──────────────────────────────────────────────────────────

@router.post("/create", response_model=InterviewResponse)
def create_interview(data: InterviewCreate, db: Session = Depends(get_db)):
    """Create a new interview session and generate questions."""
    profile = db.query(Profile).filter(Profile.id == data.profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    # Resolve target role
    target_role = data.target_role or profile.target_role

    # Get resume context
    resume = db.query(Resume).filter(
        Resume.profile_id == data.profile_id, Resume.is_active == 1
    ).first()
    resume_info = resume.parsed_information if resume else {}

    # Build RAG context
    skills_list = [s.strip() for s in (profile.skills or "").split(",") if s.strip()]
    rag_context = rag_service.retrieve_context(
        role=target_role,
        skills=skills_list,
        interview_type=data.interview_type,
        experience_level=profile.experience_level,
        additional_context=profile.job_description or "",
    )

    # Generate questions via Granite
    profile_dict = {
        "name": profile.name,
        "target_role": target_role,
        "experience_level": profile.experience_level,
        "skills": profile.skills or "",
        "programming_languages": profile.programming_languages or "",
        "technologies": profile.technologies or "",
        "target_company": data.target_company or profile.target_company or "",
        "job_description": profile.job_description or "",
    }

    questions_data = granite_service.generate_questions(
        profile=profile_dict,
        interview_type=data.interview_type,
        difficulty=data.difficulty,
        count=data.question_count,
        rag_context=rag_context,
        resume_info=resume_info or {},
    )

    # Persist interview
    interview = Interview(
        profile_id=data.profile_id,
        interview_type=data.interview_type,
        difficulty=data.difficulty,
        question_count=data.question_count,
        target_role=target_role,
        target_company=data.target_company or profile.target_company,
        status="in_progress",
        rag_context=rag_context[:5000],
    )
    db.add(interview)
    db.flush()  # get interview.id

    for idx, q in enumerate(questions_data):
        question = Question(
            interview_id=interview.id,
            question_text=q["question_text"],
            category=q.get("category", data.interview_type),
            difficulty=q.get("difficulty", data.difficulty),
            order_index=idx,
            is_followup=0,
        )
        db.add(question)

    db.commit()
    db.refresh(interview)
    return interview


# ── Get Interview ─────────────────────────────────────────────────────────────

@router.get("/{interview_id}", response_model=InterviewResponse)
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return interview


@router.get("/{interview_id}/questions", response_model=List[QuestionResponse])
def get_questions(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")
    questions = (
        db.query(Question)
        .filter(Question.interview_id == interview_id)
        .order_by(Question.order_index)
        .all()
    )
    return questions


@router.get("/{interview_id}/rag-sources")
def get_rag_sources(interview_id: int, db: Session = Depends(get_db)):
    """Return the RAG knowledge-base sources used for this interview."""

    interview = db.query(Interview).filter(
        Interview.id == interview_id
    ).first()

    if not interview:
        raise HTTPException(
            status_code=404,
            detail="Interview not found."
        )

    rag_context = interview.rag_context or ""

    sources = []
    seen = set()

    # RAG context format:
    # [Context 1 | Source: filename.txt | Category: technical]
    pattern = r"\[Context\s+\d+\s+\|\s+Source:\s*(.*?)\s+\|\s+Category:\s*(.*?)\]"

    import re

    for match in re.finditer(pattern, rag_context):
        source = match.group(1).strip()
        category = match.group(2).strip()

        key = (source, category)

        if key not in seen:
            seen.add(key)
            sources.append({
                "source": source,
                "category": category,
            })

    return {
        "interview_id": interview_id,
        "rag_enabled": bool(sources),
        "sources": sources,
    }


# ── Submit Answer ─────────────────────────────────────────────────────────────

@router.post("/{interview_id}/answer")
def submit_answer(interview_id: int, data: AnswerSubmit, db: Session = Depends(get_db)):
    """Submit an answer, evaluate it, and optionally generate a follow-up."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")

    question = db.query(Question).filter(Question.id == data.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    if not data.answer_text or not data.answer_text.strip():
        raise HTTPException(status_code=400, detail="Answer text cannot be empty.")

    # Check for existing answer
    existing = db.query(Answer).filter(Answer.question_id == data.question_id).first()
    if existing:
        existing.answer_text = data.answer_text
        answer = existing
    else:
        answer = Answer(
            question_id=data.question_id,
            answer_text=data.answer_text,
            time_taken_seconds=data.time_taken_seconds,
        )
        db.add(answer)
        db.flush()

    # Evaluate answer via Granite
    profile = db.query(Profile).filter(Profile.id == interview.profile_id).first()
    profile_dict = {
        "name": profile.name if profile else "Candidate",
        "target_role": interview.target_role or "",
        "experience_level": profile.experience_level if profile else "fresher",
    }

    eval_data = granite_service.evaluate_answer(
        question=question.question_text,
        category=question.category or interview.interview_type,
        answer=data.answer_text,
        profile=profile_dict,
    )

    # Persist evaluation
    if existing and existing.evaluation:
        ev = existing.evaluation
        ev.score = eval_data.get("score")
        ev.strengths = eval_data.get("strengths")
        ev.weaknesses = eval_data.get("weaknesses")
        ev.missing_points = eval_data.get("missing_points")
        ev.suggestions = eval_data.get("suggestions")
        ev.model_answer = eval_data.get("model_answer")
        ev.key_concepts = eval_data.get("key_concepts")
        ev.category_scores = eval_data.get("category_scores")
    else:
        ev = Evaluation(
            answer_id=answer.id,
            score=eval_data.get("score"),
            strengths=eval_data.get("strengths"),
            weaknesses=eval_data.get("weaknesses"),
            missing_points=eval_data.get("missing_points"),
            suggestions=eval_data.get("suggestions"),
            model_answer=eval_data.get("model_answer"),
            key_concepts=eval_data.get("key_concepts"),
            category_scores=eval_data.get("category_scores"),
        )
        db.add(ev)

    db.commit()

    # Generate follow-up if requested and score < 8
    followup_question = None

    current_question_count = db.query(Question).filter(
        Question.interview_id == interview_id
    ).count()

    if (
        data.generate_followup
        and eval_data.get("score", 10) < 8
        and current_question_count < interview.question_count
    ):
        fu_data = granite_service.generate_followup(
            previous_question=question.question_text,
            answer=data.answer_text,
            evaluation=eval_data,
            profile=profile_dict,
            interview_type=interview.interview_type,
        )

        if fu_data and fu_data.get("question_text"):
            fu_q = Question(
                interview_id=interview_id,
                question_text=fu_data["question_text"],
                category=fu_data.get("category", question.category),
                difficulty=fu_data.get("difficulty", question.difficulty),
                order_index=current_question_count,
                is_followup=1,
                parent_question_id=question.id,
            )
            db.add(fu_q)
            db.commit()
            db.refresh(fu_q)

            followup_question = {
                "id": fu_q.id,
                "question_text": fu_q.question_text,
                "category": fu_q.category,
                "difficulty": fu_q.difficulty,
                "is_followup": 1,
                "reason": fu_data.get("reason", ""),
            }

    db.refresh(answer)
    # is_demo is explicitly set to True by _demo_evaluation and False by Granite path.
    # Default to False here so that a missing key never incorrectly shows the Demo banner.
    eval_is_demo = eval_data.get("is_demo", False)
    return {
        "answer_id": answer.id,
        "evaluation": {
            "score": eval_data.get("score"),
            "strengths": eval_data.get("strengths", []),
            "weaknesses": eval_data.get("weaknesses", []),
            "missing_points": eval_data.get("missing_points", []),
            "suggestions": eval_data.get("suggestions", []),
            "model_answer": eval_data.get("model_answer", ""),
            "key_concepts": eval_data.get("key_concepts", []),
            "category_scores": eval_data.get("category_scores", {}),
            "is_demo": eval_is_demo,
        },
        "followup_question": followup_question,
        "is_demo": eval_is_demo,
    }


# ── Finish Interview ──────────────────────────────────────────────────────────

@router.post("/{interview_id}/finish")
def finish_interview(interview_id: int, db: Session = Depends(get_db)):
    """Mark interview complete and compute aggregate scores."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")

    if interview.status == "completed":
        return {"message": "Interview already completed.", "interview_id": interview_id}

    # Load all answered questions
    questions = db.query(Question).filter(Question.interview_id == interview_id).all()
    evaluations_raw = []
    for q in questions:
        if q.answer and q.answer.evaluation:
            e = q.answer.evaluation
            evaluations_raw.append({
                "score": e.score,
                "question_category": q.category or interview.interview_type,
                "weaknesses": e.weaknesses or [],
                "category_scores": e.category_scores or {},
            })

    scores = evaluation_service.aggregate_scores(evaluations_raw)
    weak_areas = evaluation_service.identify_weak_areas(evaluations_raw)
    readiness = evaluation_service.readiness_level(scores["overall_score"])

    interview.overall_score = scores["overall_score"]
    interview.technical_score = scores["technical_score"]
    interview.hr_score = scores["hr_score"]
    interview.behavioral_score = scores["behavioral_score"]
    interview.communication_score = scores["communication_score"]
    interview.relevance_score = scores["relevance_score"]
    interview.completeness_score = scores["completeness_score"]
    interview.readiness_level = readiness
    interview.status = "completed"
    interview.completed_at = datetime.utcnow()

    db.commit()

    return {
        "interview_id": interview_id,
        "status": "completed",
        "overall_score": scores["overall_score"],
        "readiness_level": readiness,
    }


# ── Report ────────────────────────────────────────────────────────────────────

@router.get("/{interview_id}/report")
def get_report(interview_id: int, db: Session = Depends(get_db)):
    """Generate and return the final interview report."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found.")

    profile = db.query(Profile).filter(Profile.id == interview.profile_id).first()
    questions = (
        db.query(Question)
        .filter(Question.interview_id == interview_id)
        .order_by(Question.order_index)
        .all()
    )

    qa_pairs = []
    questions_well = []
    questions_poor = []
    all_evals_raw = []

    for q in questions:
        if q.answer and q.answer.evaluation:
            e = q.answer.evaluation
            qa = {
                "question": q.question_text,
                "answer": q.answer.answer_text,
                "score": e.score,
                "category": q.category,
                "strengths": e.strengths or [],
                "weaknesses": e.weaknesses or [],
                "suggestions": e.suggestions or [],
                "model_answer": e.model_answer or "",
            }
            qa_pairs.append(qa)
            all_evals_raw.append({
                "score": e.score,
                "question_category": q.category or interview.interview_type,
                "weaknesses": e.weaknesses or [],
                "category_scores": e.category_scores or {},
            })
            if (e.score or 0) >= 6.5:
                questions_well.append({"question": q.question_text[:120], "score": e.score})
            else:
                questions_poor.append({
                    "question": q.question_text[:120],
                    "score": e.score,
                    "suggestions": (e.suggestions or [])[:2],
                })

    profile_dict = {
        "name": profile.name if profile else "Candidate",
        "target_role": interview.target_role or (profile.target_role if profile else ""),
    }

    overall_score = interview.overall_score
    if overall_score is None:
        scores = evaluation_service.aggregate_scores(all_evals_raw)
        overall_score = scores["overall_score"] or 0.0

    report_meta = granite_service.generate_report_summary(
        profile=profile_dict,
        interview_type=interview.interview_type,
        overall_score=overall_score,
        qa_pairs=qa_pairs,
    )

    weak_areas = evaluation_service.identify_weak_areas(all_evals_raw)

    # Generate preparation plan
    prep_plan = granite_service.generate_preparation_plan(
        profile=profile_dict,
        weak_areas=weak_areas,
        recommended_topics=report_meta.get("recommended_topics", []),
    )

    # Persist prep plan
    plan_record = PreparationPlan(
        profile_id=interview.profile_id,
        interview_id=interview_id,
        topics=report_meta.get("recommended_topics", []),
        daily_plan=prep_plan.get("daily_plan", []),
        weak_areas=weak_areas,
        recommendations=prep_plan.get("overall_recommendations", []),
    )
    db.add(plan_record)
    db.commit()

    readiness = interview.readiness_level or evaluation_service.readiness_level(overall_score)

    return {
        "interview_id": interview_id,
        "candidate_name": profile.name if profile else "Candidate",
        "target_role": interview.target_role or "",
        "interview_type": interview.interview_type,
        "date": interview.completed_at.isoformat() if interview.completed_at else interview.created_at.isoformat(),
        "question_count": len(questions),
        "overall_score": overall_score,
        "technical_score": interview.technical_score,
        "hr_score": interview.hr_score,
        "behavioral_score": interview.behavioral_score,
        "communication_score": interview.communication_score,
        "relevance_score": interview.relevance_score,
        "completeness_score": interview.completeness_score,
        "readiness_level": readiness,
        "strong_areas": report_meta.get("strong_areas", []),
        "weak_areas": report_meta.get("weak_areas", weak_areas[:5]),
        "questions_answered_well": questions_well,
        "questions_needing_improvement": questions_poor,
        "recommended_topics": report_meta.get("recommended_topics", []),
        "preparation_plan": prep_plan,
        "summary": report_meta.get("summary", ""),
        "key_feedback": report_meta.get("key_feedback", ""),
        "qa_pairs": qa_pairs,
        "is_demo": report_meta.get("is_demo", True),
    }


# ── List All Interviews ───────────────────────────────────────────────────────

@router.get("s", response_model=List[InterviewResponse])
def list_interviews(profile_id: int = 1, db: Session = Depends(get_db)):
    return (
        db.query(Interview)
        .filter(Interview.profile_id == profile_id)
        .order_by(Interview.created_at.desc())
        .all()
    )
