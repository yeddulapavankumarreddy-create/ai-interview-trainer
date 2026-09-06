from app.database.connection import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=True)
    target_role = Column(String(200), nullable=False)
    experience_level = Column(String(50), nullable=False)  # student, fresher, 0-2, 2-5, 5+
    education = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)  # comma-separated
    programming_languages = Column(Text, nullable=True)
    technologies = Column(Text, nullable=True)
    target_company = Column(String(200), nullable=True)
    job_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    resumes = relationship("Resume", back_populates="profile", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="profile", cascade="all, delete-orphan")
    preparation_plans = relationship("PreparationPlan", back_populates="profile", cascade="all, delete-orphan")
