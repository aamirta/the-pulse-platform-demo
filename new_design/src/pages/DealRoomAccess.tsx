import { useNavigate } from 'react-router-dom';
import { Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';

/**
 * What a signed-out visitor sees at /deal-room.
 *
 * The route used to redirect straight to the login form, so the Deal Room had
 * no page of its own and nothing explained what was behind the wall. This
 * names the space and offers the two ways in. It renders only when there is no
 * session -- `ProtectedRoute` still gates the room itself.
 */
export default function DealRoomAccess() {
  const navigate = useNavigate();
  const { language } = useLanguage();
  const isFr = language === 'fr';

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4 py-16">
      <div className="max-w-md text-center">
        <span className="inline-flex p-3 rounded-2xl bg-pulse-orange/10 text-pulse-orange mb-4">
          <Lock className="w-6 h-6" aria-hidden="true" />
        </span>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
          Deal Room
        </h1>
        <p className="text-sm text-zinc-600 dark:text-zinc-300 mt-3 leading-relaxed">
          {isFr
            ? "L'espace où les startups qui lèvent rencontrent les investisseurs membres. Accès réservé aux membres connectés."
            : 'Where startups that are raising meet member investors. Access is reserved for signed-in members.'}
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center mt-6">
          <Button
            onClick={() => navigate('/login')}
            className="bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground rounded-lg"
          >
            {isFr ? 'Se connecter' : 'Sign in'}
          </Button>
          <Button variant="outline" onClick={() => navigate('/register')} className="rounded-lg">
            {isFr ? 'Demander un accès' : 'Request access'}
          </Button>
        </div>
      </div>
    </div>
  );
}
