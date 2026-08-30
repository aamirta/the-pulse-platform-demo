/**
 * Visual Enhancement Layer — global OFF switch.
 *
 * Everything in `src/enhancements/` is ADDITIVE and gated by this flag.
 * When disabled, the platform renders exactly as before this layer existed:
 * every enhancement CSS rule is scoped under `html[data-ve="on"]`, so removing
 * the attribute makes the entire layer inert.
 *
 * Resolution order:
 *   1. URL override `?ve=off` / `?ve=on` (works before or inside the hash)
 *      — persisted to localStorage so the choice survives navigation.
 *   2. localStorage override from a previous URL override.
 *   3. Build-time default: `VITE_VISUAL_ENHANCEMENTS` env var (default: on).
 *      Set `VITE_VISUAL_ENHANCEMENTS=false` in `.env.local` to ship without
 *      the enhancement layer.
 */

const STORAGE_KEY = 'thepulse:ve-override';
const ATTR = 'data-ve';

function readUrlOverride(): boolean | null {
  if (typeof window === 'undefined') return null;
  const read = (raw: string): boolean | null => {
    const match = /(?:\?|&)ve=(on|off)\b/.exec(raw);
    if (!match) return null;
    return match[1] === 'on';
  };
  return read(window.location.search) ?? read(window.location.hash);
}

function computeInitial(): boolean {
  const fromUrl = readUrlOverride();
  if (fromUrl !== null) {
    try {
      localStorage.setItem(STORAGE_KEY, fromUrl ? 'on' : 'off');
    } catch {
      /* private mode — ignore */
    }
    return fromUrl;
  }
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'on') return true;
    if (stored === 'off') return false;
  } catch {
    /* ignore */
  }
  return import.meta.env.VITE_VISUAL_ENHANCEMENTS !== 'false';
}

let enabled = computeInitial();
const listeners = new Set<() => void>();

function applyAttribute() {
  if (typeof document === 'undefined') return;
  if (enabled) {
    document.documentElement.setAttribute(ATTR, 'on');
  } else {
    document.documentElement.removeAttribute(ATTR);
  }
}

function notify() {
  listeners.forEach((fn) => fn());
}

/** Called once from main.tsx before rendering. */
export function initEnhancements(): void {
  applyAttribute();
}

/** Current flag value (reactive-safe via subscribeEnhancements). */
export function enhancementsEnabled(): boolean {
  return enabled;
}

/**
 * Compile-time-friendly constant for non-React code. Reflects the value at
 * module load; runtime overrides applied later are visible via
 * `enhancementsEnabled()` / `useEnhancements()`.
 */
export const VISUAL_ENHANCEMENTS_ENABLED = enabled;

/** Toggle at runtime (used by tests and the ?ve= override). */
export function setEnhancements(value: boolean): void {
  enabled = value;
  try {
    localStorage.setItem(STORAGE_KEY, value ? 'on' : 'off');
  } catch {
    /* ignore */
  }
  applyAttribute();
  notify();
}

/** useSyncExternalStore-compatible subscription. */
export function subscribeEnhancements(fn: () => void): () => void {
  listeners.add(fn);
  return () => {
    listeners.delete(fn);
  };
}
