import { useNavigate } from 'react-router-dom';
import { Home } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-20 h-20 rounded-2xl bg-zinc-100 flex items-center justify-center mb-4">
        <span className="text-3xl font-bold text-zinc-400">404</span>
      </div>
      <h2 className="text-xl font-semibold text-zinc-900 mb-2">
        Page non trouvée
      </h2>
      <p className="text-sm text-zinc-500 mb-6 max-w-sm">
        La page que vous recherchez n'existe pas ou a été déplacée.
      </p>
      <Button
        onClick={() => navigate('/')}
        className="bg-pulse-orange hover:bg-pulse-orange-hover text-white"
      >
        <Home className="w-4 h-4 mr-2" />
        Retour à l'accueil
      </Button>
    </div>
  );
}
