# AI Interview Simulator

An AI-powered technical interview preparation platform with automated question generation, real-time response evaluation, detailed performance analytics, and targeted skill gap analysis.

---

## Project Structure

```text
AI-Interview-Simulator/
├── backend/                  # FastAPI & SQLAlchemy Backend
│   ├── app/
│   │   ├── api/routes/       # Endpoints: users, job roles, interview sessions, AI
│   │   ├── core/             # Configuration & security
│   │   ├── database/         # Database engine & base
│   │   ├── models/           # SQLAlchemy DB Models
│   │   ├── schemas/          # Pydantic Schemas
│   │   └── services/         # Groq LLM generators & evaluators
│   ├── .env                  # DB connection & Groq API key
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # Vite + React + Tailwind Frontend
│   ├── src/
│   │   ├── components/       # UI Components
│   │   ├── pages/            # Interview, Dashboard, Results, Roles, Auth
│   │   ├── services/         # API client & fallback analytics
│   │   └── utils/            # Local storage helpers
│   ├── .env.local            # Frontend API URL (http://127.0.0.1:8000)
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

---

## Getting Started

### 1. Run Backend (FastAPI + PostgreSQL)

```bash
cd backend

# Activate Python virtual environment
.\venv\Scripts\activate

# Start FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Backend API: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health / DB check: `http://127.0.0.1:8000/db-test`

### 2. Run Frontend (Vite + React)

```bash
cd frontend

# Start Vite dev server
npm run dev
```

- Frontend App: `http://localhost:5173`

---

## Features & AI Capabilities

- **PostgreSQL Database Integration**: Persistent storage of users, interview sessions, questions, candidate answers, scores, feedback reports, and skill gaps.
- **Dynamic Question Generation**: Groq LLM generates realistic, varied, role-specific questions for each interview round across multiple focus areas.
- **Real-Time Answer Evaluation**: Candidate responses are evaluated by LLM for technical accuracy, clarity, and relevance.
- **AI Analytics & Feedback Report**: Scores candidate answers, pinpoints specific strengths, highlights growth areas, and provides actionable coaching tips.
- **Skill Gap & Resource Recommendations**: Evaluates competencies against industry benchmarks and recommends targeted books, documentation, and practice resources.
