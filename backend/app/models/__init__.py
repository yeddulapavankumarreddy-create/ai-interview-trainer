from app.models.profile import Profile
from app.models.interview import Interview, Question, Answer, Evaluation, PreparationPlan, Resume

# Re-export as module-level attributes so tests can do:
#   from app.models import profile, resume, interview
import app.models.profile as profile  # noqa
import app.models.interview as resume   # noqa (Resume lives here)
import app.models.interview as interview  # noqa

__all__ = [
    "Profile",
    "Resume",
    "Interview",
    "Question",
    "Answer",
    "Evaluation",
    "PreparationPlan",
]
