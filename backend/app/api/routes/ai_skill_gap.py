from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models.interview_session import InterviewSession
from app.models.interview_question import InterviewQuestion
from app.models.answer import Answer
from app.models.feedback_report import FeedbackReport
from app.models.skill_gap import SkillGap
from app.services.skill_gap_analyzer import analyze_skill_gap

router = APIRouter(
    prefix="/ai",
    tags=["AI Interview"]
)


class SkillGapRequest(BaseModel):
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


def parse_skill_gap_sections(text: str) -> dict[str, str]:
    sections = {'missing_skills': '', 'recommended_skills': '', 'learning_resources': ''}
    current_key = None
    lines = []

    for line in text.splitlines():
        clean = line.strip().strip('#*:- ').strip().lower()
        if 'missing' in clean or 'gap' in clean:
            if current_key:
                sections[current_key] = '\n'.join(lines).strip()
            current_key = 'missing_skills'
            lines = []
        elif 'recommended' in clean or 'priority' in clean:
            if current_key:
                sections[current_key] = '\n'.join(lines).strip()
            current_key = 'recommended_skills'
            lines = []
        elif 'learning' in clean or 'resource' in clean or 'study' in clean:
            if current_key:
                sections[current_key] = '\n'.join(lines).strip()
            current_key = 'learning_resources'
            lines = []
        else:
            if current_key:
                lines.append(line)

    if current_key:
        sections[current_key] = '\n'.join(lines).strip()

    return sections


@router.post("/analyze-skill-gap", status_code=status.HTTP_201_CREATED)
def analyze_interview_skill_gap(
    request: SkillGapRequest,
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

    # Get latest feedback report for this session if it exists
    feedback_report = db.query(FeedbackReport).filter(
        FeedbackReport.session_id == request.session_id
    ).order_by(
        FeedbackReport.id.desc()
    ).first()

    if feedback_report:
        feedback_text = f"""
Overall Score: {feedback_report.overall_score}/10

Strengths:
{feedback_report.strengths}

Weaknesses:
{feedback_report.weaknesses}

Suggestions:
{feedback_report.suggestions}
"""
    else:
        # Fall back to answers if feedback report has not been generated yet
        questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id == request.session_id
        ).all()
        qa_pairs = []
        for q in questions:
            ans = db.query(Answer).filter(Answer.question_id == q.id).order_by(Answer.id.desc()).first()
            qa_pairs.append(f"Q: {q.question}\nA: {ans.answer_text if ans else '[Skipped]'}\nScore: {ans.score if ans else 0.0}/10")

        feedback_text = f"Interview Performance for {request.job_role}:\n" + "\n\n".join(qa_pairs)

    # Analyze skill gap using Groq LLM
    try:
        skill_gap = analyze_skill_gap(
            job_role=request.job_role,
            feedback=feedback_text
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze skill gaps: {str(e)}"
        )

    sections = parse_skill_gap_sections(skill_gap)
    missing_skills = sections.get('missing_skills', '').strip()
    recommended_skills = sections.get('recommended_skills', '').strip()
    learning_resources = sections.get('learning_resources', '').strip()

    if not missing_skills:
        missing_skills = f"- Core foundational concepts for {request.job_role}\n- Technical vocabulary and problem explanation skills"
    if not recommended_skills:
        recommended_skills = f"- Essential {request.job_role} algorithms and data modeling\n- Hands-on coding and project implementation"
    if not learning_resources:
        learning_resources = f"- Fundamental {request.job_role} documentation and introductory textbooks\n- Interactive beginner coding platforms"

    # Save skill-gap report
    new_skill_gap = SkillGap(
        session_id=request.session_id,
        missing_skills=missing_skills,
        recommended_skills=recommended_skills,
        learning_resources=learning_resources
    )

    db.add(new_skill_gap)
    db.commit()
    db.refresh(new_skill_gap)

    return {
        "message": "Skill gap analyzed from saved feedback and saved successfully",
        "skill_gap_id": new_skill_gap.id,
        "session_id": request.session_id,
        "missing_skills": missing_skills,
        "missing_skills_list": parse_bullet_points(missing_skills),
        "recommended_skills": recommended_skills,
        "recommended_skills_list": parse_bullet_points(recommended_skills),
        "learning_resources": learning_resources,
        "learning_resources_list": parse_bullet_points(learning_resources),
        "skill_gap": skill_gap
    }
