import { useNavigate } from 'react-router-dom';
import { Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';

export default function NotFound() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-20 h-20 rounded-2xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center mb-4">
        <span className="text-3xl font-bold text-zinc-500 dark:text-zinc-400">404</span>
      </div>
      <h1 className="text-xl font-semibold text-zinc-900 dark:text-white mb-2">
        {t('notFoundTitle')}
      </h1>
      <p className="text-sm text-zinc-600 dark:text-zinc-300 mb-6 max-w-sm">{t('notFoundText')}</p>
      <Button
        onClick={() => navigate('/')}
        className="bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground"
      >
        <Home className="w-4 h-4 mr-2" aria-hidden="true" />
        {t('notFoundCta')}
      </Button>
    </div>
  );
}
