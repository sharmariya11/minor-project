import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, ArrowRight, Loader2, Sparkles } from 'lucide-react';
import Navbar from '../components/Navbar';
import InterviewQuestion from '../components/InterviewQuestion';
import { getRoleById } from '../data/roles';
import {
  createBackendSession,
  generateAIQuestions,
  evaluateAIAnswer,
  generateAIFeedback,
  analyzeAISkillGap,
  generateScores,
  generateFeedback,
  generateSkillGaps,
  getRecommendations,
  isNonAnswer,
} from '../services/api';
import { addInterviewRecord, setLastResult, getAuthUser, getInterviewHistory } from '../utils/storage';

export default function Interview() {
  const navigate = useNavigate();
  const roleId = localStorage.getItem('ais_selected_role') || 'software-engineer';
  const role = useMemo(() => getRoleById(roleId), [roleId]);

  const [sessionId, setSessionId] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [loadingQuestions, setLoadingQuestions] = useState(true);
  const [finishing, setFinishing] = useState(false);
  const [statusMessage, setStatusMessage] = useState('Initializing interview...');

  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [answer, setAnswer] = useState('');
  const [seconds, setSeconds] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);

  const speechSupported =
    typeof window !== 'undefined' &&
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  // Initialize backend session and load fresh AI questions
  useEffect(() => {
    let isMounted = true;

    async function initInterview() {
      setLoadingQuestions(true);
      setStatusMessage(`Generating fresh AI questions for ${role.name}...`);

      const authUser = getAuthUser();
      const userId = authUser?.id || 1;

      // Extract previously asked questions from past attempts so questions are NEVER repeated
      const history = getInterviewHistory();
      const pastQuestions = [];
      for (const h of history) {
        if (Array.isArray(h.answers)) {
          for (const a of h.answers) {
            const q = a?.question;
            if (q && typeof q === 'string' && !pastQuestions.includes(q)) {
              pastQuestions.push(q);
            }
          }
        }
      }

      try {
        // Step 1: Create backend interview session
        const session = await createBackendSession({
          userId,
          roleId,
          roleTitle: role.name,
        });

        const activeSessionId = session?.id || Math.floor(Date.now() / 1000);
        if (isMounted) setSessionId(activeSessionId);

        // Step 2: Generate dynamic AI questions via Groq LLM (avoiding past questions)
        const aiQuestions = await generateAIQuestions({
          sessionId: activeSessionId,
          jobRole: role.name,
          difficulty: role.difficulty || 'Medium',
          count: 5,
          avoidQuestions: pastQuestions,
        });

        if (isMounted) {
          setQuestions(aiQuestions);
          setLoadingQuestions(false);
        }
      } catch (err) {
        console.warn('Backend init notice, generating dynamic questions:', err);
        const fallback = await generateAIQuestions({
          sessionId: Math.floor(Date.now() / 1000),
          jobRole: role.name,
          avoidQuestions: pastQuestions,
        });
        if (isMounted) {
          setQuestions(fallback);
          setLoadingQuestions(false);
        }
      }
    }

    initInterview();

    return () => {
      isMounted = false;
    };
  }, [role, roleId]);

  // Timer
  useEffect(() => {
    const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (s) => {
    const m = Math.floor(s / 60).toString().padStart(2, '0');
    const sec = (s % 60).toString().padStart(2, '0');
    return `${m}:${sec}`;
  };

  const startRecording = () => {
    if (!speechSupported) return;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.onresult = (event) => {
      let text = '';
      for (let i = 0; i < event.results.length; i++) {
        text += event.results[i][0].transcript;
      }
      setAnswer(text);
    };
    recognition.onerror = () => setIsRecording(false);
    recognition.onend = () => setIsRecording(false);
    recognition.start();
    recognitionRef.current = recognition;
    setIsRecording(true);
  };

  const stopRecording = () => {
    recognitionRef.current?.stop();
    setIsRecording(false);
  };

  const storeAnswer = (text) => {
    const currentQ = questions[current];
    const qText = currentQ?.text || currentQ || '';
    const updated = [...answers];
    updated[current] = {
      questionId: currentQ?.id,
      question: qText,
      answer: text,
    };
    setAnswers(updated);

    // Save answer evaluation in background
    evaluateAIAnswer({
      questionId: currentQ?.id,
      questionText: qText,
      answer: text,
    }).catch((err) => console.warn('Background evaluation notice:', err));

    return updated;
  };

  const handleSubmit = () => {
    const updatedAnswers = storeAnswer(answer);
    if (current < questions.length - 1) {
      setCurrent((c) => c + 1);
      setAnswer('');
    } else {
      finish(updatedAnswers);
    }
  };

  const handleSkip = () => {
    const updatedAnswers = storeAnswer('');
    if (current < questions.length - 1) {
      setCurrent((c) => c + 1);
      setAnswer('');
    } else {
      finish(updatedAnswers);
    }
  };

  const finish = async (providedAnswers) => {
    stopRecording();
    setFinishing(true);
    setStatusMessage('Evaluating answers and analyzing technical accuracy...');

    const allAnswers = providedAnswers || answers;

    // Send any remaining evaluations
    for (const ansItem of allAnswers) {
      try {
        await evaluateAIAnswer({
          questionId: ansItem?.questionId,
          questionText: ansItem?.question,
          answer: ansItem?.answer || '',
        });
      } catch (e) {
        // ignore evaluation notice
      }
    }

    // Call Backend AI: First generate feedback, then analyze skill gap
    let aiFeedbackData = null;
    let aiSkillGapData = null;

    try {
      setStatusMessage('AI synthesizing comprehensive performance report...');
      const formattedQA = allAnswers.map((a) => ({
        question: a.question || '',
        answer: a.answer || '',
      }));

      aiFeedbackData = await generateAIFeedback({
        sessionId,
        jobRole: role.name,
        qaList: formattedQA,
      });

      setStatusMessage('AI determining skill gaps and learning resources...');
      aiSkillGapData = await analyzeAISkillGap({ sessionId, jobRole: role.name });
    } catch (err) {
      console.warn('Backend AI analysis notice, using client-side fallback:', err);
    }

    // Check if every answer is empty or a non-answer
    const hasAnyRealAnswer = allAnswers.some((a) => !isNonAnswer(a.answer));

    // Calculate score
    let overallScore = 0;
    if (aiFeedbackData && typeof aiFeedbackData.overall_score === 'number') {
      // Backend overall score is on 0-10 scale
      overallScore = Math.round(aiFeedbackData.overall_score * 10);
    } else {
      const fallbackScores = generateScores(allAnswers);
      overallScore = fallbackScores.overall;
    }

    // If candidate gave no real answers, strictly enforce 0%
    if (!hasAnyRealAnswer) {
      overallScore = 0;
    }

    let scores = {};
    if (overallScore === 0) {
      scores = {
        overall: 0,
        technical: 0,
        communication: hasAnyRealAnswer ? 10 : 0,
        confidence: 0,
        relevance: 0,
      };
    } else {
      scores = {
        overall: Math.min(100, Math.max(0, overallScore)),
        technical: Math.min(100, Math.max(0, Math.round(overallScore + (Math.random() - 0.5) * 6))),
        communication: Math.min(100, Math.max(0, Math.round(overallScore + (Math.random() - 0.5) * 6))),
        confidence: Math.min(100, Math.max(0, Math.round(overallScore + (Math.random() - 0.5) * 6))),
        relevance: Math.min(100, Math.max(0, Math.round(overallScore + (Math.random() - 0.5) * 6))),
      };
    }

    // Feedback strengths and improvements
    let strengths = [];
    let improvements = [];

    if (overallScore === 0) {
      strengths = ['No technical strengths demonstrated. All submitted responses were incorrect, minimal, or non-answers.'];
      improvements = [
        'Study core domain fundamentals thoroughly before attempting this interview.',
        'Practice explaining technical concepts using industry-standard terminology.',
        'Avoid submitting single-word non-answers like "sorry", "kk", or "no idea".',
      ];
    } else {
      strengths = aiFeedbackData?.strengths_list?.length
        ? aiFeedbackData.strengths_list
        : generateFeedback(scores).strengths;

      improvements = aiFeedbackData?.weaknesses_list?.length
        ? aiFeedbackData.weaknesses_list
        : generateFeedback(scores).improvements;
    }

    const suggestions = aiFeedbackData?.suggestions_list || [];

    // Skill gaps & recommendations
    let skillGaps = [];
    if (overallScore === 0) {
      skillGaps = (role?.skills || ['DSA', 'System Design']).map((s) => ({
        skill: s,
        score: 0,
      }));
    } else if (aiSkillGapData?.recommended_skills_list?.length) {
      skillGaps = aiSkillGapData.recommended_skills_list.slice(0, 5).map((s, idx) => ({
        skill: s.replace(/^[•\-\*]\s*/, ''),
        score: Math.min(95, Math.max(5, Math.round(scores.overall - 10 + idx * 4))),
      }));
    } else {
      skillGaps = generateSkillGaps(roleId, scores);
    }

    let recommendations = [];
    if (aiSkillGapData?.learning_resources_list?.length) {
      recommendations = aiSkillGapData.learning_resources_list.slice(0, 4).map((r) =>
        r.replace(/^[•\-\*]\s*/, '')
      );
    } else {
      recommendations = getRecommendations(skillGaps);
    }

    const performanceLabel =
      overallScore >= 80
        ? 'Great'
        : overallScore >= 60
        ? 'Good'
        : overallScore >= 40
        ? 'Needs Improvement'
        : 'Unsatisfactory';

    const record = {
      id: `int-${sessionId || Date.now()}`,
      sessionId,
      role: role.name,
      roleId,
      date: new Date().toISOString().slice(0, 10),
      score: scores.overall,
      performance: performanceLabel,
      scores,
      feedback: {
        strengths,
        improvements,
        suggestions,
        raw: aiFeedbackData?.feedback || '',
      },
      skillGaps,
      recommendations,
      answers: allAnswers,
    };

    addInterviewRecord(record);
    setLastResult(record);
    navigate('/results');
  };

  const currentQuestionText =
    questions[current]?.text || questions[current] || 'Question loading...';
  const progress = questions.length ? ((current + 1) / questions.length) * 100 : 0;

  if (loadingQuestions || finishing) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <main className="container-app flex min-h-[70vh] flex-col items-center justify-center py-20 text-center">
          <div className="relative mb-6">
            <div className="absolute -inset-4 rounded-full bg-blue-500/20 blur-xl animate-pulse" />
            <div className="relative grid h-16 w-16 place-items-center rounded-2xl border border-blue-500/40 bg-blue-600/10 text-blue-400">
              <Sparkles className="h-8 w-8 animate-spin" style={{ animationDuration: '6s' }} />
            </div>
          </div>
          <h2 className="text-2xl font-bold text-white sm:text-3xl">
            {finishing ? 'Generating AI Evaluation Report' : 'AI Interview Simulator'}
          </h2>
          <p className="mt-3 max-w-md text-sm text-slate-400">
            {statusMessage}
          </p>
          <div className="mt-6 flex items-center gap-2 rounded-full border border-blue-500/20 bg-white/5 px-4 py-1.5 text-xs text-blue-400">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            <span>Connected to Database & Groq LLM</span>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="container-app py-10">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-widest text-blue-400">
                {role.name}
              </span>
              <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[11px] font-medium text-emerald-400 border border-emerald-500/20">
                AI Powered
              </span>
            </div>
            <h1 className="mt-1 text-2xl font-bold text-white">Live Mock Interview</h1>
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-blue-500/25 bg-[#061432] px-4 py-2.5 text-sm font-medium text-white shadow-lg shadow-blue-500/5">
            <Clock className="h-4 w-4 text-cyan-400" />
            {formatTime(seconds)}
          </div>
        </div>

        <div className="mt-6">
          <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-500 via-cyan-400 to-violet-500 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
            <span>Question {current + 1} of {questions.length}</span>
            <span>Difficulty: {questions[current]?.difficulty || role.difficulty || 'Medium'}</span>
          </div>
        </div>

        <div className="mt-8 max-w-3xl">
          <InterviewQuestion
            question={currentQuestionText}
            questionNumber={current + 1}
            totalQuestions={questions.length}
            answer={answer}
            setAnswer={setAnswer}
            isRecording={isRecording}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            speechSupported={!!speechSupported}
            onSubmit={handleSubmit}
            onSkip={handleSkip}
          />
        </div>

        <div className="mt-8 flex items-center justify-between border-t border-white/5 pt-6">
          <button
            onClick={() => {
              const updatedAnswers = storeAnswer(answer);
              finish(updatedAnswers);
            }}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
          >
            <span>Finish Early & See Analytics</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </main>
    </div>
  );
}
