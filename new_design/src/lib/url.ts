/**
 * Normalise an external link coming from the API.
 *
 * The directory stores bare domains ("212founders.ma", "www.azurinnov.com").
 * A browser treats a scheme-less string as a *relative* URL, so opening one
 * navigated to `http://<app-host>/212founders.ma` — a broken in-app page rather
 * than the company's website.
 *
 * Returns null when there is nothing usable, so callers can hide the control
 * instead of rendering a dead link.
 */
export function externalUrl(value: string | null | undefined): string | null {
  if (!value) return null;

  const trimmed = value.trim();
  if (!trimmed || trimmed === '-') return null;

  // Already absolute (http, https, mailto, tel, …).
  if (/^[a-z][a-z0-9+.-]*:/i.test(trimmed)) {
    // Only allow schemes that are safe to open from a link.
    return /^(https?|mailto|tel):/i.test(trimmed) ? trimmed : null;
  }

  // Protocol-relative ("//example.com").
  if (trimmed.startsWith('//')) return `https:${trimmed}`;

  // Reject anything that cannot be a hostname (paths, spaces, single words).
  if (!/^[^\s/]+\.[^\s/]{2,}/.test(trimmed)) return null;

  return `https://${trimmed}`;
}

/**
 * Open an external link in a new tab.
 *
 * `noopener` prevents the opened page from reaching back through
 * `window.opener`; without it every outbound link is a reverse-tabnabbing risk.
 */
export function openExternal(value: string | null | undefined): void {
  const url = externalUrl(value);
  if (url) window.open(url, '_blank', 'noopener,noreferrer');
}
