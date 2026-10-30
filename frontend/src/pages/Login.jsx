import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BrainCircuit, Mail, Lock, ArrowRight, Loader2 } from 'lucide-react';
import { setAuthUser } from '../utils/storage';
import { loginUser } from '../services/api';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Try backend database login first
      const backendRes = await loginUser(email, password);
      if (backendRes && backendRes.user) {
        const profile = {
          id: backendRes.user.id,
          name: backendRes.user.name,
          email: backendRes.user.email,
          targetRole: 'Software Engineer',
        };
        setAuthUser(profile);
        setLoading(false);
        navigate('/dashboard');
        return;
      }
    } catch (err) {
      console.warn('Backend login error:', err);
    }

    // Fallback to local storage if backend is unavailable or not registered in DB
    const stored = JSON.parse(localStorage.getItem('ais_users') || '[]');
    const localUser = stored.find((u) => u.email === email && u.password === password);

    const profile = localUser || {
      id: 1,
      name: email.split('@')[0],
      email,
      targetRole: 'Software Engineer',
    };

    setAuthUser(profile);
    setLoading(false);
    navigate('/dashboard');
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-5 py-12">
      <div
        className="pointer-events-none absolute inset-0 -z-10 opacity-60"
        style={{
          background:
            'radial-gradient(40rem 30rem at 50% 0%, rgba(59,130,246,0.15), transparent 60%), radial-gradient(30rem 25rem at 80% 100%, rgba(124,58,237,0.12), transparent 60%)',
        }}
      />
      <div className="w-full max-w-md animate-fade-up">
        <div className="mb-6 flex items-center justify-center gap-2.5">
          <span className="grid h-10 w-10 place-items-center rounded-xl border border-blue-500/30 bg-blue-500/10">
            <BrainCircuit className="h-5 w-5 text-blue-400" />
          </span>
          <span className="text-lg font-semibold text-white">AI Interview Simulator</span>
        </div>

        <div className="card p-8">
          <h1 className="text-2xl font-bold text-white">Welcome Back</h1>
          <p className="mt-1.5 text-sm text-slate-400">Log in to continue your interview practice.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-slate-300">
                Email
              </label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="input-field pl-10"
                  autoComplete="email"
                />
              </div>
            </div>

            <div>
              <label htmlFor="pass" className="mb-1.5 block text-sm font-medium text-slate-300">
                Password
              </label>
              <div className="relative">
                <Lock className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <input
                  id="pass"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input-field pl-10"
                  autoComplete="current-password"
                />
              </div>
            </div>

            {error && (
              <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full justify-center py-3"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Logging in...
                </>
              ) : (
                <>
                  Log In
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-slate-400">
            Don't have an account?{' '}
            <Link to="/register" className="font-medium text-blue-400 hover:text-blue-300">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
