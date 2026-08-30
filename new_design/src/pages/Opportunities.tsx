import { useState } from 'react';
import { toast } from 'sonner';
import { apiPost, type ApiError } from '@/lib/api';
import { Clock, Building2, ArrowUpRight, Sparkles, CheckCircle } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useLanguage } from '@/context/LanguageContext';
import { useOpportunities } from '@/hooks/useOpportunities';
import type { Opportunity } from '@/types';

export default function Opportunities() {
  const [selectedOpp, setSelectedOpp] = useState<Opportunity | null>(null);
  const [successApply, setSuccessApply] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [motivation, setMotivation] = useState('');
  const { t, language } = useLanguage();
  const { data: opportunities = [], isLoading } = useOpportunities();

  // The application is persisted through the API. It previously only flipped a
  // local flag — the success message appeared and the motivation text, which was
  // not even bound to state, was discarded.
  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOpp || submitting) return;

    setSubmitting(true);
    try {
      await apiPost(`/resources/${selectedOpp.id}/apply`, { message: motivation.trim() || null });
      setSuccessApply(true);
      toast.success(language === 'en' ? 'Application sent' : 'Candidature envoyée');
      setTimeout(() => {
        setSuccessApply(false);
        setSelectedOpp(null);
        setMotivation('');
      }, 1500);
    } catch (err) {
      const status = (err as ApiError).status;
      toast.error(
        status === 401 || status === 403
          ? language === 'en'
            ? 'Please sign in as a member to apply'
            : 'Connectez-vous en tant que membre pour postuler'
          : err instanceof Error
            ? err.message
            : 'Application failed',
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-900 dark:text-white mb-1 font-serif">{t('oppsTitle')}</h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {t('oppsSubtitle')}
        </p>
      </div>

      <div className="space-y-3">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, idx) => (
            <Skeleton key={idx} className="h-40 rounded-xl" />
          ))
        ) : (
          opportunities.map((opp) => (
            <div
              key={opp.id}
              className="p-5 bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 hover:border-zinc-200 dark:hover:border-zinc-700 hover:shadow-md transition-all group ve-card-lift"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Badge
                    variant="outline"
                    className="text-[10px] font-semibold border-pulse-orange/30 text-pulse-orange bg-pulse-orange-50/50 dark:bg-pulse-orange/10 dark:text-orange-400"
                  >
                    {opp.category}
                  </Badge>
                  
                  {/* An "AI match score" was rendered here from a hardcoded
                      lookup (96/87/74 by row index). No matching model exists,
                      so the invented figure is removed rather than displayed. */}
                </div>
                <ArrowUpRight className="w-4 h-4 text-zinc-300 group-hover:text-pulse-orange transition-colors" />
              </div>

              <h3 className="text-base font-semibold text-zinc-900 dark:text-white mb-2 group-hover:text-pulse-orange dark:group-hover:text-orange-400 transition-colors">
                {opp.title}
              </h3>

              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-4 leading-relaxed">
                {opp.description}
              </p>

              <div className="flex items-center justify-between pt-3 border-t border-zinc-50 dark:border-zinc-800/80">
                <div className="flex items-center gap-3 text-xs text-zinc-500 dark:text-zinc-400">
                  <span className="flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5" />
                    {opp.organization}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    {t('deadlineLabel')}{' '}
                    {new Date(opp.deadline).toLocaleDateString(language === 'en' ? 'en-US' : 'fr-FR')}
                  </span>
                </div>
                <Button
                  size="sm"
                  onClick={() => setSelectedOpp(opp)}
                  className="h-8 px-4 bg-pulse-orange hover:bg-pulse-orange-hover text-white text-xs font-semibold rounded-lg border-none"
                >
                  {t('applyButton')}
                </Button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Candidature Modal */}
      <Dialog open={selectedOpp !== null} onOpenChange={(open) => !open && setSelectedOpp(null)}>
        <DialogContent className="sm:max-w-[460px] dark:bg-zinc-900 dark:border-zinc-800">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-lg font-serif dark:text-white">
              <Sparkles className="w-5 h-5 text-pulse-orange" />
              {t('applyModalTitle')}
            </DialogTitle>
            <DialogDescription className="dark:text-zinc-400 text-xs">
              {t('applyModalSub')}
            </DialogDescription>
          </DialogHeader>

          {successApply ? (
            <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
              <CheckCircle className="w-12 h-12 text-emerald-500 animate-bounce" />
              <h4 className="text-sm font-bold text-zinc-900 dark:text-white">{t('applySuccessTitle')}</h4>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">{t('applySuccessSub')}</p>
            </div>
          ) : (
            <form onSubmit={handleApply} className="space-y-4 pt-3">
              <div className="p-3 bg-zinc-50 dark:bg-zinc-800/40 rounded-lg text-xs space-y-1.5 text-zinc-600 dark:text-zinc-300">
                <p><strong>{t('programLabel')}</strong> {selectedOpp?.title}</p>
                <p><strong>{t('organizerLabel')}</strong> {selectedOpp?.organization}</p>
              </div>

              <div className="space-y-1">
                <label htmlFor="opportunity-motivation" className="text-[11px] font-bold text-zinc-400 dark:text-zinc-500 uppercase">{t('motivationLabel')}</label>
                <textarea
                  id="opportunity-motivation"
                  value={motivation}
                  onChange={(event) => setMotivation(event.target.value)}
                  placeholder={t('motivationPlaceholder')}
                  rows={3}
                  maxLength={5000}
                  className="w-full p-2.5 text-xs bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg dark:text-white focus:outline-none focus:border-pulse-orange/40 focus:ring-2 focus:ring-pulse-orange/10"
                />
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <Button 
                  type="button"
                  variant="outline"
                  onClick={() => setSelectedOpp(null)}
                  className="h-9 text-xs dark:bg-zinc-800 dark:border-zinc-700"
                >
                  {t('cancelButton')}
                </Button>
                <Button
                  type="submit"
                  disabled={submitting}
                  className="h-9 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-white rounded-lg border-none disabled:opacity-60"
                >
                  {submitting ? (language === 'en' ? 'Sending…' : 'Envoi…') : t('confirmApplyButton')}
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
