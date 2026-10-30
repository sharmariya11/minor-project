export const questionBank = {
  'software-engineer': [
    'How would you design a distributed rate limiter that handles millions of requests per minute across multiple regions?',
    'Explain the internals of how a database index (B-tree) speeds up read queries and how it affects write performance.',
    'Describe a scenario where a race condition or deadlock could occur in a multithreaded application and how you would prevent it.',
    'How would you architect a cache-invalidation strategy (e.g., Cache-Aside, Write-Through) to guarantee data consistency?',
    'What are the core differences between optimistic and pessimistic locking in relational databases, and when would you choose each?',
    'Explain how the CAP theorem dictates architectural trade-offs when designing a globally distributed microservices system.',
    'How would you debug a sudden spike in P99 latency in a microservice where CPU and memory usage remain low?',
    'Describe how you would design a scalable notification service supporting push, SMS, and email with retry and backoff guarantees.',
    'What data structure and algorithm would you use to find the lowest common ancestor in a large organizational hierarchy tree?',
    'Explain the trade-offs between monolithic architecture, microservices, and modular monoliths in modern software engineering.',
    'How would you handle idempotent payment processing to ensure customers are never double-charged during network drops?',
    'Describe your approach to implementing zero-downtime database schema migrations on a high-write production table.'
  ],
  'frontend-developer': [
    'Explain how the React Fiber architecture and reconciliation process work under the hood.',
    'What strategies and metrics (LCP, INP, CLS) do you prioritize when optimizing Critical Rendering Path performance?',
    'How does the browser event loop handle macro-tasks, micro-tasks, and requestAnimationFrame?',
    'Describe how you would prevent unnecessary component re-renders when managing global state across a complex dashboard.',
    'How would you implement secure client-side authentication and session management to mitigate XSS and CSRF attacks?',
    'Explain the mechanics of CSS Grid vs Flexbox and when CSS Container Queries are preferred over Media Queries.',
    'How would you design an accessible modal dialog adhering to WCAG 2.1 AA keyboard navigation and ARIA guidelines?',
    'Describe how you would set up code-splitting, lazy-loading, and bundle analysis in a modern Vite/Webpack application.',
    'How would you implement infinite scrolling with virtualized lists to maintain 60 FPS performance with 50,000 items?',
    'Explain the differences between Server-Side Rendering (SSR), Static Site Generation (SSG), and Client-Side Rendering (CSR).'
  ],
  'backend-developer': [
    'How would you design a fault-tolerant message processing pipeline using Kafka or RabbitMQ with at-least-once delivery?',
    'Explain how database transaction isolation levels (Read Committed, Repeatable Read, Serializable) prevent race conditions.',
    'How do you design and version a public REST or gRPC API to ensure backward compatibility for legacy mobile clients?',
    'Describe how you would implement token revocation and refresh-token rotation in a distributed JWT authentication system.',
    'What strategies do you employ for database connection pooling, query optimization, and slow-query troubleshooting?',
    'How would you architect a distributed lock using Redis, and what edge cases (such as clock drift and process pausing) arise?',
    'Explain the architectural trade-offs between synchronous REST calls, asynchronous event streams, and message queues.',
    'How would you design a multi-tenant SaaS backend that guarantees strict data isolation between corporate clients?'
  ],
  'data-analyst': [
    'How do you use SQL window functions like ROW_NUMBER(), RANK(), and DENSE_RANK() to calculate cohort retention?',
    'Explain how you would design a data validation pipeline to detect corrupted records and schema drift before ingestion.',
    'Describe your methodology for conducting an A/B test: from sample size calculation to statistical significance and p-values.',
    'How would you compute Customer Acquisition Cost (CAC) and Lifetime Value (LTV) across blended marketing channels?',
    'Explain the structural and performance differences between Star Schema and Snowflake Schema in data warehousing.',
    'How would you design an executive-level KPI dashboard that balances summary metrics with drill-down diagnostic capability?'
  ],
  'data-scientist': [
    'How do you address extreme class imbalance when training a fraud detection classification model?',
    'Explain the bias-variance tradeoff and how L1 (Lasso) vs L2 (Ridge) regularization alters feature weights.',
    'How would you evaluate and validate a Retrieval-Augmented Generation (RAG) system with complex domain documentation?',
    'Describe the mathematical intuition behind Gradient Boosting and how it differs from Random Forests.',
    'How do you detect and mitigate data drift and concept drift in machine learning models deployed in production?',
    'Explain how SHAP (Shapley Additive exPlanations) values provide local and global interpretability for black-box models.'
  ],
  'ml-engineer': [
    'How do you optimize model serving latency and throughput using techniques like quantization (INT8/FP8) and vLLM?',
    'Describe how you would design an automated MLOps pipeline covering data validation, model training, evaluation, and registry.',
    'What strategies do you use for distributed model training across multi-node GPU clusters (DDP, FSDP, DeepSpeed)?',
    'How do you manage vector database indexing strategies (HNSW vs IVF-PQ) for million-scale semantic search?',
    'Explain how you would implement canary deployments and shadow scoring for new machine learning models in production.'
  ],
  'cybersecurity-analyst': [
    'Walk through the end-to-end incident response lifecycle for a suspected ransomware or data exfiltration breach.',
    'Explain how Server-Side Request Forgery (SSRF) and Insecure Direct Object Reference (IDOR) attacks work and how to fix them.',
    'What is the difference between symmetric (AES-GCM) and asymmetric (RSA/ECC) cryptography, and how are they combined in TLS 1.3?',
    'How would you architect a Zero Trust security model for an organization with distributed remote employees and hybrid cloud?',
    'How do you configure and interpret SIEM correlation rules to detect advanced persistent threat (APT) lateral movement?'
  ],
  'devops-engineer': [
    'How would you design a zero-downtime deployment pipeline using Kubernetes progressive delivery tools like ArgoCD or Flagger?',
    'Explain how Kubernetes Pod scheduling, node affinity, taints, and tolerations work together to manage cluster workloads.',
    'How do you structure Terraform code to support multiple environments while avoiding state file locking and drift issues?',
    'Describe your strategy for setting up distributed tracing and metrics monitoring with Prometheus, OpenTelemetry, and Grafana.',
    'How would you harden a containerized CI/CD pipeline to prevent secret leakage and supply chain tampering (e.g. Cosign, SBOM)?'
  ]
};

export function getQuestionsForRole(roleId, count = 5, avoidQuestions = []) {
  const cleanId = (roleId || '').toLowerCase().replace(/\s+/g, '-');
  const pool = questionBank[cleanId] || questionBank['software-engineer'];

  // Filter out questions that have already been asked if possible
  const avoidSet = new Set(
    (avoidQuestions || []).map((q) => (typeof q === 'string' ? q.trim().toLowerCase() : ''))
  );
  let available = pool.filter((q) => !avoidSet.has(q.trim().toLowerCase()));

  // If filtered pool is smaller than count, fall back to full pool
  if (available.length < count) {
    available = [...pool];
  }

  // Fisher-Yates shuffle to ensure random, non-repeating questions
  const shuffled = [...available];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }

  return shuffled.slice(0, count);
}
