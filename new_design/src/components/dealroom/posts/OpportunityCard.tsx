/**
 * One opportunity on the board.
 *
 * The card answers four questions in reading order, because that is the order a
 * person actually asks them: what kind of ask is this, who is asking, what do
 * they want, and what is the shape of the deal. Everything else — the full
 * description, the "looking for" text — waits for the detail sheet.
 *
 * Nothing here decides permissions. `can_manage` and `responded_by_me` arrive
 * already resolved from the API for the current viewer.
 */

import { Clock, Eye, FileLock2, MapPin, MessagesSquare, Users } from 'lucide-react';
import { FadeInImage } from '@/enhancements/FadeInImage';
import type { DealRoomPostListItem } from '@/types/dealroomPosts';
import {
  Chip,
  PostTypeIcon,
  counterpartyLabel,
  daysUntil,
  formatAmountRange,
  initials,
  postStatusLabel,
  postTypeLabel,
  postTypeTone,
  relativeTime,
  stageLabel,
  statusTone,
} from './shared';

interface OpportunityCardProps {
  post: DealRoomPostListItem;
  language: string;
  onOpen: (post: DealRoomPostListItem) => void;
  /** Shown on the author's own board, where lifecycle matters more than contact. */
  showStatus?: boolean;
}

export default function OpportunityCard({
  post,
  language,
  onOpen,
  showStatus = false,
}: OpportunityCardProps) {
  const en = language === 'en';
  const author = post.author;
  const displayName = author.entity_name || author.full_name || (en ? 'Member' : 'Membre');
  const amount = formatAmountRange(post.amount_min, post.amount_max, post.currency, language);
  const remaining = daysUntil(post.deadline);
  // Only worth showing while it is still a deadline rather than a fact.
  const urgent = remaining !== null && remaining >= 0 && remaining <= 14;

  return (
    <article
      role="button"
      tabIndex={0}
      onClick={() => onOpen(post)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onOpen(post);
        }
      }}
      className="group text-left w-full bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-4 hover:border-pulse-orange/40 hover:shadow-sm transition-all cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/50 flex flex-col gap-3 ve-card-lift"
      aria-label={post.title}
    >
      {/* What kind of ask, and its state */}
      <div className="flex items-center gap-2 flex-wrap">
        <Chip
          icon={<PostTypeIcon type={post.post_type} className="w-3 h-3" />}
          className={postTypeTone(post.post_type)}
        >
          {postTypeLabel(post.post_type, language)}
        </Chip>
        {showStatus && (
          <Chip className={statusTone(post.status)}>{postStatusLabel(post.status, language)}</Chip>
        )}
        {post.moderation_status === 'flagged' && (
          <Chip className="bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20">
            {en ? 'Under review' : 'En examen'}
          </Chip>
        )}
        {post.has_deal_room && (
          <Chip
            icon={<FileLock2 className="w-3 h-3" />}
            className="bg-zinc-500/10 text-zinc-600 dark:text-zinc-300 border-zinc-500/20"
          >
            {en ? 'Data room' : 'Data room'}
          </Chip>
        )}
        <span className="ml-auto text-[10px] text-zinc-400 whitespace-nowrap">
          {relativeTime(post.published_at ?? post.created_at, language)}
        </span>
      </div>

      {/* The ask itself */}
      <div className="min-w-0">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-white leading-snug line-clamp-2 group-hover:text-pulse-orange transition-colors">
          {post.title}
        </h3>
        <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1.5 line-clamp-2 leading-relaxed">
          {post.summary}
        </p>
      </div>

      {/* The shape of the deal */}
      <div className="flex items-center gap-1.5 flex-wrap">
        {amount && (
          <Chip className="bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 border-transparent font-semibold">
            {amount}
          </Chip>
        )}
        {post.sector && (
          <Chip className="bg-transparent text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700">
            {post.sector}
          </Chip>
        )}
        {post.stage && post.stage !== 'not_applicable' && (
          <Chip className="bg-transparent text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700">
            {stageLabel(post.stage, language)}
          </Chip>
        )}
        {post.location && (
          <Chip
            icon={<MapPin className="w-2.5 h-2.5" />}
            className="bg-transparent text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700"
          >
            {post.location}
          </Chip>
        )}
        {urgent && (
          <Chip
            icon={<Clock className="w-2.5 h-2.5" />}
            className="bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20"
          >
            {remaining === 0
              ? en
                ? 'Closes today'
                : "Clôture aujourd'hui"
              : en
                ? `${remaining}d left`
                : `${remaining} j restants`}
          </Chip>
        )}
      </div>

      {/* Who is asking, and who they want to hear from */}
      <div className="flex items-center gap-2 pt-2.5 border-t border-zinc-50 dark:border-zinc-800 mt-auto">
        {author.profile_pic ? (
          <FadeInImage
            src={author.profile_pic}
            alt=""
            className="w-6 h-6 rounded-full object-cover flex-shrink-0"
          />
        ) : (
          <span className="w-6 h-6 rounded-full bg-pulse-orange/10 text-pulse-orange text-[9px] font-bold grid place-items-center flex-shrink-0">
            {initials(displayName)}
          </span>
        )}
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-medium text-zinc-700 dark:text-zinc-200 truncate">
            {displayName}
          </p>
          {post.counterparty_type !== 'any' && (
            <p className="text-[10px] text-zinc-400 truncate">
              {en ? 'Looking for' : 'Recherche'}{' '}
              {counterpartyLabel(post.counterparty_type, language).toLowerCase()}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2.5 text-[10px] text-zinc-400 flex-shrink-0">
          <span className="inline-flex items-center gap-0.5" title={en ? 'Views' : 'Vues'}>
            <Eye className="w-3 h-3" />
            {post.view_count}
          </span>
          <span className="inline-flex items-center gap-0.5" title={en ? 'Responses' : 'Réponses'}>
            <Users className="w-3 h-3" />
            {post.response_count}
          </span>
        </div>
      </div>

      {/* Already contacted: say so rather than inviting a duplicate */}
      {post.responded_by_me && (
        <p className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-600 dark:text-emerald-400 -mt-1">
          <MessagesSquare className="w-3 h-3" />
          {en ? 'You have contacted this author' : 'Vous avez déjà contacté cet auteur'}
        </p>
      )}
    </article>
  );
}
