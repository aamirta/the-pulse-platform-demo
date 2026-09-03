import { useCallback, useEffect, useState } from 'react';
import { FileSignature, Loader2, Save, ShieldCheck } from 'lucide-react';
import { apiGet, apiPatch, apiPost } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import type {
  DealRoomPermission,
  DealRoomStatus,
  DealRoomSummary,
  NdaAcceptance,
  NdaView,
} from '@/types/dealroom';
import { EmptyState, Panel, formatDateTime, permissionLabel } from './shared';

const INVESTOR_PERMISSIONS: DealRoomPermission[] = [
  'view',
  'view_watermark',
  'download',
  'download_watermark',
];

interface Props {
  room: DealRoomSummary;
  language: string;
  onChanged: () => void;
}

/** Room policy: publication status, NDA gate, watermarking and download rules. */
export default function DealRoomSettings({ room, language, onChanged }: Props) {
  const en = language === 'en';

  const [status, setStatus] = useState<DealRoomStatus>(room.status);
  const [ndaRequired, setNdaRequired] = useState(room.nda_required);
  const [ndaBody, setNdaBody] = useState('');
  const [watermark, setWatermark] = useState(room.watermark_enabled);
  const [allowDownloads, setAllowDownloads] = useState(room.allow_downloads);
  const [defaultPermission, setDefaultPermission] = useState<DealRoomPermission>(
    INVESTOR_PERMISSIONS.includes(room.default_permission) ? room.default_permission : 'view_watermark',
  );
  const [name, setName] = useState(room.name ?? '');
  const [saving, setSaving] = useState(false);
  const [acceptances, setAcceptances] = useState<NdaAcceptance[]>([]);

  const loadNda = useCallback(async () => {
    try {
      const [nda, signed] = await Promise.all([
        apiGet<NdaView>(`/deal-rooms/${room.id}/nda`),
        apiGet<NdaAcceptance[]>(`/deal-rooms/${room.id}/nda/acceptances`),
      ]);
      setNdaBody(nda.body ?? '');
      setAcceptances(signed);
    } catch {
      // The NDA panel is supplementary; a failure here must not blank the form.
    }
  }, [room.id]);

  useEffect(() => {
    void loadNda();
  }, [loadNda]);

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await apiPatch(`/deal-rooms/${room.id}`, {
        name: name.trim() || null,
        status,
        nda_required: ndaRequired,
        nda_body: ndaBody.trim() || null,
        watermark_enabled: watermark,
        allow_downloads: allowDownloads,
        default_permission: defaultPermission,
      });
      toast.success(en ? 'Settings saved' : 'Paramètres enregistrés');
      onChanged();
      await loadNda();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <Panel title={en ? 'Room settings' : 'Paramètres de la salle'}>
        <form onSubmit={save} className="p-4 space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="dr-name" className="text-xs">{en ? 'Room name' : 'Nom de la salle'}</Label>
              <Input
                id="dr-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="h-9 text-sm dark:bg-zinc-950"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">{en ? 'Status' : 'Statut'}</Label>
              <Select value={status} onValueChange={(v) => setStatus(v as DealRoomStatus)}>
                <SelectTrigger className="h-9 text-xs dark:bg-zinc-950">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">{en ? 'Draft — invisible to investors' : 'Brouillon — invisible'}</SelectItem>
                  <SelectItem value="active">{en ? 'Active — investors can enter' : 'Actif — accès investisseurs'}</SelectItem>
                  <SelectItem value="paused">{en ? 'Paused — access held' : 'En pause — accès suspendu'}</SelectItem>
                  <SelectItem value="closed">{en ? 'Closed' : 'Fermé'}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">{en ? 'Default access for new investors' : 'Accès par défaut'}</Label>
            <Select
              value={defaultPermission}
              onValueChange={(v) => setDefaultPermission(v as DealRoomPermission)}
            >
              <SelectTrigger className="h-9 text-xs dark:bg-zinc-950 sm:w-1/2">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {INVESTOR_PERMISSIONS.map((permission) => (
                  <SelectItem key={permission} value={permission}>
                    {permissionLabel(permission, language)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-3 pt-1">
            <SettingToggle
              id="dr-watermark"
              checked={watermark}
              onChange={setWatermark}
              title={en ? 'Watermark every investor view' : 'Filigraner chaque consultation'}
              description={
                en
                  ? "Burns the viewer's email, id and timestamp into the file before it is sent, so a leaked copy is traceable. Applied on the server."
                  : "Incruste l'e-mail, l'identifiant et l'horodatage du lecteur avant l'envoi. Appliqué côté serveur."
              }
            />
            <SettingToggle
              id="dr-downloads"
              checked={allowDownloads}
              onChange={setAllowDownloads}
              title={en ? 'Allow downloads' : 'Autoriser les téléchargements'}
              description={
                en
                  ? 'When off, every investor is view-only regardless of their individual permission.'
                  : "Désactivé, tous les investisseurs sont en lecture seule, quel que soit leur droit."
              }
            />
            <SettingToggle
              id="dr-nda"
              checked={ndaRequired}
              onChange={setNdaRequired}
              title={en ? 'Require an NDA before opening documents' : 'Exiger un NDA avant consultation'}
              description={
                en
                  ? 'Investors must accept the agreement below before any document opens. Editing the text re-seals the room until they accept again.'
                  : "Les investisseurs doivent accepter l'accord ci-dessous. Modifier le texte referme la salle jusqu'à nouvelle acceptation."
              }
            />
          </div>

          {ndaRequired && (
            <div className="space-y-1.5">
              <Label htmlFor="dr-nda-body" className="text-xs">
                {en ? 'Agreement text' : "Texte de l'accord"}
                {room.nda_version && (
                  <span className="ml-2 text-[11px] text-zinc-500 dark:text-zinc-400">v{room.nda_version}</span>
                )}
              </Label>
              <Textarea
                id="dr-nda-body"
                value={ndaBody}
                onChange={(e) => setNdaBody(e.target.value)}
                rows={7}
                placeholder={
                  en
                    ? 'The recipient agrees to keep all materials in this deal room confidential…'
                    : 'Le destinataire s’engage à garder confidentiels tous les documents…'
                }
                className="text-sm dark:bg-zinc-950 leading-relaxed"
              />
            </div>
          )}

          <div className="flex justify-end pt-1">
            <Button
              type="submit"
              size="sm"
              disabled={saving}
              className="h-9 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground"
            >
              {saving ? (
                <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
              ) : (
                <Save className="w-3.5 h-3.5 mr-1.5" />
              )}
              {en ? 'Save settings' : 'Enregistrer'}
            </Button>
          </div>
        </form>
      </Panel>

      {room.nda_required && (
        <Panel title={en ? 'NDA acceptances' : 'Acceptations du NDA'}>
          {acceptances.length === 0 ? (
            <EmptyState
              icon={FileSignature}
              title={en ? 'Nobody has signed yet' : 'Aucune signature'}
              description={
                en
                  ? 'Each acceptance is recorded with the signer, the exact agreement version and their IP address.'
                  : "Chaque acceptation est enregistrée avec le signataire, la version exacte de l'accord et son adresse IP."
              }
            />
          ) : (
            <ul className="divide-y divide-zinc-50 dark:divide-zinc-800/60">
              {acceptances.map((item) => (
                <li key={item.id} className="px-4 py-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[13px] text-zinc-900 dark:text-white truncate">
                      {item.full_name || item.email}
                    </p>
                    <p className="text-[11px] text-zinc-600 dark:text-zinc-300">
                      {en ? 'Signed' : 'Signé'} “{item.signature_name}” · v{item.nda_version} ·{' '}
                      {formatDateTime(item.accepted_at, language)}
                      {item.ip && ` · ${item.ip}`}
                    </p>
                  </div>
                  <ShieldCheck className="w-4 h-4 text-emerald-700 dark:text-emerald-400 flex-shrink-0" />
                </li>
              ))}
            </ul>
          )}
        </Panel>
      )}
    </div>
  );
}

function SettingToggle({
  id,
  checked,
  onChange,
  title,
  description,
}: {
  id: string;
  checked: boolean;
  onChange: (value: boolean) => void;
  title: string;
  description: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4 p-3 rounded-lg bg-zinc-50 dark:bg-zinc-800/40">
      <div className="min-w-0">
        <Label htmlFor={id} className="text-[13px] font-medium cursor-pointer">
          {title}
        </Label>
        <p className="text-[11px] text-zinc-600 dark:text-zinc-300 mt-0.5 leading-relaxed">
          {description}
        </p>
      </div>
      <Switch id={id} checked={checked} onCheckedChange={onChange} className="flex-shrink-0 mt-0.5" />
    </div>
  );
}

/**
 * NDA gate shown to an investor who has not accepted the current agreement.
 *
 * Purely a convenience: the API refuses document links for an unsigned investor
 * regardless of what the UI renders, so skipping this screen gains nothing.
 */
export function NdaGate({
  room,
  language,
  onAccepted,
}: {
  room: DealRoomSummary;
  language: string;
  onAccepted: () => void;
}) {
  const en = language === 'en';
  const [nda, setNda] = useState<NdaView | null>(null);
  const [signature, setSignature] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        setNda(await apiGet<NdaView>(`/deal-rooms/${room.id}/nda`));
      } catch (err) {
        toast.error(err instanceof Error ? err.message : 'Could not load the agreement');
      }
    })();
  }, [room.id]);

  const accept = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    try {
      await apiPost(`/deal-rooms/${room.id}/nda/accept`, {
        signature_name: signature.trim(),
        accepted: true,
      });
      toast.success(en ? 'Agreement accepted' : 'Accord accepté');
      onAccepted();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Could not record acceptance');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel>
      <div className="p-6 max-w-2xl mx-auto">
        <div className="text-center mb-5">
          <div className="w-11 h-11 rounded-full bg-pulse-orange-50 dark:bg-zinc-800 grid place-items-center mx-auto mb-3">
            <FileSignature className="w-5 h-5 text-pulse-orange" />
          </div>
          <h2 className="text-base font-semibold text-zinc-900 dark:text-white">
            {en ? 'Confidentiality agreement' : 'Accord de confidentialité'}
          </h2>
          <p className="text-xs text-zinc-600 dark:text-zinc-300 mt-1">
            {en
              ? `${room.startup_name ?? 'This startup'} requires an NDA before you can open any document.`
              : `${room.startup_name ?? 'Cette startup'} exige un NDA avant toute consultation.`}
          </p>
        </div>

        <div className="max-h-64 overflow-y-auto rounded-lg border border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 p-4 text-[13px] text-zinc-700 dark:text-zinc-300 leading-relaxed whitespace-pre-wrap">
          {nda?.body || (en ? 'Loading the agreement…' : "Chargement de l'accord…")}
        </div>

        <form onSubmit={accept} className="mt-5 space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="dr-signature" className="text-xs">
              {en ? 'Type your full name to sign' : 'Saisissez votre nom complet pour signer'}
            </Label>
            <Input
              id="dr-signature"
              value={signature}
              onChange={(e) => setSignature(e.target.value)}
              required
              minLength={2}
              className="h-9 text-sm dark:bg-zinc-950"
            />
          </div>
          <p className="text-[11px] text-zinc-600 dark:text-zinc-300">
            {en
              ? 'Your name, the agreement version, the time and your IP address are recorded.'
              : "Votre nom, la version de l'accord, l'heure et votre adresse IP sont enregistrés."}
          </p>
          <Button
            type="submit"
            disabled={busy || signature.trim().length < 2}
            className="w-full h-10 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground"
          >
            {busy && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
            {en ? 'Accept and continue' : 'Accepter et continuer'}
          </Button>
        </form>
      </div>
    </Panel>
  );
}
