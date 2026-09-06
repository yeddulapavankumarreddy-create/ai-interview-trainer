from app.database.connection import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    filename = Column(String(300), nullable=False)
    file_path = Column(String(500), nullable=True)
    extracted_text = Column(Text, nullable=True)
    parsed_information = Column(JSON, nullable=True)  # structured JSON from Granite
    upload_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1 = active

    profile = relationship("Profile", back_populates="resumes")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    interview_type = Column(String(50), nullable=False)  # technical, hr, behavioral, mixed
    difficulty = Column(String(50), nullable=False)  # easy, medium, hard, adaptive
    question_count = Column(Integer, default=10)
    target_role = Column(String(200), nullable=True)
    target_company = Column(String(200), nullable=True)
    status = Column(String(50), default="in_progress")  # in_progress, completed
    overall_score = Column(Float, nullable=True)
    technical_score = Column(Float, nullable=True)
    hr_score = Column(Float, nullable=True)
    behavioral_score = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    completeness_score = Column(Float, nullable=True)
    readiness_level = Column(String(50), nullable=True)
    report_data = Column(JSON, nullable=True)
    rag_context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    profile = relationship("Profile", back_populates="interviews")
    questions = relationship("Question", back_populates="interview", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)  # technical, hr, behavioral
    difficulty = Column(String(50), nullable=True)
    order_index = Column(Integer, default=0)
    is_followup = Column(Integer, default=0)
    parent_question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False, cascade="all, delete-orphan")
    followups = relationship("Question", foreign_keys=[parent_question_id])


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    time_taken_seconds = Column(Integer, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="answer")
    evaluation = relationship("Evaluation", back_populates="answer", uselist=False, cascade="all, delete-orphan")


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False)
    score = Column(Float, nullable=True)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    missing_points = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)
    model_answer = Column(Text, nullable=True)
    key_concepts = Column(JSON, nullable=True)
    category_scores = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    answer = relationship("Answer", back_populates="evaluation")


class PreparationPlan(Base):
    __tablename__ = "preparation_plans"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    interview_id = Column(Integer, ForeignKey("interviews.id"), nullable=True)
    topics = Column(JSON, nullable=True)
    daily_plan = Column(JSON, nullable=True)
    weak_areas = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="preparation_plans")
