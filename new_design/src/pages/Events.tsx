import { useState } from 'react';
import { MapPin, Calendar, Users, CheckCircle, CalendarX } from 'lucide-react';
import { toast } from 'sonner';
import { apiPost, type ApiError } from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useLanguage } from '@/context/LanguageContext';
import { useEvents } from '@/hooks/useEvents';
import type { Event } from '@/types';

export default function Events() {
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [successRegister, setSuccessRegister] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const { t, language } = useLanguage();
  const { data: events = [], isLoading } = useEvents();

  // Registration is persisted through the API. It previously only flipped a
  // local flag, so the success message appeared and the submission was lost.
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvent || submitting) return;

    setSubmitting(true);
    try {
      await apiPost(`/resources/${selectedEvent.id}/apply`, { message: message.trim() || null });
      setSuccessRegister(true);
      toast.success(language === 'en' ? 'Registration confirmed' : 'Inscription confirmée');
      setTimeout(() => {
        setSuccessRegister(false);
        setSelectedEvent(null);
        setMessage('');
      }, 1500);
    } catch (err) {
      const status = (err as ApiError).status;
      toast.error(
        status === 401 || status === 403
          ? language === 'en'
            ? 'Please sign in as a member to register'
            : 'Connectez-vous en tant que membre pour vous inscrire'
          : err instanceof Error
            ? err.message
            : 'Registration failed',
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1 font-serif">{t('eventsTitle')}</h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {t('eventsSubtitle')}
        </p>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, idx) => (
            <Skeleton key={idx} className="h-40 rounded-xl" />
          ))
        ) : events.length === 0 ? (
          /* Empty state: the list previously rendered nothing at all when the
             catalogue held no events, leaving a blank page. */
          <div className="py-16 text-center bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800">
            <CalendarX className="w-10 h-10 text-zinc-300 dark:text-zinc-700 mx-auto mb-3" />
            <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
              {language === 'en' ? 'No events scheduled yet' : 'Aucun événement programmé'}
            </p>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
              {language === 'en'
                ? 'New ecosystem events will appear here.'
                : 'Les prochains événements de l’écosystème apparaîtront ici.'}
            </p>
          </div>
        ) : (
          events.map((event) => {
            const startDate = new Date(event.startDate);
            const day = startDate.getDate();
            const month = startDate.toLocaleDateString(language === 'en' ? 'en-US' : 'fr-FR', { month: 'short' });

            return (
              <div
                key={event.id}
                className="flex flex-col sm:flex-row gap-5 p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-md transition-all group ve-card-lift"
              >
                {/* Date Badge */}
                <div className="flex flex-col items-center justify-center w-16 h-16 bg-purple-50 dark:bg-zinc-800 rounded-xl flex-shrink-0 self-start sm:self-center">
                  <span className="text-lg font-bold text-purple-700 dark:text-purple-400">{day}</span>
                  <span className="text-[10px] font-semibold text-purple-500 dark:text-purple-500 uppercase">
                    {month}
                  </span>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 space-y-3">
                  <div>
                    <h3 className="text-base font-semibold text-zinc-900 dark:text-white group-hover:text-pulse-orange dark:group-hover:text-orange-400 transition-colors">
                      {event.title}
                    </h3>
                    <p className="text-xs text-zinc-550 dark:text-zinc-400 mt-1 line-clamp-2 leading-relaxed">
                      {event.description}
                    </p>
                  </div>

                  {/* A speaker list was rendered here from hardcoded names
                      attributed to real people. There is no speaker data in the
                      backend, so it is omitted rather than invented. */}

                  <div className="flex flex-wrap items-center gap-4 text-xs text-zinc-500 dark:text-zinc-400 pt-1">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5" />
                      {event.location}
                    </span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {event.startDate}
                      {event.endDate && ` ${language === 'en' ? 'to' : 'au'} ${event.endDate}`}
                    </span>
                    {event.attendees && (
                      <span className="flex items-center gap-1">
                        <Users className="w-3.5 h-3.5" />
                        {event.attendees.toLocaleString()} {t('registeredLabel')}
                      </span>
                    )}
                  </div>
                </div>

                {/* Action */}
                <div className="flex items-center flex-shrink-0 self-end sm:self-center">
                  <Button
                    size="sm"
                    onClick={() => setSelectedEvent(event)}
                    className="h-9 px-5 bg-pulse-orange hover:bg-pulse-orange-hover text-white text-xs font-semibold rounded-lg border-none"
                  >
                    {t('registerButton')}
                  </Button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Registration Modal */}
      <Dialog open={selectedEvent !== null} onOpenChange={(open) => !open && setSelectedEvent(null)}>
        <DialogContent className="sm:max-w-[460px] dark:bg-zinc-900 dark:border-zinc-800">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-serif dark:text-white">
              {t('registerModalTitle')}
            </DialogTitle>
            <DialogDescription className="dark:text-zinc-400 text-xs">
              {t('registerModalSub')}
            </DialogDescription>
          </DialogHeader>

          {successRegister ? (
            <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
              <CheckCircle className="w-12 h-12 text-emerald-500 animate-bounce" />
              <h4 className="text-sm font-bold text-zinc-900 dark:text-white">{t('registerSuccessTitle')}</h4>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">{t('registerSuccessSub')}</p>
            </div>
          ) : (
            <form onSubmit={handleRegister} className="space-y-4 pt-3">
              <div className="p-3 bg-zinc-50 dark:bg-zinc-800 rounded-lg text-xs space-y-1.5 text-zinc-650 dark:text-zinc-300">
                <p><strong>{t('eventLabel')}</strong> {selectedEvent?.title}</p>
                <p><strong>{t('locationLabel')}</strong> {selectedEvent?.location}</p>
                <p><strong>{t('dateLabel')}</strong> {selectedEvent?.startDate}</p>
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="event-register-note"
                  className="text-xs font-medium text-zinc-700 dark:text-zinc-300"
                >
                  {language === 'en' ? 'Message (optional)' : 'Message (facultatif)'}
                </label>
                <textarea
                  id="event-register-note"
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  rows={3}
                  maxLength={5000}
                  className="w-full px-3 py-2 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg text-xs text-zinc-900 dark:text-white placeholder:text-zinc-400 focus:outline-none focus:border-pulse-orange/40 focus:ring-2 focus:ring-pulse-orange/10 transition-all"
                  placeholder={
                    language === 'en'
                      ? 'Anything the organisers should know?'
                      : 'Un mot pour les organisateurs ?'
                  }
                />
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setSelectedEvent(null)}
                  className="h-9 text-xs dark:bg-zinc-800 dark:border-zinc-700"
                >
                  {t('cancelButton')}
                </Button>
                <Button
                  type="submit"
                  disabled={submitting}
                  className="h-9 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-white rounded-lg border-none disabled:opacity-60"
                >
                  {submitting
                    ? language === 'en'
                      ? 'Submitting…'
                      : 'Envoi…'
                    : t('confirmRegisterButton')}
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
