# AI Interview Trainer Agent

>  
> IBM Internship Project · Powered by IBM Granite / watsonx.ai

---

## Overview

**AI Interview Trainer** is a full-stack, production-style web application that prepares users for job interviews using Retrieval-Augmented Generation (RAG) and IBM Granite AI.

Users can upload their resume, configure a mock interview, answer personalised questions, receive real-time AI evaluation, get adaptive follow-up questions, and generate a final performance report with a personalised study plan.

---

## Problem Statement

> *"An Interview Trainer Agent, powered by RAG (Retrieval-Augmented Generation), prepares users for job interviews by generating tailored question sets and preparation strategies based on their profile, experience level, and job role. It retrieves role-specific interview questions, industry expectations, behavioral scenarios, and HR guidelines from recruitment portals, professional networks, and company interview databases."*

---

## Features

| Feature | Description |
|---|---|
| Resume Upload & Analysis | Upload PDF/DOCX/TXT resume; IBM Granite extracts structured information |
| RAG Question Generation | TF-IDF retrieval + IBM Granite generates personalised questions |
| Live Mock Interview | Interactive question-answer interface with real-time evaluation |
| IBM Granite Evaluation | Each answer scored with strengths, weaknesses, model answers |
| Adaptive Follow-ups | Granite generates follow-up questions based on weak answers |
| Performance Report | Detailed final report with category scores and readiness level |
| Analytics Dashboard | Score trends, radar charts, improvement tracking |
| Interview History | View all past interviews with full Q&A review |
| Preparation Plan | Personalised 7-day study plan targeting weak areas |
| Demo Mode | Full UI testing without IBM credentials configured |

---

## Architecture

```
User
 │
 ▼
React Frontend (Vite + Tailwind)
 │  REST API
 ▼
FastAPI Backend
 ├── Profile Service
 ├── Resume Service (PDF/DOCX extraction)
 ├── RAG Service ──► Knowledge Base (TF-IDF Retrieval)
 │                      └── technical/, hr/, behavioral/, guidelines/
 ├── IBM Granite Service ──► IBM watsonx.ai API
 │    ├── Resume Analysis
 │    ├── Question Generation
 │    ├── Answer Evaluation
 │    ├── Follow-up Generation
 │    ├── Report Generation
 │    └── Preparation Plan
 ├── Evaluation Service (score aggregation)
 └── SQLite Database (SQLAlchemy ORM)
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, React Router, Recharts |
| Backend | Python, FastAPI, Uvicorn |
| Database | SQLite (dev), SQLAlchemy ORM |
| AI | IBM Granite via IBM watsonx.ai |
| RAG | Custom TF-IDF retrieval (no heavy dependencies) |
| Resume Parsing | pdfplumber (PDF), python-docx (DOCX) |

---

## RAG Architecture

The RAG system works in three clear stages:

**1. Knowledge Retrieval**
```
knowledge_base/
  technical/  — Python, DSA, System Design, ML questions
  hr/         — HR interview questions and strategies
  behavioral/ — STAR method, behavioral scenarios
  guidelines/ — Evaluation criteria, industry expectations
```

Documents are chunked and indexed using TF-IDF vectors at startup.

**2. Context Construction**
```python
query = f"interview questions for {role} {experience_level} {interview_type}"
chunks = retriever.retrieve(query, top_k=6)
context = format_context(chunks)
```

**3. Granite Generation**
The retrieved context is injected into structured prompts sent to IBM Granite:
```
[Context 1 | technical] ...relevant DSA content...
[Context 2 | behavioral] ...STAR method guidance...

Generate 10 interview questions for: {candidate_profile}
```

---

## IBM Granite Integration

All IBM Granite calls are in `backend/app/services/granite_service.py`.

**Services provided:**
- `analyze_resume()` — Extract structured JSON from resume text
- `generate_questions()` — Create personalised interview questions
- `evaluate_answer()` — Score and provide feedback on answers
- `generate_followup()` — Adaptive follow-up question generation
- `generate_report_summary()` — Final interview report
- `generate_preparation_plan()` — Personalised study plan

**API call flow:**
```
1. Exchange WATSONX_API_KEY for IAM Bearer token
2. POST /ml/v1/text/generation?version=2023-05-29
3. Parse structured JSON response
4. Fall back gracefully on failure
```

---

## Folder Structure

```
ai-interview-trainer/
├── frontend/
│   ├── src/
│   │   ├── components/       Layout.jsx, UI.jsx
│   │   ├── pages/            Landing, Dashboard, Profile, Resume,
│   │   │                     InterviewSetup, LiveInterview, Report,
│   │   │                     Analytics, History, PreparationPlan
│   │   ├── services/         api.js (all API calls)
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
│
├── backend/
│   ├── app/
│   │   ├── main.py           FastAPI app, CORS, startup
│   │   ├── models/           SQLAlchemy ORM models
│   │   ├── schemas/          Pydantic request/response schemas
│   │   ├── routes/           profile, resume, interview, analytics, preparation
│   │   ├── services/
│   │   │   ├── granite_service.py   ← IBM Granite / watsonx.ai
│   │   │   ├── rag_service.py       ← TF-IDF retrieval
│   │   │   ├── resume_service.py    ← PDF/DOCX extraction
│   │   │   └── evaluation_service.py ← Score aggregation
│   │   └── database/
│   │       └── connection.py
│   ├── tests/
│   │   └── test_api.py
│   └── requirements.txt
│
├── knowledge_base/
│   ├── technical/  python_questions.txt, data_structures.txt,
│   │               system_design.txt, machine_learning.txt
│   ├── hr/         hr_questions.txt
│   ├── behavioral/ behavioral_questions.txt
│   └── guidelines/ evaluation_guidelines.txt
│
├── uploads/        (user resume files — not committed)
└── .env.example
```

---

## Installation

### Prerequisites
- Python 3.9+
- Node.js 18+ and npm

### Backend Setup

```bash
cd ai-interview-trainer/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
copy ..\\.env.example .env     # Windows
# cp ../.env.example .env      # macOS/Linux

# Edit .env with your IBM credentials (optional for Demo Mode)
```

### Frontend Setup

```bash
cd ai-interview-trainer/frontend

npm install
```

---

## Running the Application

### Start Backend

```bash
cd ai-interview-trainer/backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: http://localhost:8000  
API docs: http://localhost:8000/docs

### Start Frontend

```bash
cd ai-interview-trainer/frontend
npm run dev
```

Frontend runs at: http://localhost:5173

---

## Environment Configuration

Copy `.env.example` to `.env` in the `backend/` directory:

```env
# IBM watsonx.ai credentials
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_API_KEY=your_ibm_cloud_api_key_here
WATSONX_PROJECT_ID=your_watsonx_project_id_here
GRANITE_MODEL_ID=ibm/granite-13b-chat-v2

# Set to true when running without IBM credentials (default)
# Set to false when Granite credentials are configured above
DEMO_MODE=true

# Database
DATABASE_URL=sqlite:///./interview_trainer.db
```

**Important:** Never commit the `.env` file. It is listed in `.gitignore`.

---

## Demo Mode

When IBM Granite credentials are **not configured**, the application runs in Demo Mode:

- A banner reads: *"Demo Mode — IBM Granite is not currently connected."*
- Resume parsing uses heuristic keyword extraction
- Questions are drawn from a curated static pool
- Answer evaluation uses word-count heuristics
- Follow-up and report generation use deterministic templates

Demo Mode lets you explore the full UI and flow without any credentials.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application info |
| GET | `/api/status` | Granite connection status |
| GET | `/api/profile` | Get candidate profile |
| POST | `/api/profile` | Create/update profile |
| POST | `/api/resume/upload` | Upload and analyse resume |
| GET | `/api/resume/{profile_id}` | Get active resume |
| POST | `/api/interview/create` | Create interview, generate questions |
| GET | `/api/interview/{id}` | Get interview details |
| GET | `/api/interview/{id}/questions` | Get questions |
| POST | `/api/interview/{id}/answer` | Submit answer + get evaluation |
| POST | `/api/interview/{id}/finish` | Complete interview |
| GET | `/api/interview/{id}/report` | Get final report |
| GET | `/api/interview/{id}/rag-sources` | Get RAG knowledge-base sources used for the interview |
| GET | `/api/interviews` | List all interviews |
| GET | `/api/analytics` | Performance analytics |
| GET | `/api/preparation` | List preparation plans |
| POST | `/api/preparation/generate` | Generate new preparation plan |

---

## Database Schema

```
Profile         id, name, email, target_role, experience_level, skills, ...
Resume          id, profile_id, filename, extracted_text, parsed_information
Interview       id, profile_id, type, difficulty, status, scores, readiness_level
Question        id, interview_id, question_text, category, difficulty, is_followup
Answer          id, question_id, answer_text, time_taken_seconds
Evaluation      id, answer_id, score, strengths, weaknesses, suggestions, model_answer
PreparationPlan id, profile_id, interview_id, daily_plan, recommendations
```

---

## Running Tests

```bash
cd ai-interview-trainer/backend
venv\Scripts\activate
pytest tests/ -v
```

Tests cover: profile CRUD, interview creation, question retrieval, answer submission, evaluation, finish, report, analytics, preparation plans.

---

## Interview Flow

```
1. Profile Setup    → Save name, role, experience, skills
2. Resume Upload    → Extract text → IBM Granite analysis → store parsed info
3. Interview Setup  → Choose type, difficulty, count → POST /api/interview/create
4. RAG Retrieval    → Query knowledge base → retrieve relevant chunks
5. Granite Generates→ Personalised questions stored in database
6. Live Interview   → Display question → user answers → POST /api/interview/{id}/answer
7. Evaluation       → IBM Granite scores answer → store evaluation
8. Follow-up        → If score < 8, Granite generates adaptive follow-up
9. Finish           → POST /api/interview/{id}/finish → aggregate scores
10. Report          → GET /api/interview/{id}/report → full analysis + prep plan
```

---

## Future Improvements

- User authentication and multi-user support
- Voice interview mode (speech-to-text)
- More knowledge base documents (Java, C++, DevOps, Cloud)
- Configurable prompt templates via UI
- Export report as PDF
- Company-specific question databases
- Integration with job boards via API

---

## Readiness Levels

| Score | Level |
|---|---|
| ≥ 8.5 | Interview Ready |
| ≥ 7.0 | Strong |
| ≥ 5.5 | Good |
| ≥ 3.5 | Developing |
| < 3.5 | Needs Improvement |

---

*Scores are AI-generated assessment scores and should be used as guidance, not as scientifically validated measurements.*

---

**AI Interview Trainer Agent** · Problem Statement No. 22 · IBM Granite · watsonx.ai
