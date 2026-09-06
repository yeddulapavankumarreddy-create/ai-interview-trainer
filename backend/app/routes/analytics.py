from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from statistics import mean

from app.database.connection import get_db
from app.models.interview import Interview, Question, Answer, Evaluation
from app.services.evaluation_service import readiness_level

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("")
def get_analytics(profile_id: int = 1, db: Session = Depends(get_db)):
    """Return performance analytics for a candidate."""
    interviews = (
        db.query(Interview)
        .filter(Interview.profile_id == profile_id, Interview.status == "completed")
        .order_by(Interview.created_at)
        .all()
    )

    if not interviews:
        return {
            "total_interviews": 0,
            "average_score": None,
            "best_score": None,
            "score_history": [],
            "category_averages": {
                "technical": None,
                "hr": None,
                "behavioral": None,
                "communication": None,
            },
            "weak_skill_areas": [],
            "improvement_trend": "No data yet",
        }

    scores = [i.overall_score for i in interviews if i.overall_score is not None]
    avg_score = round(mean(scores), 2) if scores else None
    best_score = round(max(scores), 2) if scores else None

    score_history = [
        {
            "date": i.created_at.strftime("%Y-%m-%d"),
            "score": i.overall_score,
            "type": i.interview_type,
            "readiness": i.readiness_level,
        }
        for i in interviews
        if i.overall_score is not None
    ]

    # Category averages
    tech_scores = [i.technical_score for i in interviews if i.technical_score is not None]
    hr_scores = [i.hr_score for i in interviews if i.hr_score is not None]
    beh_scores = [i.behavioral_score for i in interviews if i.behavioral_score is not None]
    comm_scores = [i.communication_score for i in interviews if i.communication_score is not None]

    # Collect weak areas across all evaluations
    interview_ids = [i.id for i in interviews]
    weak_areas_set = set()
    questions = db.query(Question).filter(Question.interview_id.in_(interview_ids)).all()
    for q in questions:
        if q.answer and q.answer.evaluation:
            for w in (q.answer.evaluation.weaknesses or []):
                if w:
                    weak_areas_set.add(w)

    # Trend
    trend = "No trend"
    if len(scores) >= 2:
        diff = scores[-1] - scores[0]
        if diff > 1.0:
            trend = "Improving"
        elif diff < -1.0:
            trend = "Declining"
        else:
            trend = "Stable"

    return {
        "total_interviews": len(interviews),
        "average_score": avg_score,
        "best_score": best_score,
        "score_history": score_history,
        "category_averages": {
            "technical": round(mean(tech_scores), 2) if tech_scores else None,
            "hr": round(mean(hr_scores), 2) if hr_scores else None,
            "behavioral": round(mean(beh_scores), 2) if beh_scores else None,
            "communication": round(mean(comm_scores), 2) if comm_scores else None,
        },
        "weak_skill_areas": list(weak_areas_set)[:8],
        "improvement_trend": trend,
    }
