import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.profile import Profile
from app.models.interview import Resume
from app.schemas.schemas import ResumeResponse
from app.services import resume_service, granite_service
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume", tags=["Resume"])

MAX_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024


@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    profile_id: int = Form(default=1),
    db: Session = Depends(get_db),
):
    """Upload and parse a resume file (PDF / DOCX / TXT)."""
    if not resume_service.allowed_file(file.filename or ""):
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, or TXT.")

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_BYTES // (1024*1024)} MB limit.")

    # Ensure profile exists
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create a profile first.")

    # Save file
    try:
        file_path = resume_service.save_upload(content, file.filename or "resume.pdf", profile_id)
    except Exception as exc:
        logger.error("File save failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

    # Extract text
    extracted_text, err = resume_service.extract_text(file_path, file.filename or "")
    if err:
        logger.warning("Text extraction warning: %s", err)
        # Don't fail entirely — store with empty text and note
        extracted_text = extracted_text or ""

    # Analyse with Granite
    parsed_info = {}
    if extracted_text:
        parsed_info = granite_service.analyze_resume(extracted_text)
        # Update profile with extracted info
        _update_profile_from_resume(profile, parsed_info, db)
    else:
        parsed_info = {"error": err or "No text extracted", "is_demo": True}

    # Deactivate old resumes
    db.query(Resume).filter(Resume.profile_id == profile_id).update({"is_active": 0})

    # Save resume record
    resume = Resume(
        profile_id=profile_id,
        filename=file.filename or "resume",
        file_path=file_path,
        extracted_text=extracted_text[:20000] if extracted_text else "",
        parsed_information=parsed_info,
        is_active=1,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def _update_profile_from_resume(profile: Profile, parsed: dict, db: Session):
    """Backfill profile fields from parsed resume if they are empty."""
    if not profile.name or profile.name == "Candidate":
        extracted_name = parsed.get("name")
        if extracted_name:
            profile.name = extracted_name

    if not profile.skills:
        skills = parsed.get("skills", [])
        if skills:
            profile.skills = ", ".join(skills)

    if not profile.programming_languages:
        langs = parsed.get("programming_languages", [])
        if langs:
            profile.programming_languages = ", ".join(langs)

    if not profile.technologies:
        techs = parsed.get("technologies", [])
        if techs:
            profile.technologies = ", ".join(techs)

    db.commit()


@router.get("/{profile_id}", response_model=ResumeResponse)
def get_resume(profile_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(
        Resume.profile_id == profile_id, Resume.is_active == 1
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found for this profile.")
    return resume
