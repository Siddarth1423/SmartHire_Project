import os
import shutil
from pathlib import Path
from fastapi import FastAPI, Depends, Form, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from .database import Base, engine, get_db
from .models import Job, Application
from .resume_parser import extract_resume_text
from .matching import match_score

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt"}

app = FastAPI(title="SmartHire", description="AI-powered recruitment and job management demo")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    # Add a few starter jobs only when the database is empty.
    from .database import SessionLocal
    db = SessionLocal()
    try:
        if db.query(Job).count() == 0:
            db.add_all([
                Job(title="Python Full Stack Developer", company="Northstar Labs", location="Bengaluru / Hybrid",
                    description="Build REST APIs, responsive interfaces, and reliable backend services. Work with Python, FastAPI, SQL databases, Git, and Docker.",
                    skills="Python, FastAPI, REST APIs, SQL, HTML, CSS, JavaScript, Docker, Git"),
                Job(title="Junior Data Analyst", company="BluePeak Analytics", location="Remote",
                    description="Prepare datasets, write SQL queries, build dashboards, and communicate insights to business teams.",
                    skills="SQL, Python, Pandas, Excel, Power BI, data visualization"),
                Job(title="Backend Engineer Intern", company="Orbit Systems", location="Bengaluru",
                    description="Help implement APIs, database models, automated tests, and containerized development workflows.",
                    skills="Python, FastAPI, PostgreSQL, REST APIs, Docker, testing"),
            ])
            db.commit()
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: str = "", db: Session = Depends(get_db)):
    stmt = select(Job).order_by(Job.created_at.desc())
    jobs = db.scalars(stmt).all()
    if q.strip():
        query = q.lower().strip()
        jobs = [j for j in jobs if query in f"{j.title} {j.company} {j.location} {j.description} {j.skills}".lower()]
    return templates.TemplateResponse("index.html", {"request": request, "jobs": jobs, "q": q})

@app.get("/jobs/{job_id}", response_class=HTMLResponse)
def job_detail(job_id: int, request: Request, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse("job_detail.html", {"request": request, "job": job})

@app.post("/jobs/{job_id}/apply")
async def apply(job_id: int, candidate_name: str = Form(...), candidate_email: str = Form(...),
                cover_letter: str = Form(""), resume: UploadFile = File(...), db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not candidate_name.strip() or "@" not in candidate_email:
        raise HTTPException(status_code=400, detail="Enter a valid name and email.")
    suffix = Path(resume.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Upload a PDF or TXT resume.")
    contents = await resume.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Resume must be 5 MB or smaller.")
    safe_name = f"job{job_id}_{os.urandom(8).hex()}{suffix}"
    path = UPLOAD_DIR / safe_name
    path.write_bytes(contents)
    try:
        resume_text = extract_resume_text(str(path))
        score = match_score(resume_text, f"{job.title}\n{job.description}\n{job.skills}")
        application = Application(
            candidate_name=candidate_name.strip(), candidate_email=candidate_email.strip().lower(),
            resume_filename=safe_name, resume_text=resume_text, cover_letter=cover_letter.strip(),
            job_id=job.id, match_score=score
        )
        db.add(application)
        db.commit()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return RedirectResponse(url=f"/applications/success?score={score}", status_code=303)

@app.get("/applications/success", response_class=HTMLResponse)
def application_success(request: Request, score: float = 0):
    return templates.TemplateResponse("success.html", {"request": request, "score": score})

@app.get("/recruiter", response_class=HTMLResponse)
def recruiter_dashboard(request: Request, db: Session = Depends(get_db)):
    jobs = db.scalars(select(Job).options(joinedload(Job.applications)).order_by(Job.created_at.desc())).unique().all()
    return templates.TemplateResponse("recruiter.html", {"request": request, "jobs": jobs})

@app.post("/recruiter/jobs")
def create_job(title: str = Form(...), company: str = Form(...), location: str = Form("Remote"),
               description: str = Form(...), skills: str = Form(""), db: Session = Depends(get_db)):
    if not title.strip() or not company.strip() or not description.strip():
        raise HTTPException(status_code=400, detail="Title, company, and description are required.")
    db.add(Job(title=title.strip(), company=company.strip(), location=location.strip() or "Remote",
               description=description.strip(), skills=skills.strip()))
    db.commit()
    return RedirectResponse(url="/recruiter", status_code=303)

@app.post("/recruiter/applications/{application_id}/status")
def update_status(application_id: int, status: str = Form(...), db: Session = Depends(get_db)):
    allowed = {"Applied", "Shortlisted", "Interview", "Rejected", "Hired"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid application status.")
    application = db.get(Application, application_id)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = status
    db.commit()
    return RedirectResponse(url="/recruiter", status_code=303)

@app.get("/api/jobs")
def api_jobs(db: Session = Depends(get_db)):
    jobs = db.scalars(select(Job).order_by(Job.created_at.desc())).all()
    return [{"id": j.id, "title": j.title, "company": j.company, "location": j.location,
             "description": j.description, "skills": j.skills} for j in jobs]

@app.get("/api/applications")
def api_applications(db: Session = Depends(get_db)):
    rows = db.scalars(select(Application).options(joinedload(Application.job)).order_by(Application.created_at.desc())).all()
    return [{"id": a.id, "candidate_name": a.candidate_name, "candidate_email": a.candidate_email,
             "job_title": a.job.title, "status": a.status, "match_score": a.match_score,
             "created_at": a.created_at.isoformat()} for a in rows]
