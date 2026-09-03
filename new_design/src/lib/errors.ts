/**
 * User-facing wording for failed requests.
 *
 * The review found "Impossible de charger les incubateurs - HTTP 500:" and a
 * bare "HTTP 500:" on Analytics. Status codes, response bodies and stack traces
 * never belong on screen, so pages render `describeError()` rather than
 * `error.message`, and the technical detail stays on the error object for the
 * console.
 */
import type { Language } from '@/data/translations';
import type { ApiErrorKind } from '@/lib/api';

/** Which surface failed, so the copy can name it ("the map", "the data"). */
export type ErrorSubject = 'data' | 'map' | 'page';

const COPY: Record<ErrorSubject, Record<Language, string>> = {
  data: {
    fr: 'Les données ne se chargent pas. Réessayez dans un instant.',
    en: 'The data could not be loaded. Please try again in a moment.',
  },
  map: {
    fr: 'La carte ne se charge pas. Réessayez dans un instant.',
    en: 'The map could not be loaded. Please try again in a moment.',
  },
  page: {
    fr: "Cette page n'existe pas ou a changé d'adresse.",
    en: 'This page does not exist or has moved.',
  },
};

const BY_KIND: Partial<Record<ApiErrorKind, Record<Language, string>>> = {
  auth: {
    fr: 'Vous devez être connecté pour voir ce contenu.',
    en: 'You need to be signed in to see this content.',
  },
  rateLimit: {
    fr: 'Trop de requêtes. Patientez quelques instants avant de réessayer.',
    en: 'Too many requests. Please wait a moment before trying again.',
  },
  network: {
    fr: 'Connexion indisponible. Vérifiez votre réseau et réessayez.',
    en: 'No connection. Check your network and try again.',
  },
};

/** Is this a message written for a person, or an internal sentinel/status line? */
function isPresentable(message: string): boolean {
  if (!message || message === 'REQUEST_FAILED') return false;
  // Anything that still smells like a status line, a stack or a payload.
  return !/^HTTP\b|\bstatus\b|^\s*[[{]|\bTraceback\b|\bError:\s/i.test(message);
}

/**
 * Turn any thrown value into a sentence worth showing.
 *
 * A 4xx carries a message the API wrote for the user ("Invalid credentials"),
 * so it is passed through. Everything else falls back to the wording for the
 * surface that failed.
 */
export function describeError(
  error: unknown,
  language: Language,
  subject: ErrorSubject = 'data',
): string {
  const kind = (error as { kind?: ApiErrorKind } | null)?.kind;
  if (kind && BY_KIND[kind]) {
    return BY_KIND[kind]![language];
  }
  if (kind !== 'server' && error instanceof Error && isPresentable(error.message)) {
    return error.message;
  }
  return COPY[subject][language];
}
