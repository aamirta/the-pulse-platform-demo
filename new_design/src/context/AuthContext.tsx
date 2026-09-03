import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import {
  apiGet,
  apiPost,
  setAccessToken,
  getAccessToken,
  refreshAccessToken,
  setSessionExpiredHandler,
  REFRESH_TOKEN_KEY,
} from '@/lib/api';
import { toast } from 'sonner';

export interface User {
  user_id: number;
  username: string;
  role: string;
  is_active: boolean;
}

export interface MemberProfile {
  member_id: number;
  full_name: string;
  role: string;
  email: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** Response of the unified `/auth/signin` endpoint. */
export interface SignInResponse extends AuthTokens {
  account_type: 'admin' | 'member';
  member_id?: number | null;
  full_name?: string | null;
  role?: string | null;
}

/** Roles the dashboard understands, always derived from the authenticated identity. */
export type DashboardRole = 'startup' | 'investor' | 'partner' | 'admin';

interface AuthContextType {
  user: User | null;
  member: MemberProfile | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  /** True until the stored session has been checked on first paint. */
  isBootstrapping: boolean;
  /** Server-derived role; null when signed out. */
  role: DashboardRole | null;
  /** Single entry point: the server resolves admin vs member. */
  signIn: (identifier: string, password: string) => Promise<boolean>;
  login: (username: string, password: string) => Promise<boolean>;
  memberLogin: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  refresh: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const MEMBER_KEY = 'pulse-member';
/** Bumped on logout so other tabs can drop their session too. */
const LOGOUT_BROADCAST_KEY = 'pulse-logout-at';

/**
 * Map a member's self-declared role string onto a dashboard view.
 *
 * The member role is free text captured at onboarding (French and English
 * variants both occur), so it is normalised here rather than trusted verbatim.
 */
export function roleToDashboardRole(role: string | undefined | null): DashboardRole {
  const value = (role ?? '').toLowerCase();
  if (/investor|investisseur|vc|business angel|fond/.test(value)) return 'investor';
  if (/incubateur|accelerateur|accélérateur|programme|partner|partenaire|studio/.test(value)) {
    return 'partner';
  }
  return 'startup';
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [member, setMember] = useState<MemberProfile | null>(() => {
    try {
      const raw = localStorage.getItem(MEMBER_KEY);
      return raw ? (JSON.parse(raw) as MemberProfile) : null;
    } catch {
      return null;
    }
  });
  const [accessToken, setAccessTokenState] = useState<string | null>(() => getAccessToken());
  const [isLoading, setIsLoading] = useState(false);
  // A refresh token on disk means there may be a session to restore, so hold
  // route rendering until the bootstrap below resolves. Without this, a browser
  // refresh briefly reported "signed out" and bounced users to /login.
  const [isBootstrapping, setIsBootstrapping] = useState(
    () => !!localStorage.getItem(REFRESH_TOKEN_KEY),
  );

  const updateTokens = useCallback((tokens: AuthTokens | null) => {
    if (tokens) {
      setAccessToken(tokens.access_token);
      setAccessTokenState(tokens.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    } else {
      setAccessToken(null);
      setAccessTokenState(null);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
    }
  }, []);

  const login = useCallback(async (username: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      const tokens = await apiPost<AuthTokens>('/auth/login', formData, true);
      updateTokens(tokens);
      // Identity comes from the server rather than being assumed: a row in the
      // User table is not necessarily the administrator.
      const profile = await apiGet<User>('/auth/me');
      setUser(profile);
      setMember(null);
      localStorage.removeItem(MEMBER_KEY);
      toast.success('Connexion réussie');
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Échec de la connexion';
      toast.error(message);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [updateTokens]);

  /**
   * Single sign-in: the server decides which account the credentials belong to.
   *
   * The form used to make the person choose "Admin" or "Member" up front and
   * called a different endpoint for each. Both stores live on the server, so it
   * resolves the identifier and tells us which kind of session came back.
   */
  const signIn = useCallback(async (identifier: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const res = await apiPost<SignInResponse>('/auth/signin', { identifier, password });
      const { access_token, refresh_token, token_type } = res;
      updateTokens({ access_token, refresh_token, token_type });

      if (res.account_type === 'member') {
        const profile = {
          member_id: res.member_id as number,
          full_name: res.full_name ?? '',
          role: res.role ?? '',
          email: identifier.trim().toLowerCase(),
        };
        setMember(profile);
        localStorage.setItem(MEMBER_KEY, JSON.stringify(profile));
        setUser(null);
      } else {
        // Identity still comes from the server: a row in the User table is not
        // automatically the administrator.
        const profile = await apiGet<User>('/auth/me');
        setUser(profile);
        setMember(null);
        localStorage.removeItem(MEMBER_KEY);
      }
      toast.success('Connexion réussie');
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Échec de la connexion';
      toast.error(message);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [updateTokens]);

  const memberLogin = useCallback(async (email: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const response = await apiPost<AuthTokens & MemberProfile>('/auth/member-login', {
        email,
        password,
      });
      const { access_token, refresh_token, token_type, member_id, full_name, role } = response;
      updateTokens({ access_token, refresh_token, token_type });
      const profile = { member_id, full_name, role, email: email.trim().toLowerCase() };
      setMember(profile);
      localStorage.setItem(MEMBER_KEY, JSON.stringify(profile));
      setUser(null);
      toast.success('Connexion réussie');
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Échec de la connexion';
      toast.error(message);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [updateTokens]);

  /** Drop all session state without navigating or notifying (used by tab sync). */
  const clearSession = useCallback(() => {
    updateTokens(null);
    setUser(null);
    setMember(null);
    localStorage.removeItem(MEMBER_KEY);
    // Role is derived from the session, so nothing about the previous user may
    // survive into the next one on a shared browser.
    localStorage.removeItem('pulse-user-role');
  }, [updateTokens]);

  const logout = useCallback(() => {
    // Tell the server first, while the token is still valid: it bumps the
    // account's token version so every access and refresh token already issued
    // stops validating. Clearing localStorage alone left the refresh token
    // usable for its full lifetime by anyone who had captured it.
    //
    // Fire-and-forget on purpose — a failed call must never trap someone in a
    // session they asked to leave, and the local state is cleared either way.
    void apiPost('/auth/logout', {}).catch(() => undefined);

    clearSession();
    // Signals other open tabs to clear their session too.
    localStorage.setItem(LOGOUT_BROADCAST_KEY, String(Date.now()));
    toast.info('Déconnecté');
    window.location.href = '/#/login';
  }, [clearSession]);

  const refresh = useCallback(async (): Promise<boolean> => {
    const result = await refreshAccessToken();
    if (!result) {
      logout();
      return false;
    }
    setAccessTokenState(getAccessToken());
    return true;
  }, [logout]);

  // Restore the session on first paint.
  //
  // The access token is deliberately kept in memory only, so it does not survive
  // a reload; the longer-lived refresh token in localStorage is exchanged for a
  // fresh one instead. Previously nothing read the stored token back, so every
  // browser refresh silently signed the user out.
  useEffect(() => {
    let cancelled = false;

    const bootstrap = async () => {
      if (!localStorage.getItem(REFRESH_TOKEN_KEY)) {
        // No session to restore; drop any stale profile left behind.
        localStorage.removeItem(MEMBER_KEY);
        setMember(null);
        return;
      }
      const restored = await refreshAccessToken();
      if (cancelled) return;

      if (!restored) {
        clearSession();
        return;
      }
      setAccessTokenState(getAccessToken());

      // The refresh response says which kind of session this is, so the identity
      // is re-derived from the server rather than trusted from localStorage.
      if (restored.member_id) {
        const profile: MemberProfile = {
          member_id: restored.member_id,
          full_name: restored.full_name ?? '',
          role: restored.role ?? '',
          email: restored.email ?? '',
        };
        setMember(profile);
        localStorage.setItem(MEMBER_KEY, JSON.stringify(profile));
        setUser(null);
        return;
      }

      try {
        const profile = await apiGet<User>('/auth/me');
        if (cancelled) return;
        setUser(profile);
        setMember(null);
        localStorage.removeItem(MEMBER_KEY);
      } catch {
        if (cancelled) return;
        clearSession();
      }
    };

    bootstrap().finally(() => {
      if (!cancelled) setIsBootstrapping(false);
    });

    return () => {
      cancelled = true;
    };
  }, [clearSession]);

  // Let lib/api tear the session down when a refresh attempt finally fails.
  useEffect(() => {
    setSessionExpiredHandler(() => {
      clearSession();
      toast.error('Session expirée, veuillez vous reconnecter');
    });
    return () => setSessionExpiredHandler(null);
  }, [clearSession]);

  // Keep tabs in sync: signing out in one tab must not leave another tab holding
  // a live session, and a different user signing in must not inherit this state.
  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key === LOGOUT_BROADCAST_KEY) {
        clearSession();
      } else if (event.key === REFRESH_TOKEN_KEY && event.newValue === null) {
        clearSession();
      }
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, [clearSession]);

  const value: AuthContextType = {
    user,
    member,
    accessToken,
    isAuthenticated: !!accessToken,
    isLoading,
    isBootstrapping,
    role: user ? 'admin' : member ? roleToDashboardRole(member.role) : null,
    signIn,
    login,
    memberLogin,
    logout,
    refresh,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
