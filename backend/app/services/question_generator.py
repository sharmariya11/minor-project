import random
import time
from groq import Groq
from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

ROLE_FOCUS_TOPICS = {
    "software-engineer": [
        "Distributed Systems, CAP Theorem & Microservices Consistency",
        "Algorithmic Optimization, Dynamic Programming & Graph Traversal",
        "Memory Management, Garbage Collection & Thread Safety",
        "Database Indexing Internals (B-Trees, Hash, GiST) & Latency Profiling",
        "High-Availability System Design (Rate Limiting, Circuit Breakers, Bulkheads)",
        "Production Incident Root-Cause Analysis & Real-Time Debugging",
        "Clean Architecture, Domain-Driven Design (DDD) & Design Patterns",
        "Zero-Downtime Database Migration & Schema Evolution"
    ],
    "frontend-developer": [
        "React Fiber Architecture, Concurrent Mode & Reconciliation",
        "Browser Event Loop, Macro vs Microtasks & Memory Leaks",
        "Web Vitals (LCP, INP, CLS) & Critical Rendering Path Optimization",
        "State Management Patterns (Zustand, Redux, Context API) & Re-render Prevention",
        "Advanced CSS Layouts (Container Queries, Subgrid, CSS Modules, Tailwind)",
        "Web Security: Content Security Policy (CSP), XSS, CSRF & Token Storage",
        "Micro-Frontends, Module Federation & Code Splitting Strategies",
        "Comprehensive Accessibility (WCAG 2.1 AA, ARIA Roles, Focus Trapping)"
    ],
    "backend-developer": [
        "Distributed Locks (Redis/Redlock), Idempotency & Message Deduplication",
        "Event-Driven Architecture with Kafka / RabbitMQ Partitioning",
        "Database ACID Guarantees, Isolation Levels & Deadlock Resolution",
        "REST vs gRPC vs GraphQL: Trade-offs & High-Throughput Protocol Design",
        "OAuth2 Grant Types, OIDC, JWT Revocation & RBAC / ABAC Permissions",
        "Connection Pooling, Query Plan (EXPLAIN ANALYZE) & Table Partitioning",
        "Graceful Shutdown, Health Probes & Blue-Green Deployments",
        "Distributed Tracing (OpenTelemetry), Structured Logging & APM"
    ],
    "data-analyst": [
        "Advanced SQL: Window Functions (LEAD/LAG, DENSE_RANK), Partitioning & CTEs",
        "Data Hygiene: Missing Value Imputation, Outlier Detection & Anomaly Screening",
        "A/B Testing: Power Analysis, Sample Size Determination & P-value Nuances",
        "Product Analytics: Cohort Retention, LTV/CAC Analysis & Funnel Conversion",
        "Data Pipeline Orchestration & Automated Data Quality Assertions",
        "Executive Dashboarding: Visual Hierarchy, KPI Modeling & Signal vs Noise",
        "Cross-Functional Stakeholder Communication & Translating Insights to ROI",
        "Data Warehousing: Star vs Snowflake Schemas, Fact vs Dimension Tables"
    ],
    "data-scientist": [
        "Gradient Boosting (XGBoost/LightGBM) vs Neural Architectures: Practical Trade-offs",
        "Feature Engineering for High-Cardinality Categoricals & Temporal Signals",
        "Overfitting Mitigations: L1/L2 Regularization, Early Stopping & Cross-Validation",
        "Evaluation Metrics Under Extreme Class Imbalance (PR-AUC, F-Beta, Cost Matrices)",
        "Large Language Model Fine-Tuning (LoRA/QLoRA), RAG Pipelines & Embeddings",
        "Statistical Foundations: Central Limit Theorem, Bayesian Inference & MCMC",
        "Fairness, Explainability (SHAP/LIME) & Mitigating Model Bias",
        "Production Experimentation: Multi-Armed Bandits vs Standard A/B Tests"
    ],
    "ml-engineer": [
        "High-Throughput Model Serving (vLLM, Triton, TorchServe) & Batching",
        "Model Quantization (FP8, INT4, AWQ) & KV-Cache Memory Optimizations",
        "Detecting Data Drift, Concept Drift & Automated Retraining Triggers",
        "MLOps Orchestration (Kubeflow, Airflow, MLflow) & Feature Stores (Feast)",
        "Distributed Training: Data Parallelism (DDP), Model Parallelism (FSDP, DeepSpeed)",
        "GPU Utilization Monitoring, CUDA Kernels & Memory Bandwidth Bottlenecks",
        "Continuous Deployment for ML: Canary Rollouts & Shadow Deployments",
        "Vector Databases (Pinecone, Qdrant, Milvus) Indexing (HNSW, IVF-PQ)"
    ],
    "cybersecurity-analyst": [
        "Threat Modeling Frameworks (STRIDE, PASTA) & Attack Surface Mapping",
        "Incident Response: Containment, Eradication & Forensic Memory Dumps",
        "Zero Trust Architecture & Micro-segmentation Principles",
        "Analyzing OWASP Top 10 Exploits: SSRF, IDOR, SQLi & Deserialization",
        "SIEM Detection Engineering, Sigma Rules & Anomaly Correlation",
        "Public Key Infrastructure (PKI), TLS 1.3 Handshake & Cipher Suites",
        "Privilege Escalation Vectors in Linux and Windows Active Directory",
        "Phishing Triage, Email Header Analysis (DKIM/SPF/DMARC) & Malware Sandboxing"
    ],
    "devops-engineer": [
        "Kubernetes Control Plane Internals, CNI, CSI & Custom Resource Definitions (CRDs)",
        "Zero-Downtime Deployment Strategies: Canary, Blue-Green & Progressive Delivery (ArgoCD)",
        "Infrastructure as Code: Terraform State Locking, Drift Detection & Module Architecture",
        "CI/CD Pipeline Security: Ephemeral Runners, Artifact Signing (Cosign) & Secret Scanning",
        "Observability Stacks: Prometheus Metrics, PromQL, Grafana & Distributed Tracing",
        "Multi-Cloud & Hybrid Networking: VPC Peering, Transit Gateways & Private Endpoints",
        "Cost Optimization: Spot Instances, Horizontal Pod Autoscaling (HPA) & Karpenter",
        "Disaster Recovery Planning: RPO/RTO Targets, Multi-Region Failover & Backup Validation"
    ]
}

SCENARIO_TYPES = [
    "Real-World Production Incident Recovery",
    "High-Scale Architecture & Bottleneck Elimination",
    "Edge-Case Troubleshooting & Bug Isolation",
    "System Design & Concrete Trade-off Justification",
    "Code Quality, Refactoring & Defensive Programming",
    "Deep Conceptual Principles & Internal Mechanisms"
]


def generate_questions(
    job_role: str,
    difficulty: str = "Medium",
    count: int = 5,
    avoid_questions: list[str] | None = None
) -> str:
    if not client:
        raise ValueError("GROQ_API_KEY is not configured.")

    clean_role_key = job_role.lower().replace(" ", "-")
    topics = ROLE_FOCUS_TOPICS.get(clean_role_key, ROLE_FOCUS_TOPICS.get("software-engineer", []))

    # Pick 2-3 randomized focus topics and a scenario lens for high entropy
    sample_size = min(3, len(topics))
    chosen_focus = random.sample(topics, sample_size) if len(topics) >= sample_size else topics
    chosen_scenario = random.choice(SCENARIO_TYPES)

    avoid_note = ""
    if avoid_questions and len(avoid_questions) > 0:
        cleaned_avoids = [f"- {q.strip()}" for q in avoid_questions if q and q.strip()][:25]
        if cleaned_avoids:
            avoid_note = (
                "\nCRITICAL: Do NOT repeat, rephrase, or ask similar questions to any of these previously asked questions:\n"
                + "\n".join(cleaned_avoids)
                + "\n"
            )

    entropy_seed = f"{time.time_ns()}-{random.randint(100000, 999999)}"

    prompt = f"""You are a top-tier principal engineer and hiring interviewer conducting an authentic, dynamic live interview round.

Candidate Job Role: {job_role}
Difficulty Level: {difficulty}
Number of Questions Needed: {count}
Selected Round Scenario Angle: {chosen_scenario}
Technical Focus Areas for this Round: {", ".join(chosen_focus)}
Unique Entropy Key: {entropy_seed}
{avoid_note}
MANDATORY RULES:
1. Generate exactly {count} completely novel, fresh, non-repetitive interview questions.
2. DO NOT ask generic textbook questions (e.g. NEVER ask "Tell me about yourself", "What is an array", "Explain OOP", "What is binary search").
3. Frame questions around realistic scenarios, technical trade-offs, architecture decisions, and practical engineering challenges.
4. Each question must test real-world depth and problem-solving capability for {job_role}.
5. Return ONLY the questions numbered 1 through {count}. No introductions, conversational filler, or explanations.
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
                        "content": "You are an elite technical interviewer. You output strictly clean, numbered technical questions without intro or outro."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.92,
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
