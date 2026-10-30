import random
import time
from groq import Groq
from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

ROLE_FOCUS_TOPICS = {
    "software-engineer": [
        "System Architecture & Scalability",
        "Data Structures, Memory & Concurrency",
        "Production Bug Troubleshooting & Incident Management",
        "API Design, Microservices & Caching Strategies",
        "Clean Code, Design Patterns & Refactoring",
        "Database Indexing, ACID Transactions & Latency Optimization"
    ],
    "frontend-developer": [
        "Modern React Architecture, Hooks & State Management",
        "DOM Rendering, Core Web Vitals & Performance Profiling",
        "Responsive CSS Layouts, Tailwind & Accessibility (a11y)",
        "Network Optimization, Caching & Client-side Routing",
        "Cross-browser Security, XSS Prevention & Authentication",
        "Testing with Jest/RTL and Component Design Systems"
    ],
    "backend-developer": [
        "RESTful & GraphQL API Design and Versioning",
        "Database Normalization, Query Optimization & Connection Pools",
        "Authentication, JWT, OAuth2 and RBAC Security",
        "Microservices, Message Brokers (Kafka/RabbitMQ) & Event-Driven Architecture",
        "Distributed Systems, Caching (Redis) & Rate Limiting",
        "Serverless, Dockerization & CI/CD Pipelines"
    ],
    "data-analyst": [
        "Complex SQL Queries, Window Functions & CTEs",
        "Data Cleaning, Missing Value Imputation & Outlier Detection",
        "Business Metrics (CAC, LTV, Churn) & Cohort Analysis",
        "A/B Testing, Hypothesis Formulation & Statistical Significance",
        "Data Storytelling, Dashboarding & KPI Communication",
        "ETL Pipelines, Data Validation & Stakeholder Reporting"
    ],
    "data-scientist": [
        "Feature Engineering, Selection & Dimensionality Reduction",
        "Supervised vs Unsupervised Models & Overfitting Mitigation",
        "Model Evaluation Metrics (ROC-AUC, Precision-Recall, F1)",
        "Machine Learning Math: Gradient Descent, Loss Functions & Regularization",
        "NLP / Large Language Model Fine-Tuning & Embeddings",
        "A/B Testing Experiments and Production Model Validation"
    ],
    "ml-engineer": [
        "Production Model Deployment, Serving Latency & Batch Inference",
        "Data Drift, Concept Drift & Automated Model Retraining",
        "MLOps Pipelines (Kubeflow, MLflow, Airflow) & Model Registries",
        "GPU Acceleration, Quantization & Model Optimization (ONNX/TensorRT)",
        "Feature Stores & Distributed Training Strategies",
        "Scalable Infrastructure, Docker & Kubernetes for ML"
    ],
    "cybersecurity-analyst": [
        "Threat Modeling, OWASP Top 10 & Vulnerability Scanning",
        "Incident Response Lifecycles & Forensics Investigation",
        "Symmetric vs Asymmetric Cryptography & PKI Implementation",
        "Network Security, Firewalls, Zero Trust & Packet Analysis",
        "SIEM Monitoring, Log Analysis & Anomaly Detection",
        "Social Engineering, Phishing Defense & Security Posture"
    ],
    "devops-engineer": [
        "CI/CD Pipeline Design, Automated Testing & Zero-Downtime Deployments",
        "Docker Container Best Practices & Multi-Stage Builds",
        "Kubernetes Pod Scheduling, Services, Ingress & Helm Charts",
        "Infrastructure as Code (Terraform, Ansible) & State Management",
        "Cloud Architecture (AWS/GCP), IAM & Cost Optimization",
        "Observability: Prometheus, Grafana, Distributed Tracing & Alerting"
    ]
}


def generate_questions(
    job_role: str,
    difficulty: str = "Medium",
    count: int = 5,
    avoid_questions: list[str] | None = None
) -> str:
    if not client:
        raise ValueError("GROQ_API_KEY is not configured.")

    # Match role key for varied focus topics
    clean_role_key = job_role.lower().replace(" ", "-")
    topics = ROLE_FOCUS_TOPICS.get(clean_role_key, ROLE_FOCUS_TOPICS.get("software-engineer", []))
    
    # Pick 2-3 random focus areas to guarantee unique questions every call
    sample_size = min(3, len(topics))
    chosen_focus = random.sample(topics, sample_size) if len(topics) >= sample_size else topics
    
    avoid_note = ""
    if avoid_questions and len(avoid_questions) > 0:
        cleaned_avoids = [f"- {q.strip()}" for q in avoid_questions if q.strip()][:10]
        if cleaned_avoids:
            avoid_note = (
                "\nDo NOT repeat or closely rephrase any of these recent questions:\n"
                + "\n".join(cleaned_avoids)
                + "\n"
            )

    prompt = f"""You are an elite, modern technical interviewer conducting a unique live interview round.

Job Role: {job_role}
Difficulty Level: {difficulty}
Number of Questions to Generate: {count}
Round Specific Themes: {", ".join(chosen_focus)}
Session Seed: {time.time_ns()} - {random.randint(1000, 9999)}
{avoid_note}
CRITICAL INSTRUCTIONS:
- Generate exactly {count} brand new, unique, non-repetitive interview questions.
- Every question must be distinct, highly relevant to {job_role}, and reflect real-world industry scenarios.
- Mix theoretical insight, architectural decisions, and practical debugging/problem-solving.
- Avoid cliché or standard generic trivia (e.g., do not just ask "Tell me about yourself" or simple textbook definitions).
- Return ONLY the questions as a numbered list (1. [Question text]\n2. [Question text] ...).
- Do NOT include any answers, explanations, headers, or intro/outro text.
"""

    models_to_try = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert technical interviewer. You output only cleanly formatted numbered questions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.88,
                max_completion_tokens=2048
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
        except Exception as e:
            last_error = e
            continue

    if last_error:
        raise last_error

    raise RuntimeError("Failed to generate questions with Groq AI.")
