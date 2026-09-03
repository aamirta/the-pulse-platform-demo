const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api/v1';

export const REFRESH_TOKEN_KEY = 'pulse-refresh-token';

let accessToken: string | null = null;

/** Called when the session cannot be recovered, so AuthContext can clear its state. */
let onSessionExpired: (() => void) | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function setSessionExpiredHandler(handler: (() => void) | null) {
  onSessionExpired = handler;
}

/** Coarse failure class, so the UI can choose wording without reading status codes. */
export type ApiErrorKind = 'server' | 'notFound' | 'auth' | 'validation' | 'rateLimit' | 'network';

export interface ApiError extends Error {
  status?: number;
  data?: unknown;
  kind?: ApiErrorKind;
}

function classify(status: number): ApiErrorKind {
  if (status >= 500) return 'server';
  if (status === 404) return 'notFound';
  if (status === 401 || status === 403) return 'auth';
  if (status === 429) return 'rateLimit';
  if (status === 422 || status === 400) return 'validation';
  return 'server';
}

/**
 * Message safe to put in front of a user.
 *
 * A server-authored `detail` is only trusted for 4xx, where it is written for
 * the person filling the form ("Invalid credentials"). For 5xx the body is a
 * crash description -- it used to fall through to `HTTP ${status}:
 * ${statusText}`, which is exactly the "Impossible de charger les incubateurs -
 * HTTP 500:" the review flagged. Callers render `describeError()` instead; this
 * sentinel is only the last-resort fallback.
 */
function errorMessage(status: number, data: unknown): string {
  if (status < 500 && data && typeof data === 'object' && 'detail' in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === 'string') return detail;
    // 422 validation errors arrive as a list of {loc, msg, type}.
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) =>
          item && typeof item === 'object' && 'msg' in item
            ? String((item as { msg: unknown }).msg)
            : null,
        )
        .filter(Boolean);
      if (messages.length) return messages.join(', ');
    }
  }
  return 'REQUEST_FAILED';
}

async function buildError(response: Response): Promise<ApiError> {
  let data: unknown;
  try {
    data = await response.json();
  } catch {
    data = null;
  }
  const error: ApiError = new Error(errorMessage(response.status, data));
  error.status = response.status;
  error.data = data;
  error.kind = classify(response.status);
  // The status line and body stay available for debugging, but only here.
  if (import.meta.env.DEV) {
    console.error(`[api] ${response.status} ${response.url}`, data);
  }
  return error;
}

/**
 * Exchange the stored refresh token for a new access token.
 *
 * Concurrent 401s share one in-flight request, so a page firing several requests
 * at once does not burn several refresh tokens or trip the auth rate limit.
 */
export interface RefreshResult {
  access_token: string;
  refresh_token: string;
  /** Present only for community-member sessions; absent for admin sessions. */
  member_id?: number | null;
  full_name?: string | null;
  role?: string | null;
  email?: string | null;
}

let refreshInFlight: Promise<RefreshResult | null> | null = null;

export async function refreshAccessToken(): Promise<RefreshResult | null> {
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) return null;
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (!response.ok) return null;
      const tokens = (await response.json()) as RefreshResult;
      setAccessToken(tokens.access_token);
      localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
      return tokens;
    } catch {
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw await buildError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

/**
 * Issue a request and, on a 401, transparently refresh the session once and retry.
 *
 * Only when the refresh itself fails is the session torn down. The previous
 * implementation dropped the refresh token on any 401 and hard-navigated to the
 * login page, so a merely expired access token ended the session outright.
 */
async function request<T>(path: string, init: RequestInit, isForm = false): Promise<T> {
  const send = (): Promise<Response> => {
    const headers: Record<string, string> = { ...((init.headers as Record<string, string>) ?? {}) };
    if (!isForm && init.body !== undefined) {
      headers['Content-Type'] = 'application/json';
    }
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`;
    }
    return fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  };

  let response = await send();

  if (response.status === 401 && localStorage.getItem(REFRESH_TOKEN_KEY)) {
    if (await refreshAccessToken()) {
      response = await send();
    }
  }

  if (response.status === 401) {
    setAccessToken(null);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    onSessionExpired?.();
  }

  return handleResponse<T>(response);
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'GET' });
}

export function apiPost<T>(path: string, body: BodyInit | object, isForm = false): Promise<T> {
  return request<T>(
    path,
    { method: 'POST', body: isForm ? (body as BodyInit) : JSON.stringify(body) },
    isForm,
  );
}

export function apiPatch<T>(path: string, body: object): Promise<T> {
  return request<T>(path, { method: 'PATCH', body: JSON.stringify(body) });
}

export function apiPut<T>(path: string, body: object): Promise<T> {
  return request<T>(path, { method: 'PUT', body: JSON.stringify(body) });
}

export function apiDelete<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' });
}

export { API_BASE_URL };
