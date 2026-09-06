# conftest.py — shared pytest fixtures
import os
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_interview_trainer.db")
