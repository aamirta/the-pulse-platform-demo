/**
 * Create or edit an opportunity.
 *
 * The form is deliberately staged the way the ask itself reads: what kind of
 * opportunity, what it is, who you want, and then the optional commercial
 * detail. Only the first two groups are required, so posting "I need a
 * technical co-founder" does not demand a ticket size that does not exist.
 *
 * Every option list — post types, counterparties, stages, commitment levels,
 * the entities you may post on behalf of, the data rooms you may attach — comes
 * from the API. Nothing is hard-coded here, so the form can never offer a
 * choice the server would reject.
 */

import { useEffect, useState } from 'react';
import { Loader2, Save, Send } from 'lucide-react';
import { toast } from 'sonner';
import { apiGet, apiPatch, apiPost, type ApiError } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { DealRoomSummary } from '@/types/dealroom';
import type {
  CounterpartyType,
  DealRoomPostDetail,
  DealRoomPostInput,
  EntityType,
  PostMeta,
  PostType,
} from '@/types/dealroomPosts';
import { commitmentLabel, counterpartyLabel, postTypeLabel, stageLabel } from './shared';

/** One approved claim, as `/entity-claims/mine` returns it. */
interface EntityClaim {
  id: number;
  entity_type: EntityType;
  entity_id: number;
  entity_name: string | null;
  status: string;
}

interface ComposerProps {
  /** Present when editing; absent when creating. */
  existing?: DealRoomPostDetail | null;
  meta: PostMeta | null;
  language: string;
  onCancel: () => void;
  onSaved: (postId: number) => void;
}

/** A sentinel for "no selection", because Radix Select cannot hold an empty value. */
const NONE = '__none__';

export default function OpportunityComposer({
  existing,
  meta,
  language,
  onCancel,
  onSaved,
}: ComposerProps) {
  const en = language === 'en';
  const editing = !!existing;

  const [form, setForm] = useState<DealRoomPostInput>(() => ({
    post_type: existing?.post_type ?? ('raising_capital' as PostType),
    title: existing?.title ?? '',
    summary: existing?.summary ?? '',
    details: existing?.details ?? '',
    looking_for: existing?.looking_for ?? '',
    counterparty_type: existing?.counterparty_type ?? 'any',
    sector: existing?.sector ?? '',
    stage: existing?.stage ?? '',
    location: existing?.location ?? '',
    amount_min: existing?.amount_min == null ? null : Number(existing.amount_min),
    amount_max: existing?.amount_max == null ? null : Number(existing.amount_max),
    currency: existing?.currency ?? 'MAD',
    equity_offered: existing?.equity_offered ?? '',
    commitment: existing?.commitment ?? '',
    deadline: existing?.deadline ? existing.deadline.slice(0, 10) : '',
    tags: existing?.tags?.join(', ') ?? '',
    entity_type: existing?.author.entity_type ?? null,
    entity_id: existing?.author.entity_id ?? null,
    deal_room_id: existing?.deal_room_id ?? null,
  }));

  const [claims, setClaims] = useState<EntityClaim[]>([]);
  const [rooms, setRooms] = useState<DealRoomSummary[]>([]);
  const [saving, setSaving] = useState(false);

  // What this author may legitimately speak for, and which rooms they manage.
  // Both are re-verified server-side; loading them here only shapes the form.
  useEffect(() => {
    apiGet<EntityClaim[]>('/entity-claims/mine')
      .then((all) => setClaims(all.filter((claim) => claim.status === 'approved')))
      .catch(() => setClaims([]));
    apiGet<DealRoomSummary[]>('/deal-rooms/mine')
      .then(setRooms)
      .catch(() => setRooms([]));
  }, []);

  const set = <K extends keyof DealRoomPostInput>(key: K, value: DealRoomPostInput[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  // Mirrors the server's own minimums, so the button explains itself before the
  // request rather than after a 422.
  const titleOk = form.title.trim().length >= 6;
  const summaryOk = form.summary.trim().length >= 20;
  const detailsOk = form.details.trim().length >= 40;
  const rangeOk =
    form.amount_min == null || form.amount_max == null || form.amount_min <= form.amount_max;
  const valid = titleOk && summaryOk && detailsOk && rangeOk;

  /** Strip empty strings to null so the API sees "absent", not "blank". */
  const payload = (publish?: boolean): Record<string, unknown> => {
    const clean = (value: string | null | undefined) => {
      const trimmed = (value ?? '').trim();
      return trimmed === '' ? null : trimmed;
    };
    const body: Record<string, unknown> = {
      post_type: form.post_type,
      title: form.title.trim(),
      summary: form.summary.trim(),
      details: form.details.trim(),
      looking_for: clean(form.looking_for),
      counterparty_type: form.counterparty_type || 'any',
      sector: clean(form.sector),
      stage: clean(form.stage),
      location: clean(form.location),
      amount_min: form.amount_min ?? null,
      amount_max: form.amount_max ?? null,
      currency: clean(form.currency) ?? 'MAD',
      equity_offered: clean(form.equity_offered),
      commitment: clean(form.commitment),
      // A date input yields YYYY-MM-DD; the API wants a datetime, and the
      // deadline means "end of that day" rather than midnight at its start.
      deadline: form.deadline ? new Date(`${form.deadline}T23:59:59`).toISOString() : null,
      tags: clean(form.tags),
      entity_type: form.entity_type ?? null,
      entity_id: form.entity_id ?? null,
      deal_room_id: form.deal_room_id ?? null,
    };
    if (publish !== undefined) body.publish = publish;
    return body;
  };

  const save = async (publish: boolean) => {
    if (!valid || saving) return;
    setSaving(true);
    try {
      if (editing && existing) {
        await apiPatch<DealRoomPostDetail>(`/deal-room-posts/${existing.id}`, payload());
        // Publishing an existing draft is a lifecycle move, not an edit.
        if (publish && existing.status === 'draft') {
          await apiPost(`/deal-room-posts/${existing.id}/status`, { status: 'published' });
        }
        toast.success(en ? 'Opportunity updated' : 'Opportunité mise à jour');
        onSaved(existing.id);
      } else {
        const created = await apiPost<DealRoomPostDetail>('/deal-room-posts', payload(publish));
        toast.success(
          publish
            ? en
              ? 'Opportunity published'
              : 'Opportunité publiée'
            : en
              ? 'Draft saved'
              : 'Brouillon enregistré',
        );
        onSaved(created.id);
      }
    } catch (err) {
      toast.error(
        (err as ApiError).message || (en ? 'Could not save' : "Échec de l'enregistrement"),
      );
    } finally {
      setSaving(false);
    }
  };

  const field = 'text-sm';
  const sectionTitle = 'text-xs font-semibold uppercase tracking-wide text-zinc-400 mb-3';
  const card = 'bg-white dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-800 p-5';

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        void save(true);
      }}
    >
      {/* 1. What kind of ask */}
      <section className={card}>
        <h3 className={sectionTitle}>
          {en ? '1 · What are you posting?' : '1 · Que publiez-vous ?'}
        </h3>
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <Label className="text-xs mb-1.5 block">{en ? 'Type' : 'Type'}</Label>
            <Select
              value={form.post_type}
              onValueChange={(value) => set('post_type', value as PostType)}
            >
              <SelectTrigger className={field}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(meta?.post_types ?? []).map((type) => (
                  <SelectItem key={type} value={type} className="text-sm">
                    {postTypeLabel(type, language)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Attribution: only entities this member actually holds. */}
          {claims.length > 0 && (
            <div>
              <Label className="text-xs mb-1.5 block">
                {en ? 'Post on behalf of' : 'Publier au nom de'}
              </Label>
              <Select
                value={
                  form.entity_type && form.entity_id ? `${form.entity_type}:${form.entity_id}` : NONE
                }
                onValueChange={(value) => {
                  if (value === NONE) {
                    set('entity_type', null);
                    set('entity_id', null);
                    return;
                  }
                  const [type, id] = value.split(':');
                  set('entity_type', type as EntityType);
                  set('entity_id', Number(id));
                }}
              >
                <SelectTrigger className={field}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE} className="text-sm">
                    {en ? 'Myself' : 'Moi-même'}
                  </SelectItem>
                  {claims.map((claim) => (
                    <SelectItem
                      key={`${claim.entity_type}:${claim.entity_id}`}
                      value={`${claim.entity_type}:${claim.entity_id}`}
                      className="text-sm"
                    >
                      {claim.entity_name || `${claim.entity_type} #${claim.entity_id}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
      </section>

      {/* 2. The ask */}
      <section className={card}>
        <h3 className={sectionTitle}>
          {en ? '2 · What is the opportunity?' : "2 · Quelle est l'opportunité ?"}
        </h3>
        <div className="space-y-3">
          <div>
            <Label className="text-xs mb-1.5 block">
              {en ? 'Title' : 'Titre'} <span className="text-pulse-orange">*</span>
            </Label>
            <Input
              value={form.title}
              onChange={(event) => set('title', event.target.value)}
              maxLength={160}
              className={field}
              placeholder={
                en
                  ? 'e.g. Raising a 4M MAD seed round for our logistics platform'
                  : 'ex. Levée de 4M MAD en amorçage pour notre plateforme logistique'
              }
            />
            <p className="text-[10px] text-zinc-400 mt-1">
              {form.title.trim().length}/160
              {!titleOk && form.title.length > 0 && (
                <span className="text-amber-600 ml-2">
                  {en ? 'At least 6 characters' : 'Au moins 6 caractères'}
                </span>
              )}
            </p>
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">
              {en ? 'One-line summary' : 'Résumé en une ligne'}{' '}
              <span className="text-pulse-orange">*</span>
            </Label>
            <Textarea
              value={form.summary}
              onChange={(event) => set('summary', event.target.value)}
              rows={2}
              maxLength={400}
              className={`${field} resize-none`}
              placeholder={
                en
                  ? 'The hook people see on the board. What you do, the traction, and what you want.'
                  : "L'accroche visible sur le tableau. Ce que vous faites, la traction, et ce que vous cherchez."
              }
            />
            <p className="text-[10px] text-zinc-400 mt-1">
              {form.summary.trim().length}/400
              {!summaryOk && form.summary.length > 0 && (
                <span className="text-amber-600 ml-2">
                  {en ? 'At least 20 characters' : 'Au moins 20 caractères'}
                </span>
              )}
            </p>
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">
              {en ? 'Full details' : 'Détails complets'} <span className="text-pulse-orange">*</span>
            </Label>
            <Textarea
              value={form.details}
              onChange={(event) => set('details', event.target.value)}
              rows={7}
              maxLength={8000}
              className={`${field} resize-none`}
              placeholder={
                en
                  ? 'The purpose of the request, the numbers behind it, and anything a serious counterparty needs to judge the fit.'
                  : "L'objet de la demande, les chiffres qui la soutiennent, et tout ce qu'un interlocuteur sérieux doit savoir."
              }
            />
            <p className="text-[10px] text-zinc-400 mt-1">
              {form.details.trim().length}/8000
              {!detailsOk && form.details.length > 0 && (
                <span className="text-amber-600 ml-2">
                  {en ? 'At least 40 characters' : 'Au moins 40 caractères'}
                </span>
              )}
            </p>
          </div>
        </div>
      </section>

      {/* 3. Who they want */}
      <section className={card}>
        <h3 className={sectionTitle}>
          {en ? '3 · Who are you looking for?' : '3 · Qui recherchez-vous ?'}
        </h3>
        <div className="space-y-3">
          <div>
            <Label className="text-xs mb-1.5 block">{en ? 'Open to' : 'Ouvert à'}</Label>
            <Select
              value={form.counterparty_type || 'any'}
              onValueChange={(value) => set('counterparty_type', value as CounterpartyType)}
            >
              <SelectTrigger className={field}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {(meta?.counterparty_types ?? []).map((type) => (
                  <SelectItem key={type} value={type} className="text-sm">
                    {counterpartyLabel(type, language)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label className="text-xs mb-1.5 block">
              {en ? 'Describe the profile you want' : 'Décrivez le profil recherché'}
            </Label>
            <Textarea
              value={form.looking_for ?? ''}
              onChange={(event) => set('looking_for', event.target.value)}
              rows={4}
              maxLength={2000}
              className={`${field} resize-none`}
              placeholder={
                en
                  ? 'Be specific: sector experience, cheque size, geography, the kind of help that actually matters to you.'
                  : "Soyez précis : expérience sectorielle, taille de ticket, géographie, le type d'aide qui compte vraiment."
              }
            />
          </div>
        </div>
      </section>

      {/* 4. Optional detail */}
      <section className={card}>
        <h3 className={sectionTitle}>
          {en ? '4 · Details (all optional)' : '4 · Détails (facultatifs)'}
        </h3>
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <Label className="text-xs mb-1.5 block">{en ? 'Sector' : 'Secteur'}</Label>
            <Input
              value={form.sector ?? ''}
              onChange={(event) => set('sector', event.target.value)}
              maxLength={120}
              className={field}
              list="composer-sectors"
              placeholder={en ? 'e.g. Fintech' : 'ex. Fintech'}
            />
            {/* Suggestions from posts that already exist, so filters line up. */}
            <datalist id="composer-sectors">
              {(meta?.sectors ?? []).map((option) => (
                <option key={option.value} value={option.value} />
              ))}
            </datalist>
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">{en ? 'Stage' : 'Stade'}</Label>
            <Select
              value={form.stage || NONE}
              onValueChange={(value) => set('stage', value === NONE ? '' : value)}
            >
              <SelectTrigger className={field}>
                <SelectValue placeholder={en ? 'Not specified' : 'Non précisé'} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE} className="text-sm">
                  {en ? 'Not specified' : 'Non précisé'}
                </SelectItem>
                {(meta?.suggested_stages ?? []).map((stage) => (
                  <SelectItem key={stage} value={stage} className="text-sm">
                    {stageLabel(stage, language)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">{en ? 'Location' : 'Lieu'}</Label>
            <Input
              value={form.location ?? ''}
              onChange={(event) => set('location', event.target.value)}
              maxLength={120}
              className={field}
              list="composer-locations"
              placeholder={en ? 'e.g. Casablanca, Morocco' : 'ex. Casablanca, Maroc'}
            />
            <datalist id="composer-locations">
              {(meta?.locations ?? []).map((option) => (
                <option key={option.value} value={option.value} />
              ))}
            </datalist>
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">{en ? 'Commitment' : 'Engagement'}</Label>
            <Select
              value={form.commitment || NONE}
              onValueChange={(value) => set('commitment', value === NONE ? '' : value)}
            >
              <SelectTrigger className={field}>
                <SelectValue placeholder={en ? 'Not applicable' : 'Sans objet'} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={NONE} className="text-sm">
                  {en ? 'Not applicable' : 'Sans objet'}
                </SelectItem>
                {(meta?.commitment_levels ?? []).map((level) => (
                  <SelectItem key={level} value={level} className="text-sm">
                    {commitmentLabel(level, language)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">
              {en ? 'Amount from' : 'Montant à partir de'}
            </Label>
            <Input
              type="number"
              min={0}
              value={form.amount_min ?? ''}
              onChange={(event) =>
                set('amount_min', event.target.value === '' ? null : Number(event.target.value))
              }
              className={field}
              placeholder="0"
            />
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">{en ? 'Amount up to' : "Montant jusqu'à"}</Label>
            <Input
              type="number"
              min={0}
              value={form.amount_max ?? ''}
              onChange={(event) =>
                set('amount_max', event.target.value === '' ? null : Number(event.target.value))
              }
              className={field}
              placeholder="0"
            />
            {!rangeOk && (
              <p className="text-[10px] text-amber-600 mt-1">
                {en
                  ? 'The upper figure must be at least the lower one.'
                  : 'Le montant maximum doit être supérieur au minimum.'}
              </p>
            )}
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">{en ? 'Currency' : 'Devise'}</Label>
            <Input
              value={form.currency ?? ''}
              onChange={(event) => set('currency', event.target.value)}
              maxLength={8}
              className={field}
              placeholder="MAD"
            />
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">
              {en ? 'Equity offered' : 'Participation offerte'}
            </Label>
            <Input
              value={form.equity_offered ?? ''}
              onChange={(event) => set('equity_offered', event.target.value)}
              maxLength={60}
              className={field}
              placeholder={en ? 'e.g. 10-15%' : 'ex. 10-15%'}
            />
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">{en ? 'Closes on' : 'Clôture le'}</Label>
            <Input
              type="date"
              value={form.deadline ?? ''}
              onChange={(event) => set('deadline', event.target.value)}
              className={field}
              min={new Date(Date.now() + 86_400_000).toISOString().slice(0, 10)}
            />
          </div>

          <div>
            <Label className="text-xs mb-1.5 block">{en ? 'Tags' : 'Mots-clés'}</Label>
            <Input
              value={form.tags ?? ''}
              onChange={(event) => set('tags', event.target.value)}
              maxLength={400}
              className={field}
              placeholder={en ? 'comma, separated, keywords' : 'mots, clés, séparés'}
            />
          </div>

          {/* Only rooms this member manages; the server re-checks anyway. */}
          {rooms.length > 0 && (
            <div className="sm:col-span-2">
              <Label className="text-xs mb-1.5 block">
                {en ? 'Attach one of your data rooms' : 'Associer une de vos data rooms'}
              </Label>
              <Select
                value={form.deal_room_id ? String(form.deal_room_id) : NONE}
                onValueChange={(value) => set('deal_room_id', value === NONE ? null : Number(value))}
              >
                <SelectTrigger className={field}>
                  <SelectValue placeholder={en ? 'None' : 'Aucune'} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NONE} className="text-sm">
                    {en ? 'None' : 'Aucune'}
                  </SelectItem>
                  {rooms.map((room) => (
                    <SelectItem key={room.id} value={String(room.id)} className="text-sm">
                      {room.startup_name ?? room.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-[10px] text-zinc-400 mt-1">
                {en
                  ? 'Readers see that a data room exists. They still have to request access.'
                  : "Les lecteurs voient qu'une data room existe. Ils doivent toujours demander l'accès."}
              </p>
            </div>
          )}
        </div>
      </section>

      {/* Actions */}
      <div className="flex items-center gap-2 flex-wrap sticky bottom-0 bg-zinc-50/90 dark:bg-zinc-950/90 backdrop-blur py-3 -mx-1 px-1 rounded-lg">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel} disabled={saving}>
          {en ? 'Cancel' : 'Annuler'}
        </Button>
        {(!editing || existing?.status === 'draft') && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void save(false)}
            disabled={!valid || saving}
          >
            <Save className="w-3.5 h-3.5 mr-1.5" />
            {en ? 'Save draft' : 'Enregistrer'}
          </Button>
        )}
        <Button
          type="submit"
          size="sm"
          className="bg-pulse-orange hover:bg-pulse-orange-hover text-white ml-auto"
          disabled={!valid || saving}
        >
          {saving ? (
            <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
          ) : (
            <Send className="w-3.5 h-3.5 mr-1.5" />
          )}
          {editing
            ? existing?.status === 'draft'
              ? en
                ? 'Save and publish'
                : 'Enregistrer et publier'
              : en
                ? 'Save changes'
                : 'Enregistrer'
            : en
              ? 'Publish'
              : 'Publier'}
        </Button>
      </div>
    </form>
  );
}
