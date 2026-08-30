import { useState } from 'react';
import { API_BASE_URL, getAccessToken } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Download, Loader2 } from 'lucide-react';

const CATEGORIES = [
  { value: 'entrepreneur', label: 'Entrepreneur / Startup' },
  { value: 'investisseur', label: 'Investisseur / VC' },
  { value: 'incubateur', label: 'Incubateur / Accélérateur' },
  { value: 'talent', label: 'Talent / Professionnel' },
  { value: 'expert', label: 'Expert / Mentor' },
  { value: 'venture_studio', label: 'Venture Studio' },
];

export default function BadgeDownload() {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    full_name: '',
    role_label: '',
    category: 'entrepreneur',
    ref_url: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.full_name.trim() || !form.role_label.trim()) {
      toast.error('Full name and role are required');
      return;
    }
    setLoading(true);
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {};
      if (token) headers.Authorization = `Bearer ${token}`;

      const formData = new FormData();
      formData.append('full_name', form.full_name.trim());
      formData.append('role_label', form.role_label.trim());
      formData.append('category', form.category);
      if (form.ref_url.trim()) formData.append('ref_url', form.ref_url.trim());

      const response = await fetch(`${API_BASE_URL}/members/badge`, {
        method: 'POST',
        headers,
        body: formData,
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status}: ${text}`);
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `the-pulse-badge-${form.full_name.trim().replace(/\s+/g, '-')}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Badge downloaded');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Download failed';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const update = (key: string, value: string) => setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="min-h-[60vh] flex items-center justify-center py-8">
      <div className="w-full max-w-md p-8 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-soft-lg">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Download your badge</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
            Generate a shareable PNG badge for your community profile.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">Full name</Label>
            <Input value={form.full_name} onChange={(e) => update('full_name', e.target.value)} />
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">Role label</Label>
            <Input value={form.role_label} onChange={(e) => update('role_label', e.target.value)} placeholder="e.g., Founder & CEO" />
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">Category</Label>
            <select
              value={form.category}
              onChange={(e) => update('category', e.target.value)}
              className="w-full h-10 rounded-md border border-input bg-background px-3 text-sm"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">Public profile URL (optional)</Label>
            <Input value={form.ref_url} onChange={(e) => update('ref_url', e.target.value)} placeholder="https://..." />
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-pulse-orange hover:bg-pulse-orange-hover text-white"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" /> Download badge
              </>
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
