from groq import Groq
from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


def evaluate_answer(question: str, answer: str) -> str:
    if not client:
        raise ValueError("GROQ_API_KEY is not configured.")

    clean_ans = (answer or "").strip()

    # Immediate zero for empty or known non-answers
    non_answers = {"sorry", "no idea", "idk", "i don't know", "i dont know", "kk", "skip", "pass", "na", "n/a", "none"}
    if not clean_ans or clean_ans.lower() in non_answers or len(clean_ans) < 3:
        return (
            "Score: 0.0/10\n"
            "Strengths: None demonstrated.\n"
            "Weaknesses: The candidate did not provide any substantive answer to the question.\n"
            "Suggestion: Review the fundamentals of this topic and prepare structured technical explanations."
        )

    prompt = f"""You are a strict, highly accurate technical interviewer.

Evaluate the candidate's answer to this interview question:

Question:
{question}

Candidate Answer:
{clean_ans}

SCORING CRITERIA (Strictly Enforce):
- 0.0 to 1.0: Completely WRONG, irrelevant, gibberish, admission of not knowing ("sorry", "no idea", "kk"), or factually incorrect.
- 2.0 to 3.5: Severe inaccuracies, major misconceptions, or missing 80%+ of the essential concept.
- 4.0 to 5.5: Partially correct idea but vague, lacks specifics, or has noticeable errors.
- 6.0 to 7.5: Acceptable answer covering the main points with reasonable accuracy.
- 8.0 to 10.0: Excellent, accurate, thorough response covering trade-offs, edge cases, and best practices.

Return your evaluation in EXACTLY this format:
Score: <number from 0.0 to 10.0>/10
Strengths: <Concise assessment of what (if anything) was correct. If wrong or irrelevant, state: "None demonstrated.">
Weaknesses: <Specific explanation of what was incorrect, missing, or inaccurate.>
Suggestion: <Actionable technical advice on the correct answer and how to improve.>
"""

    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_completion_tokens=1024
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error

    raise RuntimeError("Failed to evaluate answer with Groq AI.")
