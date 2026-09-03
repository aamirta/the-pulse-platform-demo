/**
 * The Pulse wordmark.
 *
 * The asset is the logo supplied in the supervisor's Word document and is the
 * only Pulse logo the app uses -- the header previously drew its own lockup
 * from a text span plus a hand-rolled SVG pulse line, which was a different
 * mark. It ships in two colourways because the wordmark is solid black: the
 * light file is swapped in on dark surfaces so the mark never disappears.
 *
 * Width is left to flow from the height so the 5.15:1 ratio is never stretched.
 */
interface BrandLogoProps {
  /** Rendered height. Width follows the aspect ratio. */
  className?: string;
  /** Accessible name; pass "" where an adjacent label already names the link. */
  alt?: string;
}

export default function BrandLogo({ className = 'h-7', alt = 'The Pulse' }: BrandLogoProps) {
  return (
    <>
      <img
        src="/brand/the-pulse-logo.png"
        alt={alt}
        width={778}
        height={151}
        className={`${className} w-auto object-contain dark:hidden`}
      />
      <img
        src="/brand/the-pulse-logo-light.png"
        alt=""
        aria-hidden="true"
        width={778}
        height={151}
        className={`${className} w-auto object-contain hidden dark:block`}
      />
    </>
  );
}
