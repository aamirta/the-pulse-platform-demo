import { useState, type ImgHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

/**
 * Visual Enhancement Layer — image with a subtle load reveal.
 *
 * A drop-in `<img>` replacement: identical attributes, plus an opacity/scale
 * settle once the image loads. The reveal classes are inert unless the
 * enhancement flag is on (`html[data-ve="on"]`), and `prefers-reduced-motion`
 * disables the transition — so with enhancements off this renders exactly
 * like a plain `<img>`.
 *
 * Fallback policy is intentionally left to the caller (same as before this
 * layer existed): render this only when you have a usable `src`, and keep the
 * existing placeholder/initials branch untouched.
 */
export function FadeInImage({
  className,
  loading = 'lazy',
  decoding = 'async',
  ...rest
}: ImgHTMLAttributes<HTMLImageElement>) {
  const [loaded, setLoaded] = useState(false);
  return (
    <img
      loading={loading}
      decoding={decoding}
      onLoad={() => setLoaded(true)}
      className={cn(className, 've-img', loaded && 've-img-loaded')}
      {...rest}
    />
  );
}
