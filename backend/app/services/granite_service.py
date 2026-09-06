"""
IBM Granite Service
-------------------
All IBM watsonx.ai / Granite API calls are centralised here.
Credentials are read exclusively from environment variables — never hard-coded.

Required environment variables:
  WATSONX_URL          – e.g. https://us-south.ml.cloud.ibm.com
  WATSONX_API_KEY      – IBM Cloud IAM API key
  WATSONX_PROJECT_ID   – watsonx.ai project ID
  GRANITE_MODEL_ID     – e.g. ibm/granite-13b-chat-v2
  DEMO_MODE            – set to "true" to use demo responses when Granite is unavailable
"""

import os
import json
import logging
import re
import requests
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

WATSONX_URL = os.getenv("WATSONX_URL", "")
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
GRANITE_MODEL_ID = os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-chat-v2")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

# Token cache
_iam_token: Optional[str] = None
_iam_token_expiry: float = 0.0


def is_granite_configured() -> bool:
    """Return True if all required Granite credentials are set."""
    return bool(WATSONX_URL and WATSONX_API_KEY and WATSONX_PROJECT_ID)


def _get_iam_token() -> Optional[str]:
    """Obtain a short-lived IAM Bearer token from IBM Cloud."""
    global _iam_token, _iam_token_expiry
    import time

    if _iam_token and time.time() < _iam_token_expiry - 60:
        return _iam_token

    try:
        resp = requests.post(
            "https://iam.cloud.ibm.com/identity/token",
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": WATSONX_API_KEY,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        _iam_token = data["access_token"]
        _iam_token_expiry = time.time() + data.get("expires_in", 3600)
        return _iam_token
    except Exception as exc:
        logger.error("Failed to obtain IAM token: %s", exc)
        return None


def _call_granite(prompt: str, max_tokens: int = 1024) -> Optional[str]:
    """
    Send a prompt to IBM Granite via watsonx.ai and return the generated text.
    Returns None on failure.
    """
    if not is_granite_configured():
        logger.warning("Granite not configured — skipping API call.")
        return None

    token = _get_iam_token()
    if not token:
        return None

    url = f"{WATSONX_URL.rstrip('/')}/ml/v1/text/generation?version=2023-05-29"
    payload = {
        "model_id": GRANITE_MODEL_ID,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": max_tokens,
            "min_new_tokens": 10,
            "stop_sequences": [],
            "repetition_penalty": 1.1,
        },
        "project_id": WATSONX_PROJECT_ID,
    }

    try:
        resp = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        generated = result["results"][0]["generated_text"]
        return generated.strip()
    except Exception as exc:
        logger.error("Granite API call failed: %s", exc)
        return None


def _extract_first_json_block(text: str, open_char: str) -> Optional[str]:
    """
    Return the substring of *text* that forms the first balanced JSON
    object (open_char='{') or array (open_char='[').

    Uses character-level depth tracking so it is not fooled by greedy
    regexes that grab too much when Granite adds text before or after the
    JSON payload.
    """
    close_char = '}' if open_char == '{' else ']'
    depth = 0
    in_string = False
    escape_next = False
    start = None

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == open_char:
            if depth == 0:
                start = i
            depth += 1
        elif ch == close_char:
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    return text[start:i + 1]
    return None


def _safe_json(text: str) -> Optional[Dict]:
    """
    Extract and parse the first valid JSON *object* from *text*.

    Handles Granite responses that include preamble text such as
    "start symbol {" before the actual JSON payload.
    Falls back to a JSON array if no object is found.
    """
    # Fast path: the whole string is valid JSON already
    try:
        result = json.loads(text)
        if isinstance(result, (dict, list)):
            return result
    except Exception:
        pass

    # Try to extract first balanced { ... } block
    block = _extract_first_json_block(text, '{')
    if block:
        try:
            result = json.loads(block)
            if isinstance(result, dict):
                return result
        except Exception:
            pass

    # Try to extract first balanced [ ... ] block (object wrapped in array edge case)
    block = _extract_first_json_block(text, '[')
    if block:
        try:
            result = json.loads(block)
            # If it's a list with one dict, unwrap it
            if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict):
                return result[0]
            if isinstance(result, dict):
                return result
        except Exception:
            pass

    return None


# ── Resume Analysis ───────────────────────────────────────────────────────────

RESUME_ANALYSIS_PROMPT = """You are an expert resume parser. Analyze the resume text below and extract structured information.
Return ONLY a valid JSON object with these exact keys:
{{
  "name": "candidate full name or null",
  "email": "email or null",
  "education": ["degree - institution - year", ...],
  "skills": ["skill1", "skill2", ...],
  "programming_languages": ["Python", "Java", ...],
  "technologies": ["React", "Docker", ...],
  "projects": [{{"name": "...", "description": "...", "tech_stack": ["..."]}}],
  "internships": [{{"company": "...", "role": "...", "duration": "..."}}],
  "experience": [{{"company": "...", "role": "...", "duration": "...", "highlights": ["..."]}}],
  "certifications": ["cert1", ...],
  "achievements": ["achievement1", ...]
}}

Resume:
{resume_text}

JSON:"""


def analyze_resume(resume_text: str) -> Dict[str, Any]:
    """Parse resume text with IBM Granite. Falls back to demo output."""
    if is_granite_configured():
        prompt = RESUME_ANALYSIS_PROMPT.format(resume_text=resume_text[:4000])
        raw = _call_granite(prompt, max_tokens=800)
        if raw:
            parsed = _safe_json(raw)
            if parsed:
                return {**parsed, "is_demo": False}

    # Demo fallback
    logger.info("Using demo resume analysis.")
    return _demo_resume_analysis(resume_text)


def _demo_resume_analysis(text: str) -> Dict[str, Any]:
    """Heuristic-based resume parsing used in demo mode."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    name = lines[0] if lines else "Candidate"

    skills = []
    langs = []
    techs = []

    skill_keywords = ["python", "java", "javascript", "sql", "react", "node", "docker",
                      "kubernetes", "ml", "machine learning", "deep learning", "nlp",
                      "tensorflow", "pytorch", "scikit", "pandas", "numpy", "flask",
                      "fastapi", "django", "spring", "c++", "c#", "go", "rust", "aws",
                      "azure", "gcp", "git", "html", "css"]
    lang_kw = ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
               "ruby", "kotlin", "swift", "r", "scala", "php"]
    tech_kw = ["react", "angular", "vue", "node", "docker", "kubernetes", "tensorflow",
               "pytorch", "flask", "fastapi", "django", "spring", "mongodb", "postgresql",
               "mysql", "redis", "aws", "azure", "gcp", "git", "linux"]

    lower_text = text.lower()
    for kw in skill_keywords:
        if kw in lower_text:
            skills.append(kw.title())
    for kw in lang_kw:
        if kw in lower_text:
            langs.append(kw.title())
    for kw in tech_kw:
        if kw in lower_text:
            techs.append(kw.title())

    return {
        "name": name,
        "email": None,
        "education": [],
        "skills": list(set(skills))[:10],
        "programming_languages": list(set(langs))[:8],
        "technologies": list(set(techs))[:10],
        "projects": [],
        "internships": [],
        "experience": [],
        "certifications": [],
        "achievements": [],
        "is_demo": True,
    }


# ── Question Generation ───────────────────────────────────────────────────────

QUESTION_GEN_PROMPT = """You are an expert technical interviewer at a leading tech company.
Generate exactly {count} interview questions for the following candidate profile.

Candidate:
- Name: {name}
- Target Role: {role}
- Experience Level: {experience}
- Skills: {skills}
- Programming Languages: {languages}
- Technologies: {technologies}
- Resume Highlights: {resume_highlights}

Interview Configuration:
- Type: {interview_type}
- Difficulty: {difficulty}
- Target Company: {company}

Retrieved Interview Context:
{rag_context}

Job Description Context:
{job_description}

IMPORTANT RULES:
1. Make questions specific to the candidate's background — reference their projects, skills, and experience.
2. Vary question types: conceptual, problem-solving, situational, and experience-based.
3. Mix difficulties appropriately for {difficulty} level.
4. Return ONLY a JSON array of question objects:

[
  {{
    "question_text": "question here",
    "category": "technical|hr|behavioral",
    "difficulty": "easy|medium|hard"
  }},
  ...
]

JSON Array:"""


def generate_questions(
    profile: Dict,
    interview_type: str,
    difficulty: str,
    count: int,
    rag_context: str,
    resume_info: Optional[Dict] = None,
) -> List[Dict]:
    """Generate interview questions using IBM Granite. Falls back to demo questions."""

    resume_info = resume_info or {}
    highlights = _build_resume_highlights(resume_info)

    if is_granite_configured():
        prompt = QUESTION_GEN_PROMPT.format(
            count=count,
            name=profile.get("name", "Candidate"),
            role=profile.get("target_role", "Software Engineer"),
            experience=profile.get("experience_level", "fresher"),
            skills=profile.get("skills", ""),
            languages=profile.get("programming_languages", ""),
            technologies=profile.get("technologies", ""),
            resume_highlights=highlights,
            interview_type=interview_type,
            difficulty=difficulty,
            company=profile.get("target_company", "a leading tech company"),
            rag_context=rag_context[:2000],
            job_description=profile.get("job_description", "Not provided")[:500],
        )
        raw = _call_granite(prompt, max_tokens=1500)
        if raw:
            parsed = _extract_json_array(raw)
            if parsed and len(parsed) >= 1:
                return [
                    {
                        "question_text": q.get("question_text", ""),
                        "category": q.get("category", interview_type),
                        "difficulty": q.get("difficulty", difficulty),
                        "is_demo": False,
                    }
                    for q in parsed
                    if q.get("question_text")
                ][:count]

    logger.info("Using demo question generation.")
    return _demo_questions(profile, interview_type, difficulty, count, resume_info)


def _build_resume_highlights(resume_info: Dict) -> str:
    parts = []
    if resume_info.get("projects"):
        for p in resume_info["projects"][:3]:
            if isinstance(p, dict):
                parts.append(f"Project: {p.get('name', '')} - {p.get('description', '')}")
    if resume_info.get("experience"):
        for e in resume_info["experience"][:2]:
            if isinstance(e, dict):
                parts.append(f"Experience: {e.get('role', '')} at {e.get('company', '')}")
    if resume_info.get("skills"):
        parts.append(f"Key Skills: {', '.join(resume_info['skills'][:8])}")
    return "\n".join(parts) if parts else "No resume information available."


def _extract_json_array(text: str) -> Optional[List]:
    """
    Extract and parse the first valid JSON *array* from *text*.

    Uses the same depth-tracking extractor as _safe_json so that preamble
    text before the array (e.g. "Here are the questions: [...]") does not
    prevent successful parsing.
    """
    # Fast path
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except Exception:
        pass

    # Depth-tracking extraction of first [ ... ] block
    block = _extract_first_json_block(text, '[')
    if block:
        try:
            result = json.loads(block)
            if isinstance(result, list):
                return result
        except Exception:
            pass

    return None


def _demo_questions(
    profile: Dict, interview_type: str, difficulty: str, count: int, resume_info: Dict
) -> List[Dict]:
    """Return deterministic demo questions based on role and type."""
    role = profile.get("target_role", "Software Engineer").lower()

    technical_pool = [
        ("Explain the difference between a list and a tuple in Python.", "technical", "easy"),
        ("What is the time complexity of binary search and why?", "technical", "medium"),
        ("Describe the SOLID principles in object-oriented design.", "technical", "medium"),
        ("How does garbage collection work in Java/Python?", "technical", "medium"),
        ("Explain the CAP theorem for distributed systems.", "technical", "hard"),
        ("What is the difference between SQL JOIN types?", "technical", "easy"),
        ("Describe how a REST API works and its key constraints.", "technical", "easy"),
        ("What are the differences between supervised and unsupervised learning?", "technical", "medium"),
        ("Explain overfitting and how to prevent it in machine learning models.", "technical", "medium"),
        ("What is a microservices architecture and its trade-offs?", "technical", "hard"),
        ("How would you design a URL shortening service?", "technical", "hard"),
        ("Explain the concept of indexing in databases.", "technical", "medium"),
        ("What is Docker and how does containerisation work?", "technical", "medium"),
        ("Describe the differences between TCP and UDP.", "technical", "medium"),
        ("What is a deadlock and how do you prevent it?", "technical", "hard"),
    ]

    hr_pool = [
        ("Tell me about yourself and your background.", "hr", "easy"),
        ("Why are you interested in this role?", "hr", "easy"),
        ("Where do you see yourself in five years?", "hr", "medium"),
        ("What are your greatest strengths and weaknesses?", "hr", "easy"),
        ("Why do you want to work at our company?", "hr", "medium"),
        ("How do you handle tight deadlines and pressure?", "hr", "medium"),
        ("Describe your ideal work environment.", "hr", "easy"),
        ("What motivates you in your work?", "hr", "easy"),
        ("How do you prioritise your tasks when you have multiple deadlines?", "hr", "medium"),
        ("What do you know about our company and industry?", "hr", "medium"),
    ]

    behavioral_pool = [
        ("Tell me about a time you faced a challenging technical problem. How did you solve it?", "behavioral", "medium"),
        ("Describe a situation where you had to work under pressure to meet a deadline.", "behavioral", "medium"),
        ("Tell me about a time you worked in a team and had a conflict. How did you resolve it?", "behavioral", "medium"),
        ("Describe a project where you took initiative and the outcome.", "behavioral", "medium"),
        ("Tell me about a mistake you made and what you learned from it.", "behavioral", "medium"),
        ("Describe a time you had to learn something new quickly.", "behavioral", "medium"),
        ("Tell me about a time you had to explain a complex concept to a non-technical audience.", "behavioral", "medium"),
        ("Describe a situation where you had to adapt to a significant change.", "behavioral", "medium"),
        ("Tell me about a time you demonstrated leadership.", "behavioral", "hard"),
        ("Describe a time you received critical feedback and how you responded.", "behavioral", "medium"),
    ]

    if interview_type == "technical":
        pool = technical_pool
    elif interview_type == "hr":
        pool = hr_pool
    elif interview_type == "behavioral":
        pool = behavioral_pool
    else:  # mixed
        pool = technical_pool[:6] + hr_pool[:4] + behavioral_pool[:5]

    questions = [
        {"question_text": q[0], "category": q[1], "difficulty": q[2], "is_demo": True}
        for q in pool[:count]
    ]
    # Pad if needed
    while len(questions) < count:
        questions.append({
            "question_text": f"Tell me about your experience with {profile.get('target_role', 'this role')}.",
            "category": "hr",
            "difficulty": "easy",
            "is_demo": True,
        })
    return questions[:count]


# ── Answer Evaluation ─────────────────────────────────────────────────────────

EVALUATION_PROMPT = """You are a senior interviewer and career coach evaluating a candidate's interview answer.

Question: {question}

Question Category: {category}

Candidate's Answer: {answer}

Candidate Role: {role}

Experience Level: {experience}

Your task is to evaluate the candidate's answer.

IMPORTANT: Your entire response MUST be exactly ONE valid JSON object.

DO NOT:
- write explanations before the JSON
- write explanations after the JSON
- write comments
- write Markdown
- use ```json or ``` fences
- repeat the question
- describe these instructions
- output plain text
- output anything except the JSON object

The JSON object MUST have exactly this structure:

{{
  "score": 7,
  "strengths": ["specific strength"],
  "weaknesses": ["specific weakness"],
  "missing_points": ["specific missing point"],
  "suggestions": ["specific improvement"],
  "model_answer": "A strong model answer written as a complete sentence.",
  "key_concepts": ["concept1", "concept2"],
  "category_scores": {{
    "technical_correctness": 7,
    "relevance": 8,
    "completeness": 6,
    "communication": 8,
    "clarity": 8
  }}
}}

STRICT RULES:
- "score" must be a number from 0 to 10.
- "technical_correctness" must be a number from 0 to 10, or null for a non-technical question.
- "relevance", "completeness", "communication", and "clarity" must be numbers from 0 to 10.
- Every array item MUST be a double-quoted string.
- Never put unquoted text inside an array.
- Never use single quotes.
- Never leave a string unquoted.
- Never add trailing commas.
- Use valid JSON syntax that Python json.loads() can parse.
- If something is not applicable, use [] for that array.
- Give specific feedback based on the candidate's actual answer.
- Do not mention these instructions in your response.

Before responding, verify that the complete response is valid JSON.

RETURN ONLY THE JSON OBJECT."""


def evaluate_answer(
    question: str,
    category: str,
    answer: str,
    profile: Dict,
) -> Dict[str, Any]:
    """Evaluate a candidate's answer using IBM Granite."""

    if is_granite_configured():
        prompt = EVALUATION_PROMPT.format(
            question=question,
            category=category,
            answer=answer[:2000],
            role=profile.get("target_role", "Software Engineer"),
            experience=profile.get("experience_level", "fresher"),
        )
        raw = _call_granite(prompt, max_tokens=1500)
        if raw is None:
            # _call_granite already logged the HTTP/token error; fall through to demo
            logger.warning("evaluate_answer: Granite call returned None — using demo fallback.")
        else:
            parsed = _safe_json(raw)
            if parsed:
                return {**parsed, "is_demo": False}
            else:
                # Granite responded but output was not parseable JSON.
                # Log the raw output so it can be diagnosed, then fall through to demo.
                logger.error(
                    "evaluate_answer: Granite returned non-JSON output. "
                    "Raw (first 500 chars): %s",
                    raw[:500],
                )

    logger.info("evaluate_answer: using demo evaluation fallback.")
    return _demo_evaluation(question, category, answer)


def _demo_evaluation(question: str, category: str, answer: str) -> Dict[str, Any]:
    """Heuristic demo evaluation based on answer length and keywords."""
    word_count = len(answer.split())

    if word_count < 10:
        score = 2.0
        strengths = ["Attempted to answer"]
        weaknesses = ["Answer is too brief", "Lacks detail and explanation"]
        missing = ["Specific examples", "Technical depth", "Structured response"]
        suggestions = ["Expand your answer with examples", "Use the STAR method for behavioral questions",
                       "Include relevant technical details"]
    elif word_count < 30:
        score = 4.5
        strengths = ["Addressed the question", "Shows basic awareness"]
        weaknesses = ["Could be more detailed", "Missing examples"]
        missing = ["Concrete examples", "Deeper technical explanation"]
        suggestions = ["Add specific examples from your experience",
                       "Explain your reasoning process",
                       "Mention relevant technologies or methods"]
    elif word_count < 80:
        score = 6.5
        strengths = ["Good coverage of the topic", "Clear communication"]
        weaknesses = ["Could include more depth in technical aspects"]
        missing = ["Edge cases or limitations", "Alternative approaches"]
        suggestions = ["Consider discussing trade-offs",
                       "Add specific metrics or outcomes where possible"]
    else:
        score = 8.0
        strengths = ["Comprehensive answer", "Well-structured response", "Shows good understanding"]
        weaknesses = ["Minor areas could be expanded"]
        missing = ["Quantified outcomes (if applicable)"]
        suggestions = ["Continue practising structured responses", "Great depth — keep it up"]

    return {
        "score": score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missing_points": missing,
        "suggestions": suggestions,
        "model_answer": f"A strong answer to '{question[:80]}...' would include specific examples, technical accuracy, clear structure, and demonstrated understanding of core concepts.",
        "key_concepts": ["Communication skills", "Technical depth", "Structured thinking"],
        "category_scores": {
            "technical_correctness": score if category == "technical" else None,
            "relevance": min(score + 0.5, 10),
            "completeness": score - 0.5 if word_count < 50 else score,
            "communication": score,
            "clarity": score,
        },
        "is_demo": True,
    }


# ── Follow-up Question ────────────────────────────────────────────────────────

FOLLOWUP_PROMPT = """You are an experienced interviewer conducting a live interview.
Based on the previous exchange, generate ONE relevant follow-up question.

Previous Question: {previous_question}
Candidate's Answer: {answer}
Answer Score: {score}/10
Weaknesses identified: {weaknesses}
Candidate Role: {role}
Interview Type: {interview_type}

Generate a follow-up question that:
1. Probes deeper into a weak area or unclear part of the answer
2. Is specific and targeted
3. Helps the interviewer better understand the candidate's knowledge

Return ONLY a JSON object:
{{
  "question_text": "your follow-up question here",
  "category": "technical|hr|behavioral",
  "difficulty": "easy|medium|hard",
  "reason": "brief reason for this follow-up"
}}

JSON:"""


def generate_followup(
    previous_question: str,
    answer: str,
    evaluation: Dict,
    profile: Dict,
    interview_type: str,
) -> Optional[Dict]:
    """Generate a follow-up question based on the previous answer."""

    if is_granite_configured():
        weaknesses = ", ".join(evaluation.get("weaknesses", [])[:3])
        prompt = FOLLOWUP_PROMPT.format(
            previous_question=previous_question,
            answer=answer[:1000],
            score=evaluation.get("score", 5),
            weaknesses=weaknesses or "Not specified",
            role=profile.get("target_role", "Software Engineer"),
            interview_type=interview_type,
        )
        raw = _call_granite(prompt, max_tokens=300)
        if raw is None:
            logger.warning("generate_followup: Granite call returned None — using demo fallback.")
        else:
            parsed = _safe_json(raw)
            if parsed and parsed.get("question_text"):
                return {**parsed, "is_demo": False}
            else:
                logger.error(
                    "generate_followup: Granite returned non-JSON output. "
                    "Raw (first 300 chars): %s",
                    raw[:300],
                )

    logger.info("generate_followup: using demo fallback.")
    return _demo_followup(previous_question, evaluation)


def _demo_followup(previous_question: str, evaluation: Dict) -> Dict:
    weaknesses = evaluation.get("weaknesses", [])
    if weaknesses:
        reason = weaknesses[0]
        followup = f"Could you elaborate more on '{reason.lower()}'? Can you give a specific example?"
    else:
        followup = f"Can you provide a concrete example from your experience to support your answer?"

    return {
        "question_text": followup,
        "category": "behavioral",
        "difficulty": "medium",
        "reason": "Probing for more specific details",
        "is_demo": True,
    }


# ── Final Report ──────────────────────────────────────────────────────────────

REPORT_PROMPT = """You are generating a final interview performance report.

Candidate: {name}
Role: {role}
Interview Type: {interview_type}
Questions Answered: {question_count}
Overall Score: {overall_score}/10

Per-question performance:
{qa_summary}

Generate a comprehensive report summary and return ONLY a JSON object:
{{
  "strong_areas": ["area1", "area2"],
  "weak_areas": ["area1", "area2"],
  "readiness_level": "Needs Improvement|Developing|Good|Strong|Interview Ready",
  "summary": "2-3 sentence overall summary",
  "recommended_topics": ["topic1", "topic2", "topic3"],
  "key_feedback": "Most important thing the candidate should work on"
}}

JSON:"""


def generate_report_summary(
    profile: Dict,
    interview_type: str,
    overall_score: float,
    qa_pairs: List[Dict],
) -> Dict[str, Any]:
    """Generate final report using IBM Granite."""

    if is_granite_configured():
        qa_summary = "\n".join([
            f"Q{i+1}: {q.get('question', '')[:100]} | Score: {q.get('score', 'N/A')}/10"
            for i, q in enumerate(qa_pairs[:10])
        ])
        prompt = REPORT_PROMPT.format(
            name=profile.get("name", "Candidate"),
            role=profile.get("target_role", "Software Engineer"),
            interview_type=interview_type,
            question_count=len(qa_pairs),
            overall_score=round(overall_score, 1),
            qa_summary=qa_summary,
        )
        raw = _call_granite(prompt, max_tokens=500)
        if raw:
            parsed = _safe_json(raw)
            if parsed:
                return {**parsed, "is_demo": False}

    logger.info("Using demo report generation.")
    return _demo_report(overall_score)


def _demo_report(score: float) -> Dict[str, Any]:
    if score >= 8.0:
        level = "Interview Ready"
        summary = "Excellent performance across all areas. The candidate demonstrates strong knowledge, clear communication, and well-structured responses."
        strong = ["Technical knowledge", "Communication", "Problem-solving"]
        weak = ["Could add more quantified examples"]
    elif score >= 6.5:
        level = "Strong"
        summary = "Good overall performance with solid understanding of core concepts. Some areas could benefit from deeper technical detail."
        strong = ["Core concepts", "Communication clarity"]
        weak = ["Technical depth", "Specific examples"]
    elif score >= 5.0:
        level = "Good"
        summary = "Decent performance showing foundational knowledge. Key areas need improvement before interview readiness."
        strong = ["Basic awareness of topics"]
        weak = ["Technical depth", "Structured responses", "Specific examples"]
    elif score >= 3.5:
        level = "Developing"
        summary = "Some foundational knowledge present but significant improvement needed across technical and communication areas."
        strong = ["Enthusiasm and willingness to learn"]
        weak = ["Technical fundamentals", "Answer structure", "Depth of knowledge"]
    else:
        level = "Needs Improvement"
        summary = "Considerable preparation needed. Focus on fundamentals, structured thinking, and practising mock interviews."
        strong = ["Identified areas for growth"]
        weak = ["Technical fundamentals", "Communication", "Answer structure", "Depth"]

    return {
        "strong_areas": strong,
        "weak_areas": weak,
        "readiness_level": level,
        "summary": summary,
        "recommended_topics": ["Data Structures & Algorithms", "System Design", "Behavioral Interview Prep",
                                "Communication Skills", "Technical Fundamentals"],
        "key_feedback": f"Focus on {weak[0].lower()} to significantly improve your interview performance.",
        "is_demo": True,
    }


# ── Preparation Plan ──────────────────────────────────────────────────────────

PREP_PROMPT = """You are a career coach creating a personalised interview preparation plan.

Candidate: {name}
Target Role: {role}
Experience Level: {experience}
Weak Areas: {weak_areas}
Recommended Topics: {topics}

Create a 7-day study plan and return ONLY a JSON object:
{{
  "daily_plan": [
    {{"day": 1, "focus": "topic", "activities": ["activity1", "activity2"], "resources": ["resource1"]}},
    ...
  ],
  "overall_recommendations": ["rec1", "rec2", "rec3"],
  "priority_topics": ["topic1", "topic2"]
}}

JSON:"""


def generate_preparation_plan(
    profile: Dict,
    weak_areas: List[str],
    recommended_topics: List[str],
) -> Dict[str, Any]:
    """Generate a personalised preparation plan using IBM Granite."""

    if is_granite_configured():
        prompt = PREP_PROMPT.format(
            name=profile.get("name", "Candidate"),
            role=profile.get("target_role", "Software Engineer"),
            experience=profile.get("experience_level", "fresher"),
            weak_areas=", ".join(weak_areas[:5]),
            topics=", ".join(recommended_topics[:6]),
        )
        raw = _call_granite(prompt, max_tokens=1500)
        if raw:
            parsed = _safe_json(raw)
            if parsed:
                return {**parsed, "is_demo": False}

    logger.info("Using demo preparation plan.")
    return _demo_prep_plan(weak_areas, recommended_topics)


def _demo_prep_plan(weak_areas: List[str], topics: List[str]) -> Dict[str, Any]:
    default_topics = topics if topics else ["Data Structures", "Algorithms", "System Design",
                                             "OOP", "SQL", "Python Fundamentals", "Behavioral Prep"]
    plan = []
    for i, topic in enumerate(default_topics[:7], 1):
        plan.append({
            "day": i,
            "focus": topic,
            "activities": [
                f"Study {topic} concepts and theory",
                f"Solve 3-5 practice problems on {topic}",
                f"Review and revise key definitions",
            ],
            "resources": [
                f"LeetCode — {topic} tag",
                "GeeksforGeeks",
                "YouTube tutorials",
            ],
        })

    return {
        "daily_plan": plan,
        "overall_recommendations": [
            "Practice answering questions aloud to improve fluency",
            "Use the STAR method for all behavioral questions",
            "Review your projects and be ready to discuss them in depth",
            "Research the company and role thoroughly before the interview",
        ],
        "priority_topics": (weak_areas[:3] if weak_areas else default_topics[:3]),
        "is_demo": True,
    }
