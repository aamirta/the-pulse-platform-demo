import { useState } from 'react';

interface ImageWithFallbackProps {
  src: string | null | undefined;
  alt: string;
  className?: string;
  /** Text the placeholder derives its initial from; defaults to `alt`. */
  fallbackText?: string;
}

/**
 * An image that degrades to a typographic placeholder.
 *
 * The API returns `""` for missing logos and avatars. Passing that straight to
 * `<img src>` makes the browser re-request the current page (and logs a console
 * error), and a broken URL leaves a torn icon in the card. This renders the
 * placeholder instead, and lazy-loads real images so off-screen cards do not
 * compete with the initial paint.
 */
export function ImageWithFallback({
  src,
  alt,
  className = '',
  fallbackText,
}: ImageWithFallbackProps) {
  const [failed, setFailed] = useState(false);
  // Enhancement layer: reveal animation state. The `ve-img` classes are inert
  // unless the enhancement flag is on (html[data-ve="on"]), so disabling the
  // layer restores the exact original rendering.
  const [loaded, setLoaded] = useState(false);
  const usable = typeof src === 'string' && src.trim().length > 0 && !failed;

  if (!usable) {
    const initial = (fallbackText || alt || '?').trim().charAt(0).toUpperCase() || '?';
    return (
      <div
        role="img"
        aria-label={alt}
        className={`flex items-center justify-center bg-secondary/60 text-muted-foreground font-bold select-none ${className}`}
      >
        {initial}
      </div>
    );
  }

  return (
    <img
      src={src as string}
      alt={alt}
      loading="lazy"
      decoding="async"
      onError={() => setFailed(true)}
      onLoad={() => setLoaded(true)}
      className={`${className} ve-img ${loaded ? 've-img-loaded' : ''}`}
    />
  );
}
