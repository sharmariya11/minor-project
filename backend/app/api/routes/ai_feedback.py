import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.interview_session import InterviewSession
from app.models.interview_question import InterviewQuestion
from app.models.answer import Answer
from app.models.feedback_report import FeedbackReport
from app.services.feedback_generator import generate_feedback


router = APIRouter(
    prefix="/ai",
    tags=["AI Interview"]
)


class FeedbackRequest(BaseModel):
    session_id: Optional[int] = 0
    job_role: str
    qa_list: Optional[List[dict]] = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def parse_bullet_points(text: str) -> list[str]:
    items = []
    for line in text.splitlines():
        line = line.strip().lstrip("*-•123456789.) ").strip()
        if line and len(line) > 3:
            items.append(line)
    return items


def parse_feedback_sections(text: str) -> dict[str, str]:
    sections = {'strengths': '', 'weaknesses': '', 'suggestions': ''}
    current_key = None
    lines = []

    for line in text.splitlines():
        clean = line.strip().strip('#*:- ').strip().lower()
        if 'strength' in clean:
            if current_key:
                sections[current_key] = '\n'.join(lines).strip()
            current_key = 'strengths'
            lines = []
        elif 'suggestion' in clean or 'recommend' in clean:
            if current_key:
                sections[current_key] = '\n'.join(lines).strip()
            current_key = 'suggestions'
            lines = []
        elif 'weakness' in clean or 'area' in clean or 'improvement' in clean:
            if current_key:
                sections[current_key] = '\n'.join(lines).strip()
            current_key = 'weaknesses'
            lines = []
        else:
            if current_key:
                lines.append(line)

    if current_key:
        sections[current_key] = '\n'.join(lines).strip()

    return sections


@router.post("/generate-feedback", status_code=status.HTTP_201_CREATED)
def generate_interview_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    evaluations = []
    answer_scores = []

    # 1. Try fetching questions and answers from database if session_id is provided
    if request.session_id and request.session_id > 0:
        try:
            questions = db.query(InterviewQuestion).filter(
                InterviewQuestion.session_id == request.session_id
            ).order_by(InterviewQuestion.id).all()

            for question in questions:
                answer = db.query(Answer).filter(
                    Answer.question_id == question.id
                ).order_by(Answer.id.desc()).first()

                if answer and answer.answer_text and answer.answer_text != "[Skipped]":
                    score_val = answer.score if answer.score is not None else 0.0
                    answer_scores.append(score_val)
                    evaluations.append(
                        f"Question: {question.question}\n"
                        f"Candidate Answer: {answer.answer_text}\n"
                        f"Evaluated Score: {score_val}/10"
                    )
                else:
                    answer_scores.append(0.0)
                    evaluations.append(
                        f"Question: {question.question}\n"
                        f"Candidate Answer: [Skipped / Not Answered]\n"
                        f"Evaluated Score: 0.0/10"
                    )
        except Exception as e:
            print(f"Notice: Could not load session from DB ({e})")

    # 2. Fall back to qa_list provided in request payload
    if not evaluations and request.qa_list:
        for item in request.qa_list:
            q_txt = item.get("question") or item.get("text") or "Question"
            a_txt = item.get("answer") or "[Skipped]"
            score_val = item.get("score", 0.0)
            answer_scores.append(score_val)
            evaluations.append(
                f"Question: {q_txt}\n"
                f"Candidate Answer: {a_txt}\n"
                f"Evaluated Score: {score_val}/10"
            )

    if not evaluations:
        evaluations.append(f"General technical assessment for {request.job_role}.")

    evaluations_text = "\n\n".join(evaluations)

    # Generate AI feedback
    try:
        feedback = generate_feedback(
            job_role=request.job_role,
            evaluations=evaluations_text
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate feedback: {str(e)}"
        )

    # Extract overall score
    score_match = re.search(
        r"(?:overall\s+score|score)[^\d]*(\d+(?:\.\d+)?)",
        feedback,
        re.IGNORECASE
    )

    overall_score = None
    if score_match:
        try:
            val = float(score_match.group(1))
            if val > 10:
                val = round(val / 10, 1)
            overall_score = round(val, 1)
        except ValueError:
            overall_score = None

    avg_answer_score = round(sum(answer_scores) / max(len(answer_scores), 1), 1) if answer_scores else 0.0

    if overall_score is None:
        overall_score = avg_answer_score
    else:
        if answer_scores and avg_answer_score == 0.0:
            overall_score = 0.0

    sections = parse_feedback_sections(feedback)
    strengths = sections.get('strengths', '').strip()
    weaknesses = sections.get('weaknesses', '').strip()
    suggestions = sections.get('suggestions', '').strip()

    if overall_score == 0.0:
        strengths = "No technical strengths demonstrated. The candidate was unable to provide correct answers to the interview questions."
        if not weaknesses:
            weaknesses = "Fundamental lack of technical preparation for this role. Answers provided were incorrect, minimal, or missing."
        if not suggestions:
            suggestions = f"Start with fundamental {request.job_role} courses and textbook study. Practice answering basic questions before retaking the mock interview."
    else:
        if not strengths:
            strengths = "Good technical effort demonstrated on some concepts."
        if not weaknesses:
            weaknesses = "Could provide deeper architectural trade-offs and edge-case considerations."
        if not suggestions:
            suggestions = "Practice structuring answers with concrete industry examples."

    # Save to DB if session exists
    report_id = request.session_id or 1
    if request.session_id and request.session_id > 0:
        try:
            new_report = FeedbackReport(
                session_id=request.session_id,
                overall_score=overall_score,
                strengths=strengths,
                weaknesses=weaknesses,
                suggestions=suggestions
            )
            session = db.query(InterviewSession).filter(InterviewSession.id == request.session_id).first()
            if session:
                session.status = "completed"
            db.add(new_report)
            db.commit()
            db.refresh(new_report)
            report_id = new_report.id
        except Exception as e:
            print(f"Notice: Could not persist feedback to DB ({e})")

    return {
        "message": "Feedback generated successfully",
        "feedback_report_id": report_id,
        "session_id": request.session_id,
        "overall_score": overall_score,
        "strengths": strengths,
        "strengths_list": parse_bullet_points(strengths),
        "weaknesses": weaknesses,
        "weaknesses_list": parse_bullet_points(weaknesses),
        "suggestions": suggestions,
        "suggestions_list": parse_bullet_points(suggestions),
        "feedback": feedback
    }
