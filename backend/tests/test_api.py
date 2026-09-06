"""
Basic backend tests for AI Interview Trainer.
Run with: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.connection import Base, get_db

# Use in-memory SQLite for tests — avoids leftover .db files and auto-increment drift.
# StaticPool ensures all connections (create_all + test sessions) share the same
# in-memory database instance.
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Import all models so their tables are registered with Base
    from app.models import profile  # noqa: F401
    from app.models import interview  # noqa: F401
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ── Status ────────────────────────────────────────────────────────────────────

def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app"] == "AI Interview Trainer Agent"
    assert "granite_configured" in data


def test_status(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "demo_mode" in data


# ── Profile ───────────────────────────────────────────────────────────────────

def test_create_profile(client):
    resp = client.post("/api/profile", json={
        "name": "Test Candidate",
        "target_role": "Software Engineer",
        "experience_level": "fresher",
        "skills": "Python, Java",
        "programming_languages": "Python",
        "technologies": "FastAPI, React",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Candidate"
    assert data["target_role"] == "Software Engineer"
    assert data["id"] == 1


def test_get_profile(client):
    resp = client.get("/api/profile?profile_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Candidate"


def test_get_nonexistent_profile(client):
    resp = client.get("/api/profile?profile_id=999")
    assert resp.status_code == 404


# ── Interview ─────────────────────────────────────────────────────────────────

def test_create_interview(client):
    resp = client.post("/api/interview/create", json={
        "profile_id": 1,
        "interview_type": "technical",
        "difficulty": "medium",
        "question_count": 5,
        "target_role": "Software Engineer",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile_id"] == 1
    assert data["interview_type"] == "technical"
    assert data["status"] == "in_progress"
    assert isinstance(data["id"], int)


def test_get_interview(client):
    # First create one
    create_resp = client.post("/api/interview/create", json={
        "profile_id": 1,
        "interview_type": "hr",
        "difficulty": "easy",
        "question_count": 5,
    })
    interview_id = create_resp.json()["id"]

    resp = client.get(f"/api/interview/{interview_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == interview_id


def test_get_questions(client):
    create_resp = client.post("/api/interview/create", json={
        "profile_id": 1,
        "interview_type": "behavioral",
        "difficulty": "medium",
        "question_count": 5,
    })
    interview_id = create_resp.json()["id"]

    resp = client.get(f"/api/interview/{interview_id}/questions")
    assert resp.status_code == 200
    questions = resp.json()
    assert len(questions) >= 1
    assert all("question_text" in q for q in questions)


def test_submit_answer(client):
    # Create interview
    create_resp = client.post("/api/interview/create", json={
        "profile_id": 1,
        "interview_type": "technical",
        "difficulty": "easy",
        "question_count": 5,
    })
    interview_id = create_resp.json()["id"]

    # Get first question
    questions = client.get(f"/api/interview/{interview_id}/questions").json()
    assert len(questions) > 0
    question_id = questions[0]["id"]

    # Submit answer
    resp = client.post(f"/api/interview/{interview_id}/answer", json={
        "question_id": question_id,
        "answer_text": "Python is a high-level programming language known for its readability and versatility.",
        "generate_followup": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "evaluation" in data
    assert "score" in data["evaluation"]


def test_submit_answer_is_demo_field(client):
    """
    Structural contract for is_demo:
    - Must be present at the top level of the answer response.
    - Must be present inside the nested evaluation object.
    - Both values must agree with each other.
    - Value must be a boolean.

    The actual True/False depends on whether IBM Granite credentials are
    configured in the environment: True when using demo fallback, False when
    Granite successfully returns and its JSON is parsed.  Both outcomes are
    valid — what must never happen is a missing key or a mismatch.
    """
    create_resp = client.post("/api/interview/create", json={
        "profile_id": 1,
        "interview_type": "technical",
        "difficulty": "medium",
        "question_count": 5,
    })
    interview_id = create_resp.json()["id"]
    questions = client.get(f"/api/interview/{interview_id}/questions").json()
    question_id = questions[0]["id"]

    resp = client.post(f"/api/interview/{interview_id}/answer", json={
        "question_id": question_id,
        "answer_text": "A BST stores keys so left < root < right, enabling O(log n) search.",
        "generate_followup": False,
    })
    assert resp.status_code == 200
    data = resp.json()

    assert "is_demo" in data, "top-level is_demo field missing"
    assert "is_demo" in data["evaluation"], "is_demo missing from evaluation sub-object"
    assert data["is_demo"] == data["evaluation"]["is_demo"], \
        "top-level and evaluation is_demo must agree"
    assert isinstance(data["is_demo"], bool), "is_demo must be a boolean"


def test_submit_empty_answer(client):
    create_resp = client.post("/api/interview/create", json={
        "profile_id": 1,
        "interview_type": "technical",
        "difficulty": "easy",
        "question_count": 5,
    })
    interview_id = create_resp.json()["id"]
    questions = client.get(f"/api/interview/{interview_id}/questions").json()

    resp = client.post(f"/api/interview/{interview_id}/answer", json={
        "question_id": questions[0]["id"],
        "answer_text": "   ",
        "generate_followup": False,
    })
    assert resp.status_code == 400


def test_finish_interview(client):
    create_resp = client.post("/api/interview/create", json={
        "profile_id": 1,
        "interview_type": "mixed",
        "difficulty": "medium",
        "question_count": 5,
    })
    interview_id = create_resp.json()["id"]

    resp = client.post(f"/api/interview/{interview_id}/finish")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


# ── Analytics ─────────────────────────────────────────────────────────────────

def test_analytics(client):
    resp = client.get("/api/analytics?profile_id=1")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_interviews" in data
    assert "score_history" in data


# ── Preparation ───────────────────────────────────────────────────────────────

def test_preparation_plans(client):
    resp = client.get("/api/preparation?profile_id=1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_generate_preparation_plan(client):
    resp = client.post("/api/preparation/generate?profile_id=1&weak_areas=Python,System+Design")
    assert resp.status_code == 200
    data = resp.json()
    assert "daily_plan" in data or "topics" in data


# ── List interviews ───────────────────────────────────────────────────────────

def test_list_interviews(client):
    resp = client.get("/api/interviews?profile_id=1")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_nonexistent_interview(client):
    resp = client.get("/api/interview/999999")
    assert resp.status_code == 404


# ── Unit tests for JSON extraction helpers ────────────────────────────────────

class TestExtractFirstJsonBlock:
    """Tests for _extract_first_json_block — the depth-tracking extractor."""

    def setup_method(self):
        from app.services.granite_service import _extract_first_json_block
        self.extract = _extract_first_json_block

    def test_plain_object(self):
        assert self.extract('{"a": 1}', '{') == '{"a": 1}'

    def test_plain_array(self):
        assert self.extract('[1, 2, 3]', '[') == '[1, 2, 3]'

    def test_preamble_before_object(self):
        """Granite's actual pattern: text before the JSON block."""
        raw = 'start symbol {\n  "score": 7,\n  "strengths": ["Good"]\n}'
        result = self.extract(raw, '{')
        assert result is not None
        assert result.startswith('{')
        assert result.endswith('}')

    def test_preamble_and_trailing_text(self):
        raw = 'Here is the result: {"key": "value"} some trailing text'
        result = self.extract(raw, '{')
        assert result == '{"key": "value"}'

    def test_stops_at_first_balanced_block(self):
        """Must not grab a later unrelated brace block."""
        raw = 'prefix {"a": 1} suffix {"b": 2}'
        result = self.extract(raw, '{')
        assert result == '{"a": 1}'

    def test_nested_braces(self):
        raw = 'text {"outer": {"inner": 1}} rest'
        result = self.extract(raw, '{')
        assert result == '{"outer": {"inner": 1}}'

    def test_braces_inside_string_ignored(self):
        """Brace characters inside a JSON string value must not affect depth."""
        raw = 'noise {"key": "value with } brace"} trailing'
        result = self.extract(raw, '{')
        assert result == '{"key": "value with } brace"}'

    def test_no_block_returns_none(self):
        assert self.extract('no json here', '{') is None
        assert self.extract('', '[') is None

    def test_escaped_quote_in_string(self):
        raw = 'prefix {"msg": "say \\"hi\\""} suffix'
        result = self.extract(raw, '{')
        assert result == '{"msg": "say \\"hi\\""}'


class TestSafeJson:
    """Tests for _safe_json — should parse the first valid JSON object."""

    def setup_method(self):
        from app.services.granite_service import _safe_json
        self.safe_json = _safe_json

    def test_clean_json(self):
        result = self.safe_json('{"score": 8, "strengths": ["clear"]}')
        assert result == {"score": 8, "strengths": ["clear"]}

    def test_preamble_text_before_json(self):
        """This is the exact Granite failure pattern from the bug report."""
        raw = (
            'start symbol {\n'
            '  "score": 7,\n'
            '  "strengths": ["Good explanation"],\n'
            '  "weaknesses": ["Missing depth"],\n'
            '  "missing_points": ["Examples"],\n'
            '  "suggestions": ["Add examples"],\n'
            '  "model_answer": "A better answer...",\n'
            '  "key_concepts": ["concept"],\n'
            '  "category_scores": {"relevance": 7.0}\n'
            '}'
        )
        result = self.safe_json(raw)
        assert result is not None, "Should parse despite preamble text"
        assert result["score"] == 7
        assert result["strengths"] == ["Good explanation"]

    def test_trailing_text_after_json(self):
        raw = '{"score": 9} Note: this is great!'
        result = self.safe_json(raw)
        assert result == {"score": 9}

    def test_both_preamble_and_trailing(self):
        raw = 'My evaluation:\n{"score": 6}\nHope this helps.'
        result = self.safe_json(raw)
        assert result is not None
        assert result["score"] == 6

    def test_returns_none_for_garbage(self):
        assert self.safe_json("no json at all") is None
        assert self.safe_json("") is None
        assert self.safe_json("score: 7, strengths: good") is None

    def test_stops_at_first_object_not_last(self):
        """Greedy regex bug: must NOT grab to the last } in the string."""
        raw = '{"score": 5} {"score": 10}'
        result = self.safe_json(raw)
        assert result is not None
        assert result["score"] == 5

    def test_nested_object(self):
        raw = 'Result: {"outer": {"inner": 42}}'
        result = self.safe_json(raw)
        assert result == {"outer": {"inner": 42}}


class TestExtractJsonArray:
    """Tests for _extract_json_array."""

    def setup_method(self):
        from app.services.granite_service import _extract_json_array
        self.extract = _extract_json_array

    def test_clean_array(self):
        result = self.extract('[{"q": "Q1"}, {"q": "Q2"}]')
        assert len(result) == 2
        assert result[0]["q"] == "Q1"

    def test_preamble_before_array(self):
        raw = 'Here are your questions:\n[{"question_text": "Explain X", "category": "technical"}]'
        result = self.extract(raw)
        assert result is not None
        assert result[0]["question_text"] == "Explain X"

    def test_trailing_text(self):
        raw = '[{"q": "Q1"}]\nEnd of list.'
        result = self.extract(raw)
        assert result is not None
        assert result[0]["q"] == "Q1"

    def test_returns_none_for_garbage(self):
        assert self.extract("no array here") is None
