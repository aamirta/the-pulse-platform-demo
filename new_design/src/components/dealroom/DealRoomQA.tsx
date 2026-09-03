import { useCallback, useEffect, useState } from 'react';
import { Loader2, MessagesSquare, Send } from 'lucide-react';
import { apiGet, apiPost } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import type { DealRoomDocument, DealRoomSummary, Question } from '@/types/dealroom';
import {
  EmptyState,
  ErrorState,
  Panel,
  RowSkeleton,
  StatusPill,
  formatDateTime,
} from './shared';

interface Props {
  room: DealRoomSummary;
  language: string;
  documents?: DealRoomDocument[];
  onChanged?: () => void;
}

/**
 * Deal Room Q&A.
 *
 * The server decides what each caller sees: the startup gets every thread, an
 * investor gets only their own. Nothing here filters on the client, so a
 * rendering bug cannot expose one investor's questions to another.
 */
export default function DealRoomQA({ room, language, documents = [], onChanged }: Props) {
  const en = language === 'en';
  const isManager = room.viewer_role === 'startup' || room.viewer_role === 'admin';

  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [drafts, setDrafts] = useState<Record<number, string>>({});
  const [newQuestion, setNewQuestion] = useState('');
  const [documentId, setDocumentId] = useState('none');
  const [asking, setAsking] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setQuestions(await apiGet<Question[]>(`/deal-rooms/${room.id}/questions`));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load questions');
    } finally {
      setLoading(false);
    }
  }, [room.id]);

  useEffect(() => {
    void load();
  }, [load]);

  const ask = async (event: React.FormEvent) => {
    event.preventDefault();
    const body = newQuestion.trim();
    if (!body) return;
    setAsking(true);
    try {
      await apiPost(`/deal-rooms/${room.id}/questions`, {
        question: body,
        document_id: documentId === 'none' ? null : Number(documentId),
      });
      setNewQuestion('');
      setDocumentId('none');
      toast.success(en ? 'Question sent to the startup' : 'Question envoyée à la startup');
      await load();
      onChanged?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Could not send question');
    } finally {
      setAsking(false);
    }
  };

  const answer = async (question: Question) => {
    const body = (drafts[question.id] ?? '').trim();
    if (!body) return;
    setBusyId(question.id);
    try {
      await apiPost(`/deal-rooms/${room.id}/questions/${question.id}/answers`, { answer: body });
      setDrafts((prev) => ({ ...prev, [question.id]: '' }));
      toast.success(en ? 'Answer published' : 'Réponse publiée');
      await load();
      onChanged?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Could not publish answer');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-4">
      {!isManager && (
        <Panel title={en ? 'Ask a question' : 'Poser une question'}>
          <form onSubmit={ask} className="p-4 space-y-3">
            <Textarea
              value={newQuestion}
              onChange={(e) => setNewQuestion(e.target.value)}
              rows={3}
              placeholder={
                en
                  ? 'What would you like the startup to clarify?'
                  : 'Que souhaitez-vous que la startup clarifie ?'
              }
              className="text-sm resize-none dark:bg-zinc-950"
              aria-label={en ? 'Your question' : 'Votre question'}
            />
            <div className="flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between">
              {documents.length > 0 && (
                <Select value={documentId} onValueChange={setDocumentId}>
                  <SelectTrigger className="h-8 w-full sm:w-[240px] text-[11px] dark:bg-zinc-950">
                    <SelectValue placeholder={en ? 'About a document…' : 'À propos d’un document…'} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">
                      {en ? 'General question' : 'Question générale'}
                    </SelectItem>
                    {documents.map((doc) => (
                      <SelectItem key={doc.id} value={String(doc.id)}>
                        {doc.title}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              <Button
                type="submit"
                size="sm"
                disabled={asking || !newQuestion.trim()}
                className="h-8 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground sm:ml-auto"
              >
                {asking ? (
                  <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5 mr-1.5" />
                )}
                {en ? 'Send' : 'Envoyer'}
              </Button>
            </div>
            <p className="text-[11px] text-zinc-600 dark:text-zinc-300">
              {en
                ? 'Only you and the startup can see your questions.'
                : 'Vous seul et la startup pouvez voir vos questions.'}
            </p>
          </form>
        </Panel>
      )}

      <Panel
        title={
          isManager
            ? en ? 'Investor questions' : 'Questions des investisseurs'
            : en ? 'Your questions' : 'Vos questions'
        }
      >
        {loading ? (
          <RowSkeleton rows={3} />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void load()} retryLabel={en ? 'Try again' : 'Réessayer'} />
        ) : questions.length === 0 ? (
          <EmptyState
            icon={MessagesSquare}
            title={en ? 'No questions yet' : 'Aucune question'}
            description={
              isManager
                ? en
                  ? 'When an investor asks about a document, the thread appears here.'
                  : "Lorsqu'un investisseur pose une question, le fil apparaît ici."
                : en
                  ? 'Ask the startup anything about the materials you have been given.'
                  : 'Posez vos questions à la startup sur les documents partagés.'
            }
          />
        ) : (
          <ul className="divide-y divide-zinc-50 dark:divide-zinc-800/60">
            {questions.map((question) => (
              <li key={question.id} className="px-4 py-4 space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm text-zinc-900 dark:text-white leading-relaxed">
                      {question.question}
                    </p>
                    <p className="text-[11px] text-zinc-600 dark:text-zinc-300 mt-1">
                      {isManager && question.asked_by_name && `${question.asked_by_name} · `}
                      {formatDateTime(question.created_at, language)}
                      {question.document_title && ` · ${question.document_title}`}
                    </p>
                  </div>
                  <StatusPill status={question.status} language={language} />
                </div>

                {question.answers.length > 0 && (
                  <div className="space-y-2 pl-3 border-l-2 border-pulse-orange/30">
                    {question.answers.map((item) => (
                      <div key={item.id}>
                        <p className="text-[13px] text-zinc-700 dark:text-zinc-200 leading-relaxed whitespace-pre-wrap">
                          {item.answer}
                        </p>
                        <p className="text-[11px] text-zinc-600 dark:text-zinc-300 mt-0.5">
                          {item.answered_by_name} · {formatDateTime(item.created_at, language)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {isManager && (
                  <div className="flex gap-2 items-end pt-1">
                    <Textarea
                      value={drafts[question.id] ?? ''}
                      onChange={(e) =>
                        setDrafts((prev) => ({ ...prev, [question.id]: e.target.value }))
                      }
                      rows={1}
                      placeholder={en ? 'Write an answer…' : 'Rédiger une réponse…'}
                      className="flex-1 min-h-[36px] max-h-28 resize-none text-sm dark:bg-zinc-950"
                      aria-label={en ? 'Your answer' : 'Votre réponse'}
                    />
                    <Button
                      size="sm"
                      className="h-9 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground flex-shrink-0"
                      onClick={() => void answer(question)}
                      disabled={busyId === question.id || !(drafts[question.id] ?? '').trim()}
                    >
                      {busyId === question.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Send className="w-3.5 h-3.5" />
                      )}
                    </Button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </div>
  );
}
