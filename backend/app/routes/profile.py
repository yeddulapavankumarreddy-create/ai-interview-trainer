from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.profile import Profile
from app.schemas.schemas import ProfileCreate, ProfileUpdate, ProfileResponse
from datetime import datetime

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(profile_id: int = 1, db: Session = Depends(get_db)):
    """Get profile by ID (defaults to 1 for single-user mode)."""
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("", response_model=ProfileResponse)
def create_or_update_profile(data: ProfileCreate, db: Session = Depends(get_db)):
    """Create or update the candidate profile (upsert on id=1)."""
    profile = db.query(Profile).filter(Profile.id == 1).first()
    if profile:
        for field, value in data.model_dump().items():
            setattr(profile, field, value)
        profile.updated_at = datetime.utcnow()
    else:
        profile = Profile(**data.model_dump())
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(profile_id: int, data: ProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in data.model_dump().items():
        setattr(profile, field, value)
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile
