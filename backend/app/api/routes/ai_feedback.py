import re
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
    session_id: int
    job_role: str


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
    # Check interview session
    session = db.query(InterviewSession).filter(
        InterviewSession.id == request.session_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found."
        )

    # Get all questions for this interview session
    questions = db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == request.session_id
    ).order_by(InterviewQuestion.id).all()

    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No interview questions found for this session."
        )

    # Build evaluations from saved answers
    evaluations = []
    answer_scores = []

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

    # Calculate average of answer scores as verification
    avg_answer_score = round(sum(answer_scores) / max(len(answer_scores), 1), 1) if answer_scores else 0.0

    if overall_score is None:
        overall_score = avg_answer_score
    else:
        # If all answers were scored 0, the overall score MUST be 0
        if avg_answer_score == 0.0:
            overall_score = 0.0

    # Extract sections using robust parser
    sections = parse_feedback_sections(feedback)
    strengths = sections.get('strengths', '').strip()
    weaknesses = sections.get('weaknesses', '').strip()
    suggestions = sections.get('suggestions', '').strip()

    if overall_score == 0.0 or avg_answer_score == 0.0:
        if not strengths or "none" not in strengths.lower():
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

    # Save feedback report
    new_report = FeedbackReport(
        session_id=request.session_id,
        overall_score=overall_score,
        strengths=strengths,
        weaknesses=weaknesses,
        suggestions=suggestions
    )

    session.status = "completed"

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return {
        "message": "Feedback generated from saved answers and saved successfully",
        "feedback_report_id": new_report.id,
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
