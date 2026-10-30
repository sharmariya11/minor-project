import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, AlertCircle, RotateCcw, ChevronDown, ChevronUp, BookOpen, Sparkles, AlertTriangle } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import ScoreCard from '../components/ScoreCard';
import SkillBar from '../components/SkillBar';
import Button from '../components/Button';
import { getLastResult } from '../utils/storage';

export default function Results() {
  const navigate = useNavigate();
  const result = getLastResult();
  const [showQAReview, setShowQAReview] = useState(false);

  useEffect(() => {
    if (!result) navigate('/roles');
  }, [result, navigate]);

  if (!result) return null;

  const scores = result.scores || {
    overall: 0,
    technical: 0,
    communication: 0,
    confidence: 0,
    relevance: 0,
  };

  const isLowScore = scores.overall < 40;
  const primaryColor = isLowScore ? '#EF4444' : '#3B82F6';
  const techColor = isLowScore ? '#F87171' : '#22D3EE';
  const commColor = isLowScore ? '#F59E0B' : '#7C3AED';

  const scoreCards = [
    { label: 'Overall Score', value: scores.overall, color: primaryColor },
    { label: 'Technical Depth', value: scores.technical, color: techColor },
    { label: 'Communication', value: scores.communication, color: commColor },
    { label: 'Delivery & Clarity', value: scores.confidence, color: isLowScore ? '#EF4444' : '#10B981' },
    { label: 'Question Relevance', value: scores.relevance, color: isLowScore ? '#F59E0B' : '#F59E0B' },
  ];

  const strengthsList = result.feedback?.strengths || [];
  const improvementsList = result.feedback?.improvements || [];
  const suggestionsList = result.feedback?.suggestions || [];
  const skillGapsList = result.skillGaps || [];
  const recommendationsList = result.recommendations || [];
  const answersList = result.answers || [];

  return (
    <div className="min-h-screen">
      <Navbar />
      <main className="container-app py-10">
        <div className="mx-auto max-w-2xl text-center">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-3.5 py-1 text-xs font-semibold uppercase tracking-widest text-blue-400">
            <Sparkles className="h-3 w-3 text-cyan-400" />
            {result.role} AI Evaluation
          </div>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Interview Analytics & Report
          </h1>
          <p className="mt-2 text-slate-400">
            AI-powered performance assessment evaluated against industry benchmarks.
          </p>

          {/* Performance Badge Banner */}
          <div className="mt-4 flex justify-center">
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1 text-xs font-semibold border ${
                isLowScore
                  ? 'border-rose-500/30 bg-rose-500/10 text-rose-300'
                  : scores.overall >= 80
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                  : 'border-blue-500/30 bg-blue-500/10 text-blue-300'
              }`}
            >
              {isLowScore && <AlertTriangle className="h-3.5 w-3.5" />}
              Performance: {result.performance || (isLowScore ? 'Unsatisfactory' : 'Good')}
            </span>
          </div>
        </div>

        {/* Top Scores */}
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
          {scoreCards.map((s) => (
            <ScoreCard key={s.label} {...s} />
          ))}
        </div>

        {/* Strengths & Weaknesses */}
        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="card p-6">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-400" />
              <h3 className="text-lg font-semibold text-white">Identified Strengths</h3>
            </div>
            <ul className="mt-4 space-y-3">
              {strengthsList.map((s, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-300">
                  <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${isLowScore ? 'bg-amber-400' : 'bg-emerald-400'}`} />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="card p-6">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-rose-400" />
              <h3 className="text-lg font-semibold text-white">Critical Areas for Growth</h3>
            </div>
            <ul className="mt-4 space-y-3">
              {improvementsList.map((s, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-300">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-400" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* AI Actionable Coaching Tips */}
        {suggestionsList.length > 0 && (
          <div className="mt-8 card p-6 border-blue-500/25 bg-blue-950/20">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-cyan-400" />
              <h3 className="text-lg font-semibold text-white">Actionable Interview Coaching</h3>
            </div>
            <ul className="mt-4 space-y-3">
              {suggestionsList.map((tip, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-200">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-400" />
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Skill Gap Analysis */}
        <div className="mt-8 card p-6">
          <h3 className="text-lg font-semibold text-white">Targeted Skill Gap Analysis</h3>
          <p className="mt-1 text-xs text-slate-400">
            Competency scores mapped to {result.role} core hiring criteria.
          </p>
          <div className="mt-5 grid gap-5 sm:grid-cols-2">
            {skillGapsList.map((g, i) => {
              const colors = isLowScore ? ['rose', 'amber', 'rose', 'amber'] : ['blue', 'cyan', 'violet', 'emerald'];
              return (
                <SkillBar
                  key={g.skill || i}
                  label={g.skill}
                  value={g.score}
                  color={colors[i % colors.length]}
                />
              );
            })}
          </div>
        </div>

        {/* Personalized Recommendations */}
        <div className="mt-8 card p-6">
          <div className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-violet-400" />
            <h3 className="text-lg font-semibold text-white">Recommended Learning Resources</h3>
          </div>
          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            {recommendationsList.map((r, i) => (
              <div
                key={i}
                className="flex items-start gap-3 rounded-xl border border-blue-500/15 bg-white/5 p-4 text-sm text-slate-300"
              >
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-lg bg-blue-500/10 text-xs font-semibold text-blue-400">
                  {i + 1}
                </span>
                <span>{r}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Question-by-Question Review */}
        {answersList.length > 0 && (
          <div className="mt-8 card p-6">
            <button
              onClick={() => setShowQAReview(!showQAReview)}
              className="flex w-full items-center justify-between text-left"
            >
              <div>
                <h3 className="text-lg font-semibold text-white">Question-by-Question Transcript</h3>
                <p className="text-xs text-slate-400">Review all questions asked and your recorded answers</p>
              </div>
              <div className="grid h-8 w-8 place-items-center rounded-lg bg-white/5 text-slate-300">
                {showQAReview ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </div>
            </button>

            {showQAReview && (
              <div className="mt-6 space-y-4 border-t border-white/5 pt-4">
                {answersList.map((item, idx) => (
                  <div key={idx} className="rounded-xl border border-white/5 bg-slate-900/40 p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-blue-400">Question {idx + 1}</span>
                    </div>
                    <p className="mt-1 text-sm font-semibold text-white">{item.question}</p>
                    <div className="mt-3 rounded-lg bg-black/30 p-3">
                      <span className="text-xs text-slate-500">Your Answer:</span>
                      <p className="mt-1 text-sm text-slate-300 italic">
                        {item.answer ? `"${item.answer}"` : '[Question was skipped]'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-10 flex flex-wrap justify-center gap-4">
          <Button onClick={() => navigate('/roles')} className="px-7 py-3.5">
            <RotateCcw className="h-4 w-4" />
            Practice Another Interview
          </Button>
          <Button to="/dashboard" variant="ghost" className="px-7 py-3.5">
            Back to Dashboard
          </Button>
        </div>
      </main>
      <Footer />
    </div>
  );
}
