import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { useLanguage } from '@/context/LanguageContext';
import BrandLogo from '@/components/BrandLogo';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Lock, User } from 'lucide-react';

export default function Login() {
  const { t, language } = useLanguage();
  const isFr = language === 'fr';
  // One field for one form. The page used to ask people to declare "Admin" or
  // "Member" before typing anything and called a different endpoint for each;
  // the server owns both account stores, so it resolves the identifier and
  // reports the role back.
  // Never prefill credentials: the form previously shipped a working
  // administrator username and password to every visitor.
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const { signIn, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (await signIn(identifier, password)) {
      navigate('/dashboard');
    }
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="w-full max-w-md p-8 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-soft-lg ve-scale-in">
        <div className="flex flex-col items-center text-center mb-6">
          <BrandLogo className="h-7 mb-4" />
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">{t('loginTitle')}</h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-300 mt-1">{t('loginSubtitle')}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label htmlFor="login-identifier" className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">
              {t('loginUsername')}
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 dark:text-zinc-400" />
              <Input
                id="login-identifier"
                type="text"
                autoComplete="username"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                className="pl-10"
                required
              />
            </div>
          </div>

          <div className="space-y-1">
            <label htmlFor="login-password" className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">
              {t('loginPassword')}
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 dark:text-zinc-400" />
              <Input
                id="login-password"
                type="password"
                autoComplete="current-password"
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
            className="w-full bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground"
          >
            {isLoading ? (isFr ? 'Connexion…' : 'Signing in…') : t('connect')}
          </Button>
        </form>

        <div className="mt-2 flex items-center justify-between text-xs">
          <a
            href="/#/forgot-password"
            className="inline-flex items-center min-h-11 px-1 text-pulse-orange hover:underline rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
          >
            {t('loginForgot')}
          </a>
          <a
            href="/#/register"
            className="inline-flex items-center min-h-11 px-1 text-pulse-orange hover:underline rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
          >
            {t('createAccount')}
          </a>
        </div>
      </div>
    </div>
  );
}
