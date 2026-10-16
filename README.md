# SmartHire — AI-Powered Recruitment & Job Management Platform

SmartHire is a portfolio-ready full-stack recruitment demo. Candidates can browse jobs and submit applications with a PDF/TXT resume. Recruiters can post jobs, review applicants, see resume/job similarity scores, and update application statuses.

## Features

- Responsive job board with keyword search
- Job details and candidate application form
- Resume text extraction from PDF using **PyMuPDF** (TXT is also supported)
- Resume/job similarity scoring: **Sentence Transformers + FAISS** when optional AI dependencies are installed; a token-overlap fallback otherwise
- Recruiter dashboard to publish jobs and manage applicant statuses
- REST endpoints for jobs and applications
- SQLAlchemy database layer: SQLite locally, PostgreSQL via environment variable or Docker Compose
- Dockerfile and Docker Compose setup

> **Important:** This is a learning/portfolio project, not a production hiring system. The matching score is an approximate similarity signal and must not be used as the sole basis for hiring decisions. The demo does not include authentication/authorization; the recruiter dashboard and write endpoints are open. Add secure authentication, authorization, CSRF protections, rate limits, privacy/retention controls, and tests before production use.

## Run locally

Requires Python 3.11+.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# macOS/Linux:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
uvicorn app.main:app --reload
```

Open:
- App: http://127.0.0.1:8000
- Recruiter dashboard: http://127.0.0.1:8000/recruiter
- Interactive API documentation: http://127.0.0.1:8000/docs
- Jobs API: http://127.0.0.1:8000/api/jobs
- Applications API: http://127.0.0.1:8000/api/applications

The first launch creates the database and seeds three sample jobs.

## Enable semantic matching

Install the optional dependencies:

```bash
pip install -r ai-requirements.txt
```

The first use may download the `all-MiniLM-L6-v2` model. If the optional dependencies/model are unavailable, SmartHire uses its built-in token-overlap fallback.

## Run with Docker + PostgreSQL

Install Docker Desktop, then run:

```bash
docker compose up --build
```

Open http://localhost:8000. To stop:

```bash
docker compose down
```

Data persists in the `postgres_data` Docker volume. For anything beyond local development, replace the sample database password and keep secrets out of Git.

## Project structure

```text
SmartHire/
├── app/
│   ├── main.py             # FastAPI routes and application workflows
│   ├── database.py         # SQLAlchemy engine/session setup
│   ├── models.py           # Job, application, and user data models
│   ├── matching.py         # Semantic matching + fallback scoring
│   ├── resume_parser.py    # PDF/TXT resume parsing
│   ├── templates/          # Jinja2 HTML pages
│   └── static/styles.css  # Responsive styling
├── uploads/                # Uploaded resumes (ignored by Git)
├── requirements.txt
├── ai-requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## API examples

- `GET /api/jobs` — list jobs
- `GET /api/applications` — list applications
- `GET /docs` — try endpoints interactively

## Suggested next improvements

1. Add password hashing, login, and role-based authorization.
2. Add automated tests for job creation, resume upload, and status updates.
3. Add pagination, validation, and upload malware scanning.
4. Add audit logs and candidate data deletion/retention workflows.
5. Add recruiter ownership checks before allowing job/application updates.
