/**
 * The Deal Room marketplace.
 *
 * One component, four views, switched by local state rather than routes so the
 * board keeps its scroll position and filters when you open a post and come
 * back: `board` (everyone's live opportunities), `mine` (your own, drafts
 * included), `detail`, and `compose`.
 *
 * Filtering is done by the API. The filter bar's options come from
 * `/deal-room-posts/meta`, which derives sectors, stages and locations from the
 * posts that exist — so a filter never offers a value returning nothing.
 */

import { useEffect, useMemo, useState } from 'react';
import { ArrowLeft, Briefcase, Loader2, Plus, Search, SlidersHorizontal, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuth } from '@/context/AuthContext';
import { useDealRoomPosts, useMyDealRoomPosts, usePostMeta } from '@/hooks/useDealRoomPosts';
import type {
  BoardFilters,
  CounterpartyType,
  DealRoomPostDetail,
  DealRoomPostListItem,
  PostType,
} from '@/types/dealroomPosts';
import OpportunityCard from './OpportunityCard';
import OpportunityComposer from './OpportunityComposer';
import OpportunityDetail from './OpportunityDetail';
import { counterpartyLabel, postTypeLabel, stageLabel } from './shared';

type View = 'board' | 'mine' | 'detail' | 'compose';

/** Sentinel for "no filter", since Radix Select cannot hold an empty value. */
const ALL = '__all__';

interface OpportunityBoardProps {
  language: string;
}

export default function OpportunityBoard({ language }: OpportunityBoardProps) {
  const en = language === 'en';
  const { member, user, isBootstrapping } = useAuth();
  const signedIn = !isBootstrapping && (!!member || !!user);
  // Only members author posts; the platform administrator moderates instead.
  const canPost = !isBootstrapping && !!member;

  const [view, setView] = useState<View>('board');
  const [openPostId, setOpenPostId] = useState<number | null>(null);
  const [editing, setEditing] = useState<DealRoomPostDetail | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // `search` is what the user types; `q` is what reaches the API, debounced so a
  // request is not issued on every keystroke.
  const [search, setSearch] = useState('');
  const [q, setQ] = useState('');
  const [postType, setPostType] = useState('');
  const [counterparty, setCounterparty] = useState('');
  const [sector, setSector] = useState('');
  const [stage, setStage] = useState('');
  const [sort, setSort] = useState<BoardFilters['sort']>('recent');
  const [page, setPage] = useState(1);

  useEffect(() => {
    const timer = setTimeout(() => {
      setQ(search.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const filters = useMemo<BoardFilters>(
    () => ({
      q: q || undefined,
      post_type: (postType || undefined) as PostType | undefined,
      counterparty_type: (counterparty || undefined) as CounterpartyType | undefined,
      sector: sector || undefined,
      stage: stage || undefined,
      sort,
      page,
      page_size: 12,
    }),
    [q, postType, counterparty, sector, stage, sort, page],
  );

  const board = useDealRoomPosts(filters);
  const mine = useMyDealRoomPosts();
  const { meta, reload: reloadMeta } = usePostMeta();

  const activeFilterCount = [postType, counterparty, sector, stage].filter(Boolean).length;
  const clearFilters = () => {
    setPostType('');
    setCounterparty('');
    setSector('');
    setStage('');
    setPage(1);
  };

  const openPost = (post: DealRoomPostListItem) => {
    setOpenPostId(post.id);
    setView('detail');
  };

  const refreshAll = () => {
    board.reload();
    mine.reload();
    reloadMeta();
  };

  // ---------------------------------------------------------------- compose
  if (view === 'compose') {
    return (
      <div className="space-y-4 ve-view-enter" key="compose">
        <button
          type="button"
          onClick={() => {
            setEditing(null);
            setView(openPostId ? 'detail' : 'board');
          }}
          className="inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-pulse-orange transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          {en ? 'Back' : 'Retour'}
        </button>
        <div>
          <h2 className="text-base font-semibold text-zinc-900 dark:text-white">
            {editing
              ? en
                ? 'Edit opportunity'
                : "Modifier l'opportunité"
              : en
                ? 'Post an opportunity'
                : 'Publier une opportunité'}
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
            {en
              ? 'Say what you are looking for and who should reach out. Responses arrive in your inbox.'
              : 'Dites ce que vous cherchez et qui doit vous contacter. Les réponses arrivent dans votre boîte.'}
          </p>
        </div>
        <OpportunityComposer
          existing={editing}
          meta={meta}
          language={language}
          onCancel={() => {
            setEditing(null);
            setView(openPostId ? 'detail' : 'board');
          }}
          onSaved={(postId) => {
            setEditing(null);
            setOpenPostId(postId);
            refreshAll();
            setView('detail');
          }}
        />
      </div>
    );
  }

  // ----------------------------------------------------------------- detail
  if (view === 'detail' && openPostId !== null) {
    return (
      <div className="space-y-4 ve-view-enter" key={`detail-${openPostId}`}>
        <button
          type="button"
          onClick={() => {
            setOpenPostId(null);
            setView('board');
          }}
          className="inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-pulse-orange transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          {en ? 'Back to opportunities' : 'Retour aux opportunités'}
        </button>
        <OpportunityDetail
          postId={openPostId}
          meta={meta}
          language={language}
          onClose={() => {
            setOpenPostId(null);
            setView('board');
          }}
          onChanged={refreshAll}
          onEdit={(post) => {
            setEditing(post);
            setView('compose');
          }}
        />
      </div>
    );
  }

  // ------------------------------------------------------------------ lists
  const showingMine = view === 'mine';
  const state = showingMine ? mine : board;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-start sm:items-center gap-3 flex-col sm:flex-row">
        <div className="min-w-0 flex-1">
          <h2 className="text-base font-semibold text-zinc-900 dark:text-white">
            {en ? 'Opportunities' : 'Opportunités'}
          </h2>
          <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
            {en
              ? 'Capital, co-founders, partners and talent across the Moroccan ecosystem.'
              : "Capital, cofondateurs, partenaires et talents de l'écosystème marocain."}
          </p>
        </div>
        {canPost && (
          <Button
            size="sm"
            className="bg-pulse-orange hover:bg-pulse-orange-hover text-white flex-shrink-0"
            onClick={() => {
              setEditing(null);
              setOpenPostId(null);
              setView('compose');
            }}
          >
            <Plus className="w-3.5 h-3.5 mr-1.5" />
            {en ? 'Post an opportunity' : 'Publier'}
          </Button>
        )}
      </div>

      {/* Board / mine switch */}
      {signedIn && (
        <nav
          className="flex gap-1 border-b border-zinc-150 dark:border-zinc-800 -mb-px"
          role="tablist"
        >
          {(
            [
              { key: 'board' as View, label: en ? 'Browse' : 'Parcourir', count: board.total },
              { key: 'mine' as View, label: en ? 'My posts' : 'Mes publications', count: mine.total },
            ] as const
          ).map(({ key, label, count }) => (
            <button
              key={key}
              role="tab"
              aria-selected={view === key}
              onClick={() => setView(key)}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
                view === key
                  ? 'border-pulse-orange text-pulse-orange'
                  : 'border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200'
              }`}
            >
              {label}
              {count > 0 && <span className="text-[10px] text-zinc-400 font-normal">({count})</span>}
            </button>
          ))}
        </nav>
      )}

      {/* Filter bar — browse only */}
      {!showingMine && (
        <div className="space-y-2">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-400 pointer-events-none" />
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder={
                  en
                    ? 'Search opportunities, sectors, companies…'
                    : 'Rechercher opportunités, secteurs, entreprises…'
                }
                className="pl-8 text-sm h-9"
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600"
                  aria-label={en ? 'Clear search' : 'Effacer'}
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              className="h-9 flex-shrink-0"
              onClick={() => setShowFilters((open) => !open)}
            >
              <SlidersHorizontal className="w-3.5 h-3.5 sm:mr-1.5" />
              <span className="hidden sm:inline">{en ? 'Filters' : 'Filtres'}</span>
              {activeFilterCount > 0 && (
                <span className="ml-1.5 bg-pulse-orange text-white text-[9px] font-bold w-4 h-4 rounded-full grid place-items-center">
                  {activeFilterCount}
                </span>
              )}
            </Button>
          </div>

          {showFilters && (
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-2 p-3 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800">
              <Select
                value={postType || ALL}
                onValueChange={(value) => {
                  setPostType(value === ALL ? '' : value);
                  setPage(1);
                }}
              >
                <SelectTrigger className="text-xs h-8">
                  <SelectValue placeholder={en ? 'Any type' : 'Tout type'} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL} className="text-sm">
                    {en ? 'Any type' : 'Tout type'}
                  </SelectItem>
                  {(meta?.post_types ?? []).map((type) => (
                    <SelectItem key={type} value={type} className="text-sm">
                      {postTypeLabel(type, language)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={counterparty || ALL}
                onValueChange={(value) => {
                  setCounterparty(value === ALL ? '' : value);
                  setPage(1);
                }}
              >
                <SelectTrigger className="text-xs h-8">
                  <SelectValue placeholder={en ? "I'm a…" : 'Je suis…'} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL} className="text-sm">
                    {en ? 'Anyone' : 'Tout le monde'}
                  </SelectItem>
                  {(meta?.counterparty_types ?? [])
                    .filter((type) => type !== 'any')
                    .map((type) => (
                      <SelectItem key={type} value={type} className="text-sm">
                        {counterpartyLabel(type, language)}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>

              <Select
                value={sector || ALL}
                onValueChange={(value) => {
                  setSector(value === ALL ? '' : value);
                  setPage(1);
                }}
              >
                <SelectTrigger className="text-xs h-8">
                  <SelectValue placeholder={en ? 'Any sector' : 'Tout secteur'} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL} className="text-sm">
                    {en ? 'Any sector' : 'Tout secteur'}
                  </SelectItem>
                  {(meta?.sectors ?? []).map((option) => (
                    <SelectItem key={option.value} value={option.value} className="text-sm">
                      {option.value} ({option.count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={stage || ALL}
                onValueChange={(value) => {
                  setStage(value === ALL ? '' : value);
                  setPage(1);
                }}
              >
                <SelectTrigger className="text-xs h-8">
                  <SelectValue placeholder={en ? 'Any stage' : 'Tout stade'} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL} className="text-sm">
                    {en ? 'Any stage' : 'Tout stade'}
                  </SelectItem>
                  {(meta?.stages ?? []).map((option) => (
                    <SelectItem key={option.value} value={option.value} className="text-sm">
                      {stageLabel(option.value, language)} ({option.count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={sort ?? 'recent'}
                onValueChange={(value) => setSort(value as BoardFilters['sort'])}
              >
                <SelectTrigger className="text-xs h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="recent" className="text-sm">
                    {en ? 'Newest' : 'Plus récentes'}
                  </SelectItem>
                  <SelectItem value="responses" className="text-sm">
                    {en ? 'Most responses' : 'Plus de réponses'}
                  </SelectItem>
                  <SelectItem value="views" className="text-sm">
                    {en ? 'Most viewed' : 'Plus vues'}
                  </SelectItem>
                  <SelectItem value="deadline" className="text-sm">
                    {en ? 'Closing soonest' : 'Clôture proche'}
                  </SelectItem>
                </SelectContent>
              </Select>

              {activeFilterCount > 0 && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="col-span-2 lg:col-span-5 text-[11px] text-zinc-400 hover:text-pulse-orange text-left"
                >
                  {en ? 'Clear all filters' : 'Effacer les filtres'}
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {state.loading ? (
        <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              key={index}
              className="h-52 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 animate-pulse"
            />
          ))}
        </div>
      ) : state.error ? (
        <div className="text-center py-16 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">{state.error}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={state.reload}>
            {en ? 'Try again' : 'Réessayer'}
          </Button>
        </div>
      ) : state.posts.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800">
          <Briefcase className="w-8 h-8 text-zinc-300 dark:text-zinc-700 mx-auto mb-3 ve-float" />
          <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
            {showingMine
              ? en
                ? 'You have not posted anything yet'
                : "Vous n'avez rien publié"
              : activeFilterCount > 0 || q
                ? en
                  ? 'No opportunities match those filters'
                  : 'Aucune opportunité ne correspond'
                : en
                  ? 'No opportunities posted yet'
                  : 'Aucune opportunité publiée'}
          </p>
          <p className="text-xs text-zinc-400 mt-1 max-w-sm mx-auto">
            {showingMine
              ? en
                ? 'Post what you are looking for — capital, a co-founder, a partner — and responses land in your inbox.'
                : 'Publiez ce que vous cherchez — capital, cofondateur, partenaire — les réponses arrivent dans votre boîte.'
              : activeFilterCount > 0 || q
                ? en
                  ? 'Try widening the search.'
                  : "Essayez d'élargir la recherche."
                : en
                  ? 'Be the first to post one.'
                  : 'Soyez le premier à en publier une.'}
          </p>
          {(activeFilterCount > 0 || q) && !showingMine && (
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => {
                clearFilters();
                setSearch('');
              }}
            >
              {en ? 'Clear filters' : 'Effacer les filtres'}
            </Button>
          )}
          {showingMine && canPost && (
            <Button
              size="sm"
              className="mt-3 bg-pulse-orange hover:bg-pulse-orange-hover text-white"
              onClick={() => {
                setEditing(null);
                setView('compose');
              }}
            >
              <Plus className="w-3.5 h-3.5 mr-1.5" />
              {en ? 'Post an opportunity' : 'Publier'}
            </Button>
          )}
        </div>
      ) : (
        <>
          <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-3 ve-view-enter" key={showingMine ? 'mine' : 'board'}>
            {state.posts.map((post) => (
              <OpportunityCard
                key={post.id}
                post={post}
                language={language}
                onOpen={openPost}
                showStatus={showingMine}
              />
            ))}
          </div>

          {!showingMine && state.pages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1 || state.loading}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                {en ? 'Previous' : 'Précédent'}
              </Button>
              <span className="text-xs text-zinc-400">
                {en ? 'Page' : 'Page'} {state.page} / {state.pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= state.pages || state.loading}
                onClick={() => setPage((current) => current + 1)}
              >
                {state.loading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : en ? (
                  'Next'
                ) : (
                  'Suivant'
                )}
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
