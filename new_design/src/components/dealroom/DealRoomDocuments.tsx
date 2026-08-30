import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Download,
  Eye,
  FileText,
  FolderPlus,
  Loader2,
  Search,
  ShieldCheck,
  Trash2,
  Upload,
  X,
} from 'lucide-react';
import { apiDelete, apiGet, apiPatch, apiPost } from '@/lib/api';
import { FadeInImage } from '@/enhancements/FadeInImage';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { openDealRoomDocument, saveBlob } from '@/hooks/useDealRoom';
import {
  DOCUMENT_CATEGORIES,
  type DealRoomDocument,
  type DealRoomFolder,
  type DealRoomSummary,
  type DocumentCategory,
  type PagedDocuments,
} from '@/types/dealroom';
import {
  EmptyState,
  ErrorState,
  Panel,
  PermissionBadge,
  RowSkeleton,
  StatusPill,
  categoryLabel,
  formatBytes,
  formatDate,
} from './shared';

const PAGE_SIZE = 20;

interface Props {
  room: DealRoomSummary;
  language: string;
  onChanged?: () => void;
}

/** Documents tab: browse, preview, download, and (for the startup) manage. */
export default function DealRoomDocuments({ room, language, onChanged }: Props) {
  const en = language === 'en';
  const isManager = room.viewer_role === 'startup' || room.viewer_role === 'admin';

  const [documents, setDocuments] = useState<PagedDocuments | null>(null);
  const [folders, setFolders] = useState<DealRoomFolder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<string>('all');
  const [folderId, setFolderId] = useState<string>('all');
  const [sort, setSort] = useState('recent');
  const [page, setPage] = useState(1);

  const [busyId, setBusyId] = useState<number | null>(null);
  const [preview, setPreview] = useState<{ url: string; title: string; type: string } | null>(null);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [folderOpen, setFolderOpen] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: String(page),
        page_size: String(PAGE_SIZE),
        sort,
      });
      if (search.trim()) params.set('q', search.trim());
      if (category !== 'all') params.set('category', category);
      if (folderId !== 'all') params.set('folder_id', folderId);

      const [docs, folderList] = await Promise.all([
        apiGet<PagedDocuments>(`/deal-rooms/${room.id}/documents?${params}`),
        apiGet<DealRoomFolder[]>(`/deal-rooms/${room.id}/folders`),
      ]);
      setDocuments(docs);
      setFolders(folderList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  }, [room.id, page, sort, search, category, folderId]);

  useEffect(() => {
    const timer = setTimeout(() => void load(), 200);
    return () => clearTimeout(timer);
  }, [load]);

  // Release the object URL when the preview closes, so blobs are not retained.
  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview.url);
    };
  }, [preview]);

  const openDocument = async (doc: DealRoomDocument, intent: 'preview' | 'download') => {
    setBusyId(doc.id);
    try {
      const { blobUrl, link } = await openDealRoomDocument(room.id, doc.id, intent);
      if (intent === 'download') {
        saveBlob(blobUrl, link.filename);
        // The blob has been handed to the browser; nothing else references it.
        setTimeout(() => URL.revokeObjectURL(blobUrl), 10_000);
        toast.success(
          link.watermarked
            ? en
              ? 'Downloaded — this copy is watermarked with your identity.'
              : 'Téléchargé — cette copie porte votre filigrane.'
            : en
              ? 'Downloaded.'
              : 'Téléchargé.',
        );
      } else {
        setPreview({ url: blobUrl, title: doc.title, type: link.content_type });
      }
      onChanged?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Could not open document');
    } finally {
      setBusyId(null);
    }
  };

  const patchDocument = async (doc: DealRoomDocument, body: Record<string, unknown>) => {
    setBusyId(doc.id);
    try {
      await apiPatch(`/deal-rooms/${room.id}/documents/${doc.id}`, body);
      await load();
      onChanged?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setBusyId(null);
    }
  };

  const removeDocument = async (doc: DealRoomDocument) => {
    if (!window.confirm(en ? `Delete “${doc.title}”? The file is erased.` : `Supprimer « ${doc.title} » ? Le fichier sera effacé.`)) {
      return;
    }
    setBusyId(doc.id);
    try {
      await apiDelete(`/deal-rooms/${room.id}/documents/${doc.id}`);
      toast.success(en ? 'Document deleted' : 'Document supprimé');
      await load();
      onChanged?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Delete failed');
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col lg:flex-row gap-2 lg:items-center">
        <div className="relative flex-1 min-w-0">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" />
          <Input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder={en ? 'Search documents' : 'Rechercher un document'}
            className="h-9 pl-8 text-sm dark:bg-zinc-900"
            aria-label={en ? 'Search documents' : 'Rechercher un document'}
          />
        </div>

        <div className="flex flex-wrap gap-2">
          <Select
            value={category}
            onValueChange={(v) => {
              setCategory(v);
              setPage(1);
            }}
          >
            <SelectTrigger className="h-9 w-[170px] text-xs dark:bg-zinc-900">
              <SelectValue placeholder={en ? 'Category' : 'Catégorie'} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{en ? 'All categories' : 'Toutes catégories'}</SelectItem>
              {DOCUMENT_CATEGORIES.map((c) => (
                <SelectItem key={c} value={c}>
                  {categoryLabel(c, language)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {folders.length > 0 && (
            <Select
              value={folderId}
              onValueChange={(v) => {
                setFolderId(v);
                setPage(1);
              }}
            >
              <SelectTrigger className="h-9 w-[150px] text-xs dark:bg-zinc-900">
                <SelectValue placeholder={en ? 'Folder' : 'Dossier'} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{en ? 'All folders' : 'Tous les dossiers'}</SelectItem>
                {folders.map((f) => (
                  <SelectItem key={f.id} value={String(f.id)}>
                    {f.name} ({f.document_count})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          <Select value={sort} onValueChange={setSort}>
            <SelectTrigger className="h-9 w-[130px] text-xs dark:bg-zinc-900">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="recent">{en ? 'Most recent' : 'Plus récents'}</SelectItem>
              <SelectItem value="title">{en ? 'Title' : 'Titre'}</SelectItem>
              <SelectItem value="category">{en ? 'Category' : 'Catégorie'}</SelectItem>
            </SelectContent>
          </Select>

          {isManager && (
            <>
              <Button
                size="sm"
                variant="outline"
                className="h-9 text-xs dark:bg-zinc-900 dark:border-zinc-700"
                onClick={() => setFolderOpen(true)}
              >
                <FolderPlus className="w-3.5 h-3.5 mr-1.5" />
                {en ? 'Folder' : 'Dossier'}
              </Button>
              <Button
                size="sm"
                className="h-9 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-white"
                onClick={() => setUploadOpen(true)}
              >
                <Upload className="w-3.5 h-3.5 mr-1.5" />
                {en ? 'Upload' : 'Téléverser'}
              </Button>
            </>
          )}
        </div>
      </div>

      <Panel>
        {loading ? (
          <RowSkeleton rows={5} />
        ) : error ? (
          <ErrorState message={error} onRetry={() => void load()} retryLabel={en ? 'Try again' : 'Réessayer'} />
        ) : !documents || documents.items.length === 0 ? (
          <EmptyState
            icon={FileText}
            title={en ? 'No documents' : 'Aucun document'}
            description={
              isManager
                ? en
                  ? 'Upload your pitch deck, financials and cap table, then publish them to share with investors.'
                  : 'Téléversez votre pitch deck, vos données financières et votre table de capitalisation, puis publiez-les.'
                : en
                  ? 'The startup has not shared any documents with you yet.'
                  : "La startup n'a encore partagé aucun document avec vous."
            }
            action={
              isManager ? (
                <Button
                  size="sm"
                  className="h-8 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-white"
                  onClick={() => setUploadOpen(true)}
                >
                  <Upload className="w-3.5 h-3.5 mr-1.5" />
                  {en ? 'Upload a document' : 'Téléverser un document'}
                </Button>
              ) : undefined
            }
          />
        ) : (
          <ul className="divide-y divide-zinc-50 dark:divide-zinc-800/60">
            {documents.items.map((doc) => (
              <li key={doc.id} className="px-4 py-3 flex items-center gap-3 hover:bg-zinc-50/60 dark:hover:bg-zinc-800/30 transition-colors">
                <div className="w-9 h-9 rounded-lg bg-pulse-orange-50 dark:bg-zinc-800 grid place-items-center flex-shrink-0">
                  <FileText className="w-4 h-4 text-pulse-orange" />
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-zinc-900 dark:text-white truncate">
                      {doc.title}
                    </span>
                    {isManager && <StatusPill status={doc.status} language={language} />}
                    {doc.watermarked && (
                      <span
                        className="inline-flex items-center gap-1 text-[10px] text-emerald-700 dark:text-emerald-400"
                        title={en ? 'Watermarked with your identity when opened' : 'Filigrané à votre identité'}
                      >
                        <ShieldCheck className="w-3 h-3" />
                        {en ? 'Watermarked' : 'Filigrané'}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5 truncate">
                    {categoryLabel(doc.category, language)}
                    {doc.current_version && ` · ${formatBytes(doc.current_version.byte_size)}`}
                    {doc.version_count > 1 && ` · v${doc.current_version?.version_no ?? doc.version_count}`}
                    {` · ${formatDate(doc.updated_at, language)}`}
                    {isManager && doc.view_count !== null && (
                      <> · {doc.view_count} {en ? 'views' : 'vues'}</>
                    )}
                  </p>
                </div>

                <div className="flex items-center gap-1 flex-shrink-0">
                  {!isManager && <PermissionBadge permission={doc.permission} language={language} className="mr-1 hidden sm:inline-flex" />}

                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-8 w-8 p-0"
                    onClick={() => void openDocument(doc, 'preview')}
                    disabled={busyId === doc.id}
                    aria-label={en ? `Preview ${doc.title}` : `Aperçu de ${doc.title}`}
                    title={en ? 'Preview' : 'Aperçu'}
                  >
                    {busyId === doc.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Eye className="w-3.5 h-3.5" />
                    )}
                  </Button>

                  {doc.can_download && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-8 w-8 p-0"
                      onClick={() => void openDocument(doc, 'download')}
                      disabled={busyId === doc.id}
                      aria-label={en ? `Download ${doc.title}` : `Télécharger ${doc.title}`}
                      title={en ? 'Download' : 'Télécharger'}
                    >
                      <Download className="w-3.5 h-3.5" />
                    </Button>
                  )}

                  {isManager && (
                    <>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 px-2 text-[11px]"
                        onClick={() =>
                          void patchDocument(doc, {
                            status: doc.status === 'published' ? 'draft' : 'published',
                          })
                        }
                        disabled={busyId === doc.id}
                      >
                        {doc.status === 'published'
                          ? en
                            ? 'Unpublish'
                            : 'Dépublier'
                          : en
                            ? 'Publish'
                            : 'Publier'}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0 text-red-500 hover:text-red-600"
                        onClick={() => void removeDocument(doc)}
                        disabled={busyId === doc.id}
                        aria-label={en ? `Delete ${doc.title}` : `Supprimer ${doc.title}`}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}

        {documents && documents.pages > 1 && (
          <footer className="px-4 py-3 border-t border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
            <span className="text-[11px] text-zinc-500 dark:text-zinc-400">
              {en
                ? `Page ${documents.page} of ${documents.pages} · ${documents.total} documents`
                : `Page ${documents.page} sur ${documents.pages} · ${documents.total} documents`}
            </span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-[11px] dark:bg-zinc-800 dark:border-zinc-700"
                disabled={documents.page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                {en ? 'Previous' : 'Précédent'}
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-[11px] dark:bg-zinc-800 dark:border-zinc-700"
                disabled={documents.page >= documents.pages}
                onClick={() => setPage((p) => p + 1)}
              >
                {en ? 'Next' : 'Suivant'}
              </Button>
            </div>
          </footer>
        )}
      </Panel>

      {preview && (
        <PreviewDialog
          preview={preview}
          onClose={() => {
            URL.revokeObjectURL(preview.url);
            setPreview(null);
          }}
          language={language}
        />
      )}

      {uploadOpen && (
        <UploadDialog
          roomId={room.id}
          folders={folders}
          language={language}
          onClose={() => setUploadOpen(false)}
          onUploaded={() => {
            setUploadOpen(false);
            void load();
            onChanged?.();
          }}
        />
      )}

      {folderOpen && (
        <FolderDialog
          roomId={room.id}
          language={language}
          onClose={() => setFolderOpen(false)}
          onCreated={() => {
            setFolderOpen(false);
            void load();
          }}
        />
      )}
    </div>
  );
}



function PreviewDialog({
  preview,
  onClose,
  language,
}: {
  preview: { url: string; title: string; type: string };
  onClose: () => void;
  language: string;
}) {
  const en = language === 'en';
  const isPdf = preview.type === 'application/pdf';
  const isImage = preview.type.startsWith('image/');

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-5xl h-[85vh] flex flex-col p-0 gap-0">
        <DialogHeader className="px-5 py-3 border-b border-zinc-100 dark:border-zinc-800 flex-row items-center justify-between space-y-0">
          <div className="min-w-0">
            <DialogTitle className="text-sm truncate">{preview.title}</DialogTitle>
            <DialogDescription className="text-[11px] flex items-center gap-1 mt-0.5">
              <ShieldCheck className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
              {en
                ? 'Confidential — this rendition is traceable to you.'
                : 'Confidentiel — cette version vous est attribuable.'}
            </DialogDescription>
          </div>
          <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={onClose} aria-label={en ? 'Close' : 'Fermer'}>
            <X className="w-4 h-4" />
          </Button>
        </DialogHeader>
        <div className="flex-1 overflow-auto bg-zinc-50 dark:bg-zinc-950 p-2">
          {isPdf ? (
            <object data={preview.url} type="application/pdf" className="w-full h-full rounded-lg">
              <p className="p-6 text-sm text-zinc-500 text-center">
                {en
                  ? 'Your browser cannot display this PDF inline.'
                  : "Votre navigateur ne peut pas afficher ce PDF."}
              </p>
            </object>
          ) : isImage ? (
            <FadeInImage src={preview.url} alt={preview.title} className="max-w-full mx-auto rounded-lg" />
          ) : (
            <div className="h-full grid place-items-center text-center p-8">
              <div>
                <FileText className="w-8 h-8 text-zinc-300 dark:text-zinc-600 mx-auto mb-3" />
                <p className="text-sm text-zinc-600 dark:text-zinc-300">
                  {en
                    ? 'This format cannot be previewed in the browser.'
                    : 'Ce format ne peut pas être prévisualisé.'}
                </p>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function UploadDialog({
  roomId,
  folders,
  language,
  onClose,
  onUploaded,
}: {
  roomId: number;
  folders: DealRoomFolder[];
  language: string;
  onClose: () => void;
  onUploaded: () => void;
}) {
  const en = language === 'en';
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState<DocumentCategory>('other');
  const [folder, setFolder] = useState('none');
  const [description, setDescription] = useState('');
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) {
      toast.error(en ? 'Choose a file first' : "Choisissez d'abord un fichier");
      return;
    }
    setBusy(true);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('title', title.trim() || file.name);
      form.append('category', category);
      if (folder !== 'none') form.append('folder_id', folder);
      if (description.trim()) form.append('description', description.trim());

      await apiPost(`/deal-rooms/${roomId}/documents`, form, true);
      toast.success(
        en
          ? 'Uploaded as a draft. Publish it when you are ready to share.'
          : 'Téléversé en brouillon. Publiez-le lorsque vous êtes prêt.',
      );
      onUploaded();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-base">{en ? 'Upload a document' : 'Téléverser un document'}</DialogTitle>
          <DialogDescription className="text-xs">
            {en
              ? 'PDF, image, Office or CSV, up to 50 MB. New documents start as drafts and stay private until you publish them.'
              : "PDF, image, Office ou CSV, jusqu'à 50 Mo. Les documents restent privés jusqu'à publication."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="dr-file" className="text-xs">{en ? 'File' : 'Fichier'}</Label>
            <Input
              id="dr-file"
              ref={fileRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.webp,.pptx,.xlsx,.docx,.csv"
              className="text-xs dark:bg-zinc-900"
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="dr-title" className="text-xs">{en ? 'Title' : 'Titre'}</Label>
            <Input
              id="dr-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={en ? 'Series A Pitch Deck' : 'Pitch Deck Série A'}
              className="h-9 text-sm dark:bg-zinc-900"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="text-xs">{en ? 'Category' : 'Catégorie'}</Label>
              <Select value={category} onValueChange={(v) => setCategory(v as DocumentCategory)}>
                <SelectTrigger className="h-9 text-xs dark:bg-zinc-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DOCUMENT_CATEGORIES.map((c) => (
                    <SelectItem key={c} value={c}>
                      {categoryLabel(c, language)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">{en ? 'Folder' : 'Dossier'}</Label>
              <Select value={folder} onValueChange={setFolder}>
                <SelectTrigger className="h-9 text-xs dark:bg-zinc-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">{en ? 'No folder' : 'Aucun dossier'}</SelectItem>
                  {folders.map((f) => (
                    <SelectItem key={f.id} value={String(f.id)}>
                      {f.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="dr-desc" className="text-xs">{en ? 'Description' : 'Description'}</Label>
            <Textarea
              id="dr-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="text-sm resize-none dark:bg-zinc-900"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" size="sm" className="h-9 text-xs" onClick={onClose}>
              {en ? 'Cancel' : 'Annuler'}
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={busy}
              className="h-9 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-white"
            >
              {busy && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
              {en ? 'Upload' : 'Téléverser'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function FolderDialog({
  roomId,
  language,
  onClose,
  onCreated,
}: {
  roomId: number;
  language: string;
  onClose: () => void;
  onCreated: () => void;
}) {
  const en = language === 'en';
  const [name, setName] = useState('');
  const [category, setCategory] = useState<DocumentCategory>('other');
  const [busy, setBusy] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    try {
      await apiPost(`/deal-rooms/${roomId}/folders`, { name: name.trim(), category });
      toast.success(en ? 'Folder created' : 'Dossier créé');
      onCreated();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Could not create folder');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="text-base">{en ? 'New folder' : 'Nouveau dossier'}</DialogTitle>
          <DialogDescription className="text-xs">
            {en
              ? 'Group related documents so investors can find them quickly.'
              : 'Regroupez les documents pour que les investisseurs les trouvent vite.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="dr-folder" className="text-xs">{en ? 'Name' : 'Nom'}</Label>
            <Input
              id="dr-folder"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="h-9 text-sm dark:bg-zinc-900"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">{en ? 'Category' : 'Catégorie'}</Label>
            <Select value={category} onValueChange={(v) => setCategory(v as DocumentCategory)}>
              <SelectTrigger className="h-9 text-xs dark:bg-zinc-900">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DOCUMENT_CATEGORIES.map((c) => (
                  <SelectItem key={c} value={c}>
                    {categoryLabel(c, language)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" size="sm" className="h-9 text-xs" onClick={onClose}>
              {en ? 'Cancel' : 'Annuler'}
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={busy || !name.trim()}
              className="h-9 text-xs bg-pulse-orange hover:bg-pulse-orange-hover text-white"
            >
              {busy && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
              {en ? 'Create' : 'Créer'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

