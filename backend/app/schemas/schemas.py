from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any, Dict
from datetime import datetime


# ── Profile ──────────────────────────────────────────────────────────────────

class ProfileCreate(BaseModel):
    name: str
    email: Optional[str] = None
    target_role: str
    experience_level: str
    education: Optional[str] = None
    skills: Optional[str] = None
    programming_languages: Optional[str] = None
    technologies: Optional[str] = None
    target_company: Optional[str] = None
    job_description: Optional[str] = None


class ProfileUpdate(ProfileCreate):
    pass


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: Optional[str]
    target_role: str
    experience_level: str
    education: Optional[str]
    skills: Optional[str]
    programming_languages: Optional[str]
    technologies: Optional[str]
    target_company: Optional[str]
    job_description: Optional[str]
    created_at: datetime
    updated_at: datetime


# ── Resume ───────────────────────────────────────────────────────────────────

class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int
    filename: str
    parsed_information: Optional[Dict[str, Any]]
    upload_date: datetime
    is_active: int


# ── Interview ─────────────────────────────────────────────────────────────────

class InterviewCreate(BaseModel):
    profile_id: int
    interview_type: str  # technical, hr, behavioral, mixed
    difficulty: str      # easy, medium, hard, adaptive
    question_count: int = Field(default=10, ge=5, le=15)
    target_role: Optional[str] = None
    target_company: Optional[str] = None


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int
    interview_type: str
    difficulty: str
    question_count: int
    target_role: Optional[str]
    target_company: Optional[str]
    status: str
    overall_score: Optional[float]
    technical_score: Optional[float]
    hr_score: Optional[float]
    behavioral_score: Optional[float]
    communication_score: Optional[float]
    readiness_level: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


# ── Question ──────────────────────────────────────────────────────────────────

class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    interview_id: int
    question_text: str
    category: Optional[str]
    difficulty: Optional[str]
    order_index: int
    is_followup: int


# ── Answer ────────────────────────────────────────────────────────────────────

class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: str
    time_taken_seconds: Optional[int] = None
    generate_followup: bool = True


class AnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_id: int
    answer_text: str
    submitted_at: datetime


# ── Evaluation ────────────────────────────────────────────────────────────────

class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    answer_id: int
    score: Optional[float]
    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]
    missing_points: Optional[List[str]]
    suggestions: Optional[List[str]]
    model_answer: Optional[str]
    key_concepts: Optional[List[str]]
    category_scores: Optional[Dict[str, float]]


# ── Followup ─────────────────────────────────────────────────────────────────

class FollowupRequest(BaseModel):
    interview_id: int
    previous_question_id: int
    generate: bool = True


# ── Report ────────────────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    interview_id: int
    candidate_name: str
    target_role: str
    interview_type: str
    date: str
    question_count: int
    overall_score: float
    technical_score: Optional[float]
    hr_score: Optional[float]
    behavioral_score: Optional[float]
    communication_score: Optional[float]
    relevance_score: Optional[float]
    completeness_score: Optional[float]
    readiness_level: str
    strong_areas: List[str]
    weak_areas: List[str]
    questions_answered_well: List[Dict]
    questions_needing_improvement: List[Dict]
    recommended_topics: List[str]
    preparation_plan: Optional[Dict]
    summary: str
    is_demo: bool = False


# ── Analytics ─────────────────────────────────────────────────────────────────

class AnalyticsResponse(BaseModel):
    total_interviews: int
    average_score: Optional[float]
    best_score: Optional[float]
    score_history: List[Dict]
    category_averages: Dict[str, Optional[float]]
    weak_skill_areas: List[str]
    improvement_trend: str


# ── Preparation Plan ──────────────────────────────────────────────────────────

class PreparationPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    profile_id: int
    interview_id: Optional[int]
    topics: Optional[List[str]]
    daily_plan: Optional[List[Dict]]
    weak_areas: Optional[List[str]]
    recommendations: Optional[List[str]]
    created_at: datetime
