from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models.interview import PreparationPlan
from app.models.profile import Profile
from app.schemas.schemas import PreparationPlanResponse
from app.services import granite_service

router = APIRouter(prefix="/api/preparation", tags=["Preparation"])


@router.get("", response_model=List[PreparationPlanResponse])
def get_preparation_plans(profile_id: int = 1, db: Session = Depends(get_db)):
    """Return all preparation plans for a profile."""
    plans = (
        db.query(PreparationPlan)
        .filter(PreparationPlan.profile_id == profile_id)
        .order_by(PreparationPlan.created_at.desc())
        .all()
    )
    return plans


@router.post("/generate")
def generate_plan(
    profile_id: int = 1,
    weak_areas: str = "",
    db: Session = Depends(get_db),
):
    """Generate a fresh preparation plan on demand."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    weak_list = [w.strip() for w in weak_areas.split(",") if w.strip()]
    profile_dict = {
        "name": profile.name,
        "target_role": profile.target_role,
        "experience_level": profile.experience_level,
    }

    plan_data = granite_service.generate_preparation_plan(
        profile=profile_dict,
        weak_areas=weak_list,
        recommended_topics=[],
    )

    plan = PreparationPlan(
        profile_id=profile_id,
        topics=plan_data.get("priority_topics", []),
        daily_plan=plan_data.get("daily_plan", []),
        weak_areas=weak_list,
        recommendations=plan_data.get("overall_recommendations", []),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan
