from groq import Groq
from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def analyze_skill_gap(job_role: str, feedback: str) -> str:
    if not client:
        raise ValueError("GROQ_API_KEY is not configured.")

    prompt = f"""You are a senior technical career coach.

Analyze the candidate's interview performance and determine their skill gaps for the role: {job_role}.

Candidate's Feedback & Performance Data:
{feedback}

Return your analysis in this clean format:

Missing Skills:
- <Specific technical or domain skill the candidate lacked during the interview>
- <Another missing skill or capability>

Recommended Skills:
- <Priority high-impact skill to develop next for {job_role}>
- <Secondary recommended skill or framework>

Learning Resources:
- <Book title, course name, or documentation guide with specific topics to study>
- <Practical project idea or practice platform topic>
"""

    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
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

    raise RuntimeError("Failed to analyze skill gap with Groq AI.")
