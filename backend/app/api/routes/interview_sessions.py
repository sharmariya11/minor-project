from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database.connection import SessionLocal
from app.models.interview_session import InterviewSession
from app.models.job_role import JobRole
from app.models.interview_question import InterviewQuestion
from app.models.answer import Answer
from app.models.feedback_report import FeedbackReport
from app.models.skill_gap import SkillGap
from app.models.user import User
from app.schemas.interview import (
    InterviewSessionCreate,
    InterviewSessionResponse
)


router = APIRouter(
    prefix="/interview-sessions",
    tags=["Interview Sessions"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
def create_interview_session(
    session: InterviewSessionCreate,
    db: Session = Depends(get_db)
):
    # Ensure a valid user exists
    user_id = session.user_id or 1
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        first_user = db.query(User).first()
        if first_user:
            user_id = first_user.id
        else:
            # Create a default guest user
            default_user = User(name="Candidate", email="candidate@example.com")
            db.add(default_user)
            db.commit()
            db.refresh(default_user)
            user_id = default_user.id

    # Resolve job role
    role = None
    if session.job_role_id:
        role = db.query(JobRole).filter(JobRole.id == session.job_role_id).first()

    if not role and session.job_role:
        # Search by title or sanitized title
        target = session.job_role.strip().lower().replace("-", " ")
        all_roles = db.query(JobRole).all()
        for r in all_roles:
            if r.title.lower().replace("-", " ") == target or target in r.title.lower():
                role = r
                break

    if not role:
        # Fall back to first available role or create one
        role = db.query(JobRole).first()
        if not role:
            role = JobRole(title="Software Engineer", description="Core engineering role")
            db.add(role)
            db.commit()
            db.refresh(role)

    new_session = InterviewSession(
        user_id=user_id,
        job_role_id=role.id,
        status="started"
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


@router.get("/{session_id}", response_model=InterviewSessionResponse)
def get_interview_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )
    return session


@router.get("/user/{user_id}")
def get_user_interview_sessions(user_id: int, db: Session = Depends(get_db)):
    sessions = db.query(InterviewSession).filter(
        InterviewSession.user_id == user_id
    ).order_by(InterviewSession.id.desc()).all()

    result = []
    for s in sessions:
        role = db.query(JobRole).filter(JobRole.id == s.job_role_id).first()
        feedback = db.query(FeedbackReport).filter(
            FeedbackReport.session_id == s.id
        ).order_by(FeedbackReport.id.desc()).first()

        score = feedback.overall_score if feedback and feedback.overall_score is not None else None
        # Convert 10-point scale to percentage
        percentage_score = round(score * 10) if score is not None else None

        perf = "Average"
        if percentage_score is not None:
            if percentage_score >= 80:
                perf = "Great"
            elif percentage_score >= 65:
                perf = "Good"

        result.append({
            "id": s.id,
            "session_id": s.id,
            "role": role.title if role else "Software Engineer",
            "role_id": s.job_role_id,
            "date": s.started_at.strftime("%Y-%m-%d") if s.started_at else datetime.now().strftime("%Y-%m-%d"),
            "score": percentage_score,
            "raw_score": score,
            "performance": perf,
            "status": s.status
        })

    return result


@router.get("/{session_id}/summary")
def get_interview_session_summary(session_id: int, db: Session = Depends(get_db)):
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found."
        )

    role = db.query(JobRole).filter(JobRole.id == session.job_role_id).first()
    feedback = db.query(FeedbackReport).filter(
        FeedbackReport.session_id == session_id
    ).order_by(FeedbackReport.id.desc()).first()

    skill_gap = db.query(SkillGap).filter(
        SkillGap.session_id == session_id
    ).order_by(SkillGap.id.desc()).first()

    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id
    ).order_by(InterviewQuestion.id).all()

    qa_list = []
    for q in questions:
        ans = db.query(Answer).filter(
            Answer.question_id == q.id
        ).order_by(Answer.id.desc()).first()

        qa_list.append({
            "question_id": q.id,
            "question": q.question,
            "question_type": q.question_type,
            "difficulty": q.difficulty,
            "answer": ans.answer_text if ans else None,
            "score": ans.score if ans else None
        })

    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "job_role": role.title if role else "Software Engineer",
        "job_role_id": session.job_role_id,
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "questions": qa_list,
        "feedback_report": {
            "id": feedback.id,
            "overall_score": feedback.overall_score,
            "strengths": feedback.strengths,
            "weaknesses": feedback.weaknesses,
            "suggestions": feedback.suggestions,
        } if feedback else None,
        "skill_gap": {
            "id": skill_gap.id,
            "missing_skills": skill_gap.missing_skills,
            "recommended_skills": skill_gap.recommended_skills,
            "learning_resources": skill_gap.learning_resources,
        } if skill_gap else None
    }
