import { Clock, ArrowUpRight, Newspaper } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { useLanguage } from '@/context/LanguageContext';
import { LoadMore } from '@/components/LoadMore';
import { useNews } from '@/hooks/useNews';
import { ImageWithFallback } from '@/components/ImageWithFallback';

export default function News() {
  const { t, language } = useLanguage();
  // The sidebar links to /news?type=blog; the view now reflects that instead of
  // rendering the unfiltered feed under a "Blog" heading.
  const [searchParams] = useSearchParams();
  const typeFilter = searchParams.get('type');
  const { data: newsItems = [], isLoading, total, hasMore, isLoadingMore, loadMore } =
    useNews();

  const badgeConfig: Record<string, { text: string; className: string }> = {
    blog: { text: language === 'en' ? 'BLOG' : 'BLOG', className: 'bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-100' },
    funding: { text: language === 'en' ? 'FUNDRAISING' : 'LEVÉE DE FONDS', className: 'bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-450 hover:bg-amber-100' },
    news: { text: language === 'en' ? 'NEWS' : 'ACTUALITÉ', className: 'bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 hover:bg-blue-100' },
    event: { text: language === 'en' ? 'EVENT' : 'ÉVÉNEMENT', className: 'bg-purple-100 dark:bg-purple-950/40 text-purple-650 dark:text-purple-400 hover:bg-purple-100' },
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1 font-serif">
          {typeFilter === 'blog' ? t('blogTitle') : t('newsTitle')}
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {typeFilter === 'blog' ? t('blogSubtitle') : t('newsSubtitle')}
        </p>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, idx) => (
            <div key={idx} className="flex gap-5 p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800">
              <Skeleton className="hidden sm:block w-[160px] h-[100px] rounded-lg" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-5 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <div className="flex gap-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-16" />
                </div>
              </div>
            </div>
          ))
        ) : newsItems.length === 0 ? (
          <div className="py-16 text-center bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800">
            <Newspaper className="w-10 h-10 text-zinc-300 dark:text-zinc-700 mx-auto mb-3" />
            <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              {typeFilter === 'blog' ? t('blogEmptyTitle') : t('newsEmptyTitle')}
            </p>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">{t('newsEmptyHint')}</p>
          </div>
        ) : (
          newsItems.map((item) => {
            const badge = badgeConfig[item.type] || badgeConfig['news'];
            return (
              <div
                key={item.id}
                className="flex gap-5 p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-md transition-all cursor-pointer group ve-card-lift"
              >
                <div className="hidden sm:block w-[160px] h-[100px] rounded-lg overflow-hidden flex-shrink-0">
                  <ImageWithFallback
                    src={item.image}
                    alt={item.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={`text-[10px] font-semibold px-1.5 py-0.5 ${badge.className}`}>
                      {badge.text}
                    </Badge>
                  </div>
                  <h3 className="text-base font-semibold text-zinc-900 dark:text-white mb-2 group-hover:text-pulse-orange dark:group-hover:text-orange-400 transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-sm text-zinc-550 dark:text-zinc-400 mb-3 line-clamp-2 leading-relaxed">
                    {item.description}
                  </p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1.5">
                        <div className="w-5 h-5 rounded-full bg-gradient-to-br from-pulse-orange-50 to-orange-100 dark:from-orange-950/40 dark:to-orange-900/10 flex items-center justify-center">
                          <span className="text-[9px] font-bold text-pulse-orange">
                            {item.source[0]}
                          </span>
                        </div>
                        <span className="text-xs text-zinc-600 dark:text-zinc-350 font-medium">
                          {item.source}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 text-zinc-400 dark:text-zinc-500">
                        <Clock className="w-3 h-3" />
                        <span className="text-[11px]">
                          {item.publishedAt
                            ? new Date(item.publishedAt).toLocaleDateString(
                                language === 'en' ? 'en-US' : 'fr-FR',
                                { day: 'numeric', month: 'short', year: 'numeric' },
                              )
                            : item.date}
                        </span>
                      </div>
                    </div>
                    <ArrowUpRight className="w-4 h-4 text-zinc-300 group-hover:text-pulse-orange transition-colors" />
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      <LoadMore
        loaded={newsItems.length}
        total={total}
        hasMore={hasMore}
        isLoading={isLoadingMore}
        onLoadMore={loadMore}
      />
    </div>
  );
}
