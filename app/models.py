from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default="candidate")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(180), index=True)
    company: Mapped[str] = mapped_column(String(180))
    location: Mapped[str] = mapped_column(String(180), default="Remote")
    description: Mapped[str] = mapped_column(Text)
    skills: Mapped[str] = mapped_column(Text, default="")
    recruiter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    applications: Mapped[list["Application"]] = relationship(back_populates="job", cascade="all, delete-orphan")

class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_name: Mapped[str] = mapped_column(String(120))
    candidate_email: Mapped[str] = mapped_column(String(255), index=True)
    resume_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_text: Mapped[str] = mapped_column(Text, default="")
    cover_letter: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="Applied")
    match_score: Mapped[float] = mapped_column(Float, default=0.0)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    job: Mapped["Job"] = relationship(back_populates="applications")
