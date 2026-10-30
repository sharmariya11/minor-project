from groq import Groq
from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def generate_feedback(job_role: str, evaluations: str) -> str:
    if not client:
        raise ValueError("GROQ_API_KEY is not configured.")

    prompt = f"""You are a strict technical hiring manager and interview coach.

Analyze the candidate's full interview performance for the role of {job_role}.

Candidate's Question Responses and Answer Evaluations:
{evaluations}

CRITICAL SCORING & EVALUATION RULES:
1. If the candidate answered questions incorrectly, admitted they didn't know ("sorry", "no idea", "kk"), or provided off-topic/shallow answers:
   - Overall Score MUST be low (0.0 to 2.0 / 10).
   - Strengths MUST state: "None demonstrated - the candidate was unable to provide correct technical answers in this session."
   - Do NOT give fake praise or compliment "effort" or "willingness" when answers are wrong.
2. If the candidate answered some questions correctly and some wrong:
   - Score proportionally based strictly on the individual answer scores provided.
3. If the candidate answered questions thoroughly and correctly:
   - Award a solid score (7.0 - 10.0 / 10) and detail concrete technical strengths.

Format your response cleanly with these exact section headers:

Overall Score: <score out of 10, e.g. 0.0 or 4.5 or 8.5>/10

Strengths:
- <Specific strength. If no correct answers were given, explicitly state that no technical strengths were demonstrated.>

Weaknesses:
- <Specific technical misconception, missing knowledge, or inaccuracy demonstrated in the answers>
- <Another concrete technical gap>

Suggestions:
- <Actionable study recommendation to learn the missing concepts>
- <Recommended textbook, documentation, or practice focus>
"""

    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_completion_tokens=1536
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error

    raise RuntimeError("Failed to generate feedback with Groq AI.")
