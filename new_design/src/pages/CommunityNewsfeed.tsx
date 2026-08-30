import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { FadeInImage } from '@/enhancements/FadeInImage';
import { Heart, MessageCircle, Loader2, Send } from 'lucide-react';

interface PostDetail {
  post_id: number;
  author_name?: string;
  author_role?: string;
  content: string;
  post_type?: string;
  image_url?: string;
  link_url?: string;
  link_title?: string;
  tags?: string;
  likes_count: number;
  comments_count: number;
  created_at: string;
  author_pic?: string;
  /** Resolved server-side for the caller; present on both list and detail. */
  liked_by_me?: boolean;
  // Only the single-post endpoint returns these arrays. The list returns counts,
  // so they are optional here — assuming otherwise crashed the whole page for
  // every signed-in member the moment the feed rendered.
  likes?: { id: number; actor_type: string; actor_id: number; created_at: string }[];
  comments?: { id: number; actor_type: string; actor_id: number; content: string; created_at: string }[];
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export default function Newsfeed() {
  const { member } = useAuth();
  const [posts, setPosts] = useState<PostDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [commentText, setCommentText] = useState<Record<number, string>>({});
  const [showComments, setShowComments] = useState<Record<number, boolean>>({});

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const data = await apiGet<PaginatedResponse<PostDetail>>('/members/newsfeed?page=1&page_size=20');
      setPosts(data.items);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load newsfeed';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const likePost = async (post: PostDetail) => {
    try {
      await apiPost(`/members/newsfeed/${post.post_id}/like`, {});
      const updated = await apiGet<PostDetail>(`/members/newsfeed/${post.post_id}`);
      setPosts((prev) => prev.map((p) => (p.post_id === post.post_id ? updated : p)));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Like failed';
      toast.error(message);
    }
  };

  const hasLiked = (post: PostDetail) => {
    if (!member) return false;
    // The list reports this directly; the detail response is matched against the
    // full array when it has been loaded.
    if (typeof post.liked_by_me === 'boolean') return post.liked_by_me;
    return (post.likes ?? []).some(
      (l) => l.actor_type === 'member' && l.actor_id === member.member_id,
    );
  };

  const submitComment = async (post: PostDetail) => {
    const text = commentText[post.post_id]?.trim();
    if (!text) return;
    try {
      await apiPost(`/members/newsfeed/${post.post_id}/comment`, { content: text });
      setCommentText((prev) => ({ ...prev, [post.post_id]: '' }));
      const updated = await apiGet<PostDetail>(`/members/newsfeed/${post.post_id}`);
      setPosts((prev) => prev.map((p) => (p.post_id === post.post_id ? updated : p)));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Comment failed';
      toast.error(message);
    }
  };

  /**
   * Show or hide a post's comments, fetching them the first time.
   *
   * The feed endpoint returns comment *counts*, not the comments themselves, so
   * expanding a post used to reveal an empty panel under a non-zero counter.
   */
  const toggleComments = async (post: PostDetail) => {
    const opening = !showComments[post.post_id];
    setShowComments((prev) => ({ ...prev, [post.post_id]: opening }));
    if (!opening || post.comments) return;
    try {
      const detail = await apiGet<PostDetail>(`/members/newsfeed/${post.post_id}`);
      setPosts((prev) => prev.map((p) => (p.post_id === post.post_id ? detail : p)));
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load comments');
    }
  };

  useEffect(() => {
    fetchPosts();
  }, []);

  return (
    <div className="max-w-2xl mx-auto py-6 space-y-4">
      <h1 className="text-2xl font-bold mb-4">Community Newsfeed</h1>

      {loading && posts.length === 0 && (
        <div className="flex justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-zinc-400" />
        </div>
      )}

      {posts.map((post) => (
        <div
          key={post.post_id}
          className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 shadow-soft-sm"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-pulse-orange/15 flex items-center justify-center text-pulse-orange font-bold">
              {(post.author_name || 'A')[0].toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-sm">{post.author_name || 'Anonymous'}</p>
              <p className="text-xs text-zinc-500">{post.author_role}</p>
            </div>
          </div>

          <p className="text-sm text-zinc-800 dark:text-zinc-200 mb-3">{post.content}</p>

          {post.image_url && (
            <FadeInImage src={post.image_url} alt="" className="rounded-lg mb-3 max-h-64 object-cover" />
          )}

          {post.link_url && (
            <a
              href={post.link_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center min-h-11 py-1 text-sm text-pulse-orange hover:underline mb-3 break-all rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
            >
              {post.link_title || post.link_url}
            </a>
          )}

          <div className="flex items-center gap-4 pt-3 border-t border-zinc-100 dark:border-zinc-800">
            <button
              onClick={() => likePost(post)}
              aria-label={`J'aime (${post.likes_count})`}
              aria-pressed={hasLiked(post)}
              className={`inline-flex items-center gap-1.5 min-h-11 px-2 -ml-2 rounded-lg text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60 ${
                hasLiked(post) ? 'text-red-500' : 'text-zinc-500 hover:text-red-500'
              }`}
            >
              <Heart className={`w-4 h-4 ${hasLiked(post) ? 'fill-current' : ''}`} aria-hidden="true" />
              {post.likes_count}
            </button>

            <button
              onClick={() => void toggleComments(post)}
              aria-label={`Commentaires (${post.comments_count})`}
              className="inline-flex items-center gap-1.5 min-h-11 px-2 rounded-lg text-xs font-semibold text-zinc-500 hover:text-pulse-orange transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
            >
              <MessageCircle className="w-4 h-4" aria-hidden="true" />
              {post.comments_count}
            </button>
          </div>

          {showComments[post.post_id] && (
            <div className="mt-4 space-y-3">
              {(post.comments ?? []).map((c) => (
                <div key={c.id} className="bg-zinc-50 dark:bg-zinc-800/50 p-3 rounded-lg text-sm">
                  <p>{c.content}</p>
                  <p className="text-[10px] text-zinc-500 mt-1">
                    {new Date(c.created_at).toLocaleString()}
                  </p>
                </div>
              ))}

              {member && (
                <div className="flex gap-2">
                  <Textarea
                    value={commentText[post.post_id] || ''}
                    onChange={(e) =>
                      setCommentText((prev) => ({ ...prev, [post.post_id]: e.target.value }))
                    }
                    placeholder="Add a comment..."
                    rows={2}
                    className="flex-1 min-h-[40px]"
                  />
                  <Button
                    onClick={() => submitComment(post)}
                    disabled={!commentText[post.post_id]?.trim()}
                    className="bg-pulse-orange hover:bg-pulse-orange-hover text-white"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      ))}

      {!loading && posts.length === 0 && (
        <p className="text-center text-sm text-zinc-500 py-8">No posts yet.</p>
      )}
    </div>
  );
}
