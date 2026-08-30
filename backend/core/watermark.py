"""Server-side dynamic watermarking for Deal Room documents.

The watermark identifies the viewer, so a leaked copy points back at whoever was
given it. That guarantee only holds if the stamping happens here: the original
bytes are never sent to a client that is supposed to receive a watermarked
rendition, and the frontend has no part in applying it.

PDFs are stamped page by page with a rotated translucent overlay; raster images
get the same text composited over them. Formats we cannot stamp (Office
documents, CSV) are reported as unstampable so callers can refuse to release
them under a watermark-required permission rather than silently serving them
clean.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import UTC, datetime

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas

# Formats whose bytes we can actually alter. Anything else cannot carry a
# watermark and must not be released as if it did.
STAMPABLE_TYPES: frozenset[str] = frozenset(
    {"application/pdf", "image/png", "image/jpeg", "image/webp"}
)


class WatermarkError(Exception):
    """Raised when a document cannot be watermarked."""


@dataclass(frozen=True)
class WatermarkIdentity:
    """Viewer details stamped onto every page."""

    email: str
    member_id: int | None = None
    ip: str | None = None
    at: datetime | None = None

    def lines(self) -> list[str]:
        """Return the text lines to render, most identifying first."""
        moment = (self.at or datetime.now(UTC)).strftime("%Y-%m-%d %H:%M UTC")
        primary = self.email or "unidentified viewer"
        detail = f"{moment}"
        if self.member_id is not None:
            detail = f"ID {self.member_id} - {detail}"
        if self.ip:
            detail = f"{detail} - {self.ip}"
        return [primary, detail]


def can_stamp(content_type: str) -> bool:
    """Return True if a watermark can be burned into this content type."""
    return content_type in STAMPABLE_TYPES


def _overlay_pdf(width: float, height: float, identity: WatermarkIdentity) -> PdfReader:
    """Build a single-page transparent PDF bearing the watermark text."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(width, height))
    pdf.setFillColor(Color(0.42, 0.42, 0.45, alpha=0.16))

    lines = identity.lines()
    # A diagonal lattice: dense enough that cropping one instance out still
    # leaves several, but light enough to read the document underneath.
    step_x = max(width / 2, 260)
    step_y = max(height / 3, 200)
    pdf.saveState()
    pdf.translate(width / 2, height / 2)
    pdf.rotate(35)
    pdf.translate(-width / 2, -height / 2)

    y = -height
    while y < height * 2:
        x = -width
        while x < width * 2:
            pdf.setFont("Helvetica-Bold", 13)
            pdf.drawString(x, y, lines[0])
            pdf.setFont("Helvetica", 9)
            pdf.drawString(x, y - 13, lines[1])
            x += step_x
        y += step_y
    pdf.restoreState()

    # A solid footer band guarantees at least one crisp, legible attribution
    # even if the diagonal lattice lands badly on a dense page.
    pdf.setFillColor(Color(0.35, 0.35, 0.38, alpha=0.55))
    pdf.setFont("Helvetica", 7)
    pdf.drawString(18, 10, f"Confidential - shared with {lines[0]} - {lines[1]}")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return PdfReader(buffer)


def watermark_pdf(data: bytes, identity: WatermarkIdentity) -> bytes:
    """Return ``data`` with the viewer's identity stamped onto every page."""
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:  # pypdf raises a variety of parse errors
        raise WatermarkError("The document could not be read as a PDF") from exc

    if reader.is_encrypted:
        # An encrypted source cannot be merged with an overlay, and serving it
        # unstamped would break the watermark guarantee.
        raise WatermarkError("Encrypted PDFs cannot be watermarked")

    writer = PdfWriter()
    for page in reader.pages:
        box = page.mediabox
        overlay = _overlay_pdf(float(box.width), float(box.height), identity).pages[0]
        page.merge_page(overlay)
        writer.add_page(page)

    # Strip any metadata the uploader left behind rather than propagating it.
    writer.add_metadata({"/Producer": "The Pulse Deal Room", "/Title": "Confidential"})

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def watermark_image(data: bytes, identity: WatermarkIdentity, content_type: str) -> bytes:
    """Return an image with the viewer's identity composited over it."""
    try:
        source = Image.open(io.BytesIO(data))
        source.load()
    except Exception as exc:
        raise WatermarkError("The document could not be read as an image") from exc

    base = source.convert("RGBA")
    layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(layer)

    lines = identity.lines()
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", max(14, base.width // 45))
    except OSError:
        # Pillow's bundled bitmap font: always present, never the nicest.
        font = ImageFont.load_default()

    step = max(base.width // 2, 220)
    for y in range(0, base.height + step, max(base.height // 4, 120)):
        for x in range(-step, base.width + step, step):
            draw.text((x, y), lines[0], fill=(90, 90, 96, 60), font=font)
            draw.text((x, y + 18), lines[1], fill=(90, 90, 96, 55), font=font)

    draw.text((10, base.height - 18), f"Confidential - {lines[0]}", fill=(60, 60, 66, 150))

    merged = Image.alpha_composite(base, layer)
    out = io.BytesIO()
    if content_type == "image/jpeg":
        merged.convert("RGB").save(out, format="JPEG", quality=88)
    elif content_type == "image/webp":
        merged.save(out, format="WEBP", quality=88)
    else:
        merged.save(out, format="PNG")
    return out.getvalue()


def apply_watermark(data: bytes, content_type: str, identity: WatermarkIdentity) -> bytes:
    """Stamp ``data`` for ``identity``, raising if the format cannot carry a watermark."""
    if content_type == "application/pdf":
        return watermark_pdf(data, identity)
    if content_type in {"image/png", "image/jpeg", "image/webp"}:
        return watermark_image(data, identity, content_type)
    raise WatermarkError(
        f"Documents of type '{content_type}' cannot be watermarked; "
        "grant an unwatermarked permission or convert the file to PDF"
    )
