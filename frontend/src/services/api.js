import { getQuestionsForRole } from '../data/questions';
import { getRoleById } from '../data/roles';

const BASE_URL = import.meta.env?.VITE_API_URL || 'http://127.0.0.1:8000';

async function safeFetch(path, options = {}) {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      console.warn(`API call ${path} returned ${res.status}:`, errBody);
      return null;
    }
    return await res.json();
  } catch (err) {
    console.warn(`Network/API error reaching ${path}:`, err);
    return null;
  }
}

/**
 * Creates an interview session in PostgreSQL backend
 */
export async function createBackendSession({ userId = 1, roleId, roleTitle }) {
  const payload = {
    user_id: userId,
    job_role: roleTitle || roleId,
  };

  const data = await safeFetch('/interview-sessions/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  return data;
}

/**
 * Generates fresh questions via backend Groq LLM and saves to PostgreSQL
 */
export async function generateAIQuestions({ sessionId, jobRole, difficulty = 'Medium', count = 5 }) {
  if (sessionId) {
    const data = await safeFetch('/ai/generate-questions', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        job_role: jobRole,
        difficulty,
        count,
      }),
    });

    if (data && data.questions && data.questions.length > 0) {
      return data.questions.map((q) => ({
        id: q.id,
        text: q.question,
        difficulty: q.difficulty,
        type: q.question_type,
      }));
    }
  }

  // Graceful offline fallback
  const fallback = getQuestionsForRole(jobRole);
  return fallback.map((qText, i) => ({
    id: `local-${i}-${Date.now()}`,
    text: qText,
    difficulty,
    type: 'Bank Question',
  }));
}

/**
 * Evaluates an individual answer with Groq LLM and saves to DB
 */
export async function evaluateAIAnswer({ questionId, answer }) {
  if (!questionId || typeof questionId !== 'number') {
    return null;
  }

  return await safeFetch('/ai/evaluate-answer', {
    method: 'POST',
    body: JSON.stringify({
      question_id: questionId,
      answer: answer || '',
    }),
  });
}

/**
 * Generates overall interview feedback report via backend Groq LLM
 */
export async function generateAIFeedback({ sessionId, jobRole }) {
  if (!sessionId) return null;

  return await safeFetch('/ai/generate-feedback', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      job_role: jobRole,
    }),
  });
}

/**
 * Analyzes skill gaps via backend Groq LLM and saves to PostgreSQL
 */
export async function analyzeAISkillGap({ sessionId, jobRole }) {
  if (!sessionId) return null;

  return await safeFetch('/ai/analyze-skill-gap', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      job_role: jobRole,
    }),
  });
}

/**
 * Fetches user interview history from backend database
 */
export async function getUserSessions(userId = 1) {
  return await safeFetch(`/interview-sessions/user/${userId}`);
}

/**
 * User login via backend
 */
export async function loginUser(email, password) {
  return await safeFetch('/users/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

/**
 * User registration via backend
 */
export async function registerUser(name, email, password) {
  return await safeFetch('/users/', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  });
}

// ==================== Fallback Analytical Utilities ====================

const NON_ANSWER_PATTERNS = [
  /^\s*(sorry|no\s*idea|idk|i\s*don'?t\s*know|kk|pass|skip|none|na|n\/a|\?+)\s*$/i,
  /^.{0,3}$/,
];

export function isNonAnswer(text) {
  if (!text) return true;
  const trimmed = text.trim();
  return NON_ANSWER_PATTERNS.some((pat) => pat.test(trimmed));
}

export function generateScores(answers = []) {
  if (!answers || answers.length === 0) {
    return { overall: 0, technical: 0, communication: 0, confidence: 0, relevance: 0 };
  }

  const validAnswers = answers.filter((a) => !isNonAnswer(a.answer));

  // If every answer is empty or a non-answer (e.g. "sorry", "kk", "no idea"), scores are ZERO
  if (validAnswers.length === 0) {
    return {
      overall: 0,
      technical: 0,
      communication: 0,
      confidence: 0,
      relevance: 0,
    };
  }

  const ratio = validAnswers.length / answers.length;
  const avgLen = validAnswers.reduce((sum, a) => sum + (a.answer?.length || 0), 0) / validAnswers.length;

  // Base score proportional to how many questions were meaningfully attempted
  const baseScore = ratio * 50;
  const depthBonus = Math.min(avgLen / 10, 30);
  const overall = clamp(baseScore + depthBonus);

  return {
    overall,
    technical: clamp(overall + (Math.random() - 0.5) * 6),
    communication: clamp(overall + (Math.random() - 0.5) * 6),
    confidence: clamp(overall + (Math.random() - 0.5) * 6),
    relevance: clamp(overall + (Math.random() - 0.5) * 6),
  };
}

export function generateFeedback(scores) {
  const strengths = [];
  const improvements = [];

  if (scores.overall <= 25) {
    strengths.push('Attempt recorded. However, no valid technical concepts were articulated.');
    improvements.push('Thoroughly study core computer science and domain fundamentals.');
    improvements.push('Practice answering questions with clear technical terminology and concrete examples.');
    improvements.push('Avoid submitting one-word non-answers like "sorry" or "no idea".');
    return { strengths, improvements };
  }

  if (scores.technical >= 75) strengths.push('Strong technical understanding of core architecture.');
  else improvements.push('Deepen your technical knowledge of core domain fundamentals.');

  if (scores.communication >= 75) strengths.push('Clear, structured explanations with good precision.');
  else improvements.push('Structure answers using the STAR method for greater impact.');

  if (scores.confidence >= 75) strengths.push('Confident delivery with steady pacing.');
  else improvements.push('Practice articulating engineering trade-offs aloud.');

  if (scores.relevance >= 75) strengths.push('Answers stayed tightly focused on the questions.');
  else improvements.push('Keep responses focused and avoid drifting into tangential details.');

  if (strengths.length === 0) strengths.push('Willingness to attempt questions.');
  if (improvements.length === 0) improvements.push('Highlight concrete production trade-offs in examples.');

  return { strengths, improvements };
}

export function generateSkillGaps(roleId, scores) {
  const role = getRoleById(roleId);
  const skills = (role?.skills || ['DSA', 'System Design']).concat(['Communication', 'Problem Solving']);
  const seen = new Set();
  return skills
    .filter((s) => {
      if (seen.has(s)) return false;
      seen.add(s);
      return true;
    })
    .map((skill) => {
      if (scores.overall === 0) {
        return { skill, score: 0 };
      }
      const base = scores.overall + (Math.random() - 0.5) * 15;
      return { skill, score: clamp(base) };
    });
}

export function getRecommendations(skillGaps) {
  const recs = {
    DSA: 'Practice DSA arrays, trees and dynamic programming on LeetCode.',
    OOP: 'Revise OOP concepts: encapsulation, inheritance, polymorphism, and SOLID principles.',
    DBMS: 'Practice SQL joins, indexing strategies and transaction isolation levels.',
    'Problem Solving': 'Solve timed coding problems to improve speed and edge-case detection.',
    Communication: 'Record yourself explaining complex technical concepts clearly.',
    JavaScript: 'Build modern projects using ES6+, Promises, and async patterns.',
    React: 'Review React hooks, concurrency, and component state optimization.',
    CSS: 'Practice responsive layouts with Flexbox, CSS Grid, and Tailwind.',
    Accessibility: 'Add ARIA labels, semantic HTML, and keyboard navigation support.',
    'API Design': 'Design a RESTful / GraphQL API with versioning and OpenAPI specs.',
    'System Design': 'Study caching (Redis), message queues (Kafka), and database sharding.',
    Security: 'Review OWASP Top 10 vulnerabilities, auth protocols, and secure headers.',
    SQL: 'Practice complex aggregate functions, CTEs, and window functions.',
    Statistics: 'Revise probability distributions, hypothesis testing, and p-values.',
    Excel: 'Practice pivot tables, lookup functions, and financial modeling.',
    Visualization: 'Build dashboards using interactive charts and color theory.',
    ML: 'Implement gradient descent and classification models from scratch.',
    NLP: 'Explore transformer architectures, tokenization, and vector embeddings.',
    'Deep Learning': 'Build and train CNNs/RNNs using PyTorch or TensorFlow.',
    MLOps: 'Set up automated model tracking, data validation, and deployment pipelines.',
    Python: 'Practice writing clean, typed Python modules with pytest suites.',
    Cloud: 'Deploy scalable containers to AWS ECS, Lambda, or GCP Cloud Run.',
    Networking: 'Study the OSI model, TCP 3-way handshake, and HTTP/3.',
    Cryptography: 'Practice symmetric (AES) and asymmetric (RSA/ECC) encryption concepts.',
    Linux: 'Master core shell scripting, process management, and permission models.',
    Forensics: 'Analyze server access logs and telemetry for suspicious anomalies.',
    Docker: 'Containerize multi-tier applications using multi-stage Dockerfiles.',
    Kubernetes: 'Deploy, scale, and manage microservices with Kubernetes manifests.',
    AWS: 'Practice least-privilege IAM policies, VPC routing, and S3 security.',
    'CI/CD': 'Build automated test, lint, and deploy GitHub Actions workflows.',
  };

  const sorted = [...skillGaps].sort((a, b) => a.score - b.score);
  return sorted.slice(0, 4).map((g) => recs[g.skill] || `Practice ${g.skill} concepts from fundamentals.`);
}

function clamp(value) {
  return Math.max(0, Math.min(100, Math.round(value)));
}
