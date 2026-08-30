import { useSyncExternalStore } from 'react';
import {
  enhancementsEnabled,
  subscribeEnhancements,
} from './flags';

/**
 * React binding for the visual-enhancement flag.
 *
 * Note: CSS-driven effects do not need this hook — every rule in
 * `enhancements.css` is scoped under `html[data-ve="on"]` and becomes inert
 * automatically when the flag is off. Use this hook only when JS needs to
 * branch (e.g. choosing whether to mount a wrapper component).
 */
export function useEnhancements(): boolean {
  return useSyncExternalStore(subscribeEnhancements, enhancementsEnabled);
}
