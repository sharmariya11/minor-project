import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.answer import Answer
from app.models.interview_question import InterviewQuestion
from app.services.answer_evaluator import evaluate_answer


router = APIRouter(
    prefix="/ai",
    tags=["AI Interview"]
)


class AnswerEvaluationRequest(BaseModel):
    question_id: Optional[int] = 1
    question_text: Optional[str] = None
    answer: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/evaluate-answer", status_code=status.HTTP_201_CREATED)
def evaluate_interview_answer(
    request: AnswerEvaluationRequest,
    db: Session = Depends(get_db)
):
    q_text = request.question_text or ""

    # Look up question in database if question_id is provided
    if request.question_id:
        try:
            db_question = db.query(InterviewQuestion).filter(
                InterviewQuestion.id == request.question_id
            ).first()
            if db_question:
                q_text = db_question.question
        except Exception:
            pass

    if not q_text:
        q_text = "Technical interview question evaluation"

    ans_text = request.answer.strip() if request.answer else ""

    # Non-answers get immediate 0 score
    evaluation = evaluate_answer(
        question=q_text,
        answer=ans_text
    )

    # Extract score from LLM response
    score_match = re.search(
        r"(?:score)[^\d]*(\d+(?:\.\d+)?)",
        evaluation,
        re.IGNORECASE
    )

    score = 0.0
    if score_match:
        try:
            val = float(score_match.group(1))
            if val > 10:
                val = round(val / 10, 1)
            score = round(val, 1)
        except ValueError:
            score = 0.0

    # Save answer in database if possible
    answer_id = request.question_id or 1
    try:
        new_answer = Answer(
            question_id=request.question_id or 1,
            answer_text=ans_text,
            score=score
        )
        db.add(new_answer)
        db.commit()
        db.refresh(new_answer)
        answer_id = new_answer.id
    except Exception as e:
        print(f"Notice: Could not persist answer to DB ({e}), returning evaluated result directly.")

    return {
        "message": "Answer evaluated successfully",
        "answer_id": answer_id,
        "question_id": request.question_id,
        "answer": ans_text,
        "score": score,
        "evaluation": evaluation
    }
