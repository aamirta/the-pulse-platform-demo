import { useState } from 'react';
import { apiPost } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { Mail, ArrowLeft } from 'lucide-react';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes('@')) {
      toast.error('Please enter a valid email');
      return;
    }
    setLoading(true);
    try {
      await apiPost('/auth/forgot-password', { email: email.trim().toLowerCase() });
      setSent(true);
      toast.success('If an account exists, a reset link has been sent.');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Request failed';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="w-full max-w-md p-8 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-100 dark:border-zinc-800 shadow-soft-lg">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-white">Reset password</h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400 mt-1">
            Enter your email and we will send you a reset link.
          </p>
        </div>

        {sent ? (
          <div className="space-y-4 text-center">
            <p className="text-sm text-zinc-700 dark:text-zinc-300">
              Check your inbox for the reset link.
            </p>
            <a href="/#/login" className="inline-flex items-center text-sm text-pulse-orange hover:underline">
              <ArrowLeft className="w-4 h-4 mr-1" /> Back to sign in
            </a>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <Label className="text-xs font-semibold text-zinc-600 dark:text-zinc-300">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400" />
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-pulse-orange hover:bg-pulse-orange-hover text-white"
            >
              {loading ? 'Sending...' : 'Send reset link'}
            </Button>

            <p className="text-center text-xs text-zinc-500 dark:text-zinc-400">
              <a href="/#/login" className="text-pulse-orange hover:underline">
                Back to sign in
              </a>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
