import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Lock, User, Mail } from 'lucide-react';

type LoginMode = 'admin' | 'member';

export default function Login() {
  const [mode, setMode] = useState<LoginMode>('admin');
  // Never prefill credentials: the form previously shipped a working
  // administrator username and password to every visitor.
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, memberLogin, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    let success: boolean;
    if (mode === 'admin') {
      success = await login(username, password);
    } else {
      success = await memberLogin(email, password);
    }
    if (success) {
      navigate('/dashboard');
    }
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="w-full max-w-md p-8 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-soft-lg ve-scale-in">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Sign in</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
            Access your account or dashboard
          </p>
        </div>

        <div className="flex p-1 bg-zinc-100 dark:bg-zinc-800 rounded-lg mb-6">
          <button
            type="button"
            onClick={() => setMode('admin')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
              mode === 'admin'
                ? 'bg-white dark:bg-zinc-950 text-pulse-orange shadow-sm'
                : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-950 dark:hover:text-zinc-200'
            }`}
          >
            Admin
          </button>
          <button
            type="button"
            onClick={() => setMode('member')}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
              mode === 'member'
                ? 'bg-white dark:bg-zinc-950 text-pulse-orange shadow-sm'
                : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-950 dark:hover:text-zinc-200'
            }`}
          >
            Member
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'admin' ? (
            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">Username</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <Input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>
          )}

          <div className="space-y-1">
            <label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10"
                required
              />
            </div>
          </div>

          <Button
            type="submit"
            disabled={isLoading}
            className="w-full bg-pulse-orange hover:bg-pulse-orange-hover text-white"
          >
            {isLoading ? 'Connexion...' : 'Se connecter'}
          </Button>
        </form>

        <div className="mt-2 flex items-center justify-between text-xs">
          <a
            href="/#/forgot-password"
            className="inline-flex items-center min-h-11 px-1 text-pulse-orange hover:underline rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
          >
            Forgot password?
          </a>
          <a
            href="/#/onboarding"
            className="inline-flex items-center min-h-11 px-1 text-pulse-orange hover:underline rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
          >
            Create account
          </a>
        </div>
      </div>
    </div>
  );
}
