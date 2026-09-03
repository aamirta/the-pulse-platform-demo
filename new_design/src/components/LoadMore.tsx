import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLanguage } from '@/context/LanguageContext';

interface LoadMoreProps {
  loaded: number;
  total: number;
  hasMore: boolean;
  isLoading: boolean;
  onLoadMore: () => void;
}

/**
 * "Showing X of Y" plus a load-more button for the directory listings.
 *
 * The directory pages requested a single page and rendered it with no indication
 * that more records existed, so most of the dataset was silently unreachable.
 */
export function LoadMore({ loaded, total, hasMore, isLoading, onLoadMore }: LoadMoreProps) {
  const { language } = useLanguage();

  if (total === 0) return null;

  return (
    <div className="flex flex-col items-center gap-3 pt-2">
      <p className="text-xs text-zinc-600 dark:text-zinc-300" aria-live="polite">
        {language === 'en' ? `Showing ${loaded} of ${total}` : `${loaded} sur ${total} affichés`}
      </p>
      {hasMore && (
        <Button
          variant="outline"
          onClick={onLoadMore}
          disabled={isLoading}
          className="h-9 px-5 text-xs dark:bg-zinc-800 dark:border-zinc-700 disabled:opacity-60"
        >
          {isLoading && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
          {isLoading
            ? language === 'en'
              ? 'Loading…'
              : 'Chargement…'
            : language === 'en'
              ? 'Load more'
              : 'Voir plus'}
        </Button>
      )}
    </div>
  );
}
