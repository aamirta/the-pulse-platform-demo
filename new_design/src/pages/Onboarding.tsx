import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiPost } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Mail, Lock, User, Briefcase, Linkedin, Image as ImageIcon } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';
import { describeError } from '@/lib/errors';
import BrandLogo from '@/components/BrandLogo';

/** Role values are what the API stores; only the labels are localised. */
const ROLES = [
  { value: 'startup', labelFr: 'Startup / Entrepreneur', labelEn: 'Startup / Entrepreneur' },
  { value: 'founder', labelFr: 'Fondateur', labelEn: 'Founder' },
  { value: 'investor', labelFr: 'Investisseur / VC', labelEn: 'Investor / VC' },
  {
    value: 'incubateur',
    labelFr: 'Incubateur / Accélérateur / Programme',
    labelEn: 'Incubator / Accelerator / Programme',
  },
  { value: 'talent', labelFr: 'Talent / Professionnel', labelEn: 'Talent / Professional' },
  { value: 'expert', labelFr: 'Expert / Mentor', labelEn: 'Expert / Mentor' },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const { language, t } = useLanguage();
  const isFr = language === 'fr';
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    role: '',
    password: '',
    linkedin: '',
    profile_pic: '',
    organization_name: '',
    sector: '',
    city: '',
    description: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const next: Record<string, string> = {};
    if (!form.full_name.trim())
      next.full_name = isFr ? 'Le nom complet est obligatoire.' : 'Full name is required.';
    if (!form.email.trim() || !form.email.includes('@'))
      next.email = isFr ? 'Une adresse e-mail valide est obligatoire.' : 'A valid email is required.';
    if (form.password.length < 8)
      next.password = isFr
        ? 'Le mot de passe doit contenir au moins 8 caractères.'
        : 'Password must be at least 8 characters.';
    if (!form.role) next.role = isFr ? 'Sélectionnez un rôle.' : 'Please select a role.';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      // The stable role value is what the API stores. It used to send the
      // English display label, which meant the stored role changed meaning the
      // moment that label was translated.
      const role = form.role;
      const form_data: Record<string, string> = {};
      if (form.organization_name) form_data.organization_name = form.organization_name;
      if (form.sector) form_data.sector = form.sector;
      if (form.city) form_data.city = form.city;
      if (form.description) form_data.description = form.description;
      if (form.linkedin) form_data.linkedin = form.linkedin;

      await apiPost('/members/onboard', {
        full_name: form.full_name.trim(),
        email: form.email.trim().toLowerCase(),
        role,
        password: form.password,
        linkedin: form.linkedin.trim() || undefined,
        profile_pic: form.profile_pic.trim() || undefined,
        form_data: Object.keys(form_data).length ? form_data : undefined,
      });
      toast.success(
        isFr
          ? 'Compte créé. Consultez votre e-mail pour le confirmer.'
          : 'Account created. Check your email to confirm it.',
      );
      navigate('/login');
    } catch (err) {
      toast.error(describeError(err, language));
    } finally {
      setLoading(false);
    }
  };

  const update = (key: string, value: string) => setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="min-h-[60vh] flex items-center justify-center py-8">
      <div className="w-full max-w-lg p-8 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-soft-lg">
        <div className="flex flex-col items-center text-center mb-6">
          <BrandLogo className="h-7 mb-4" />
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">
            {t('joinEcosystem')}
          </h1>
          <p className="text-sm text-zinc-600 dark:text-zinc-300 mt-1">{t('joinSub')}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">{isFr ? 'Nom complet' : 'Full name'}</Label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 dark:text-zinc-400" />
              <Input value={form.full_name} onChange={(e) => update('full_name', e.target.value)} className="pl-10" />
            </div>
            {errors.full_name && <p className="text-xs text-red-500">{errors.full_name}</p>}
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">{isFr ? 'Adresse e-mail' : 'Email address'}</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 dark:text-zinc-400" />
              <Input type="email" value={form.email} onChange={(e) => update('email', e.target.value)} className="pl-10" />
            </div>
            {errors.email && <p className="text-xs text-red-500">{errors.email}</p>}
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">{isFr ? 'Rôle' : 'Role'}</Label>
            <Select value={form.role} onValueChange={(value) => update('role', value)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder={isFr ? 'Sélectionnez votre rôle' : 'Select your role'} />
              </SelectTrigger>
              <SelectContent>
                {ROLES.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {isFr ? r.labelFr : r.labelEn}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.role && <p className="text-xs text-red-500">{errors.role}</p>}
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">{isFr ? 'Mot de passe' : 'Password'}</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 dark:text-zinc-400" />
              <Input type="password" value={form.password} onChange={(e) => update('password', e.target.value)} className="pl-10" />
            </div>
            {errors.password && <p className="text-xs text-red-500">{errors.password}</p>}
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">LinkedIn</Label>
            <div className="relative">
              <Linkedin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 dark:text-zinc-400" />
              <Input value={form.linkedin} onChange={(e) => update('linkedin', e.target.value)} className="pl-10" placeholder="https://linkedin.com/in/..." />
            </div>
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">{isFr ? 'Photo de profil (URL)' : 'Profile picture URL'}</Label>
            <div className="relative">
              <ImageIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 dark:text-zinc-400" />
              <Input value={form.profile_pic} onChange={(e) => update('profile_pic', e.target.value)} className="pl-10" placeholder="https://..." />
            </div>
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">{isFr ? 'Organisation / nom de la startup' : 'Organisation / startup name'}</Label>
            <div className="relative">
              <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 dark:text-zinc-400" />
              <Input value={form.organization_name} onChange={(e) => update('organization_name', e.target.value)} className="pl-10" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">{isFr ? 'Secteur' : 'Sector'}</Label>
              <Input value={form.sector} onChange={(e) => update('sector', e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">{isFr ? 'Ville' : 'City'}</Label>
              <Input value={form.city} onChange={(e) => update('city', e.target.value)} />
            </div>
          </div>

          <div className="space-y-1">
            <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">{isFr ? 'Bio / description' : 'Bio / description'}</Label>
            <Textarea value={form.description} onChange={(e) => update('description', e.target.value)} rows={3} />
          </div>

          <Button type="submit" disabled={loading} className="w-full bg-pulse-orange hover:bg-pulse-orange-hover text-primary-foreground">
            {loading ? (isFr ? 'Création du compte…' : 'Creating account…') : t('createAccount')}
          </Button>

          <p className="text-center text-xs text-zinc-600 dark:text-zinc-300">
            Already have an account?{' '}
            <a
              href="/#/login"
              className="inline-flex items-center min-h-11 px-1 text-pulse-orange hover:underline rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pulse-orange/60"
            >
              Sign in
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
