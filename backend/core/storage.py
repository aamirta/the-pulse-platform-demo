"""Private file storage for confidential Deal Room documents.

``backend/main.py`` mounts ``static/`` with :class:`StaticFiles`, so every path
under it is world-readable to anyone who can guess the name. Deal Room documents
therefore live in a separate root that is *never* mounted, and are only ever
reached through an authorized API handler that streams the bytes itself.

Storage keys are derived server-side from a random token, so a filename supplied
by an uploader can never influence where the file lands or escape the root.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from backend.core.config import settings

# Documents accepted into a deal room. Kept deliberately narrow: these are the
# formats a data room actually needs, and each has a well-understood renderer.
ALLOWED_DOCUMENT_TYPES: dict[str, tuple[str, ...]] = {
    "application/pdf": (".pdf",),
    "image/png": (".png",),
    "image/jpeg": (".jpg", ".jpeg"),
    "image/webp": (".webp",),
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": (".pptx",),
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": (".xlsx",),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (".docx",),
    "text/csv": (".csv",),
}

MAX_DOCUMENT_BYTES: int = 50 * 1024 * 1024  # 50 MB

# Leading bytes that identify a format regardless of the declared content type.
_MAGIC_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"%PDF-", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"PK\x03\x04", "zip"),  # pptx / xlsx / docx are all zip containers
)

_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


class StorageError(Exception):
    """Raised when a file cannot be accepted or retrieved."""


@dataclass(frozen=True)
class StoredFile:
    """Result of persisting an upload."""

    storage_key: str
    byte_size: int
    sha256: str
    content_type: str
    original_filename: str


def storage_root() -> Path:
    """Return the private storage root, creating it if absent.

    Sits alongside ``static/`` rather than inside it, precisely so the
    :class:`StaticFiles` mount cannot reach it.
    """
    root = getattr(settings, "PRIVATE_STORAGE_ROOT", None)
    path = Path(root) if root else settings.UPLOAD_FOLDER.parent.parent / "private_storage"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(filename: str | None) -> str:
    """Return a display-safe filename with no path separators or control characters.

    The result is used only for the ``Content-Disposition`` header and audit
    records; it never participates in building a storage path.
    """
    if not filename:
        return "document"
    # Strip any directory component the client may have sent, including Windows
    # separators, which ``Path().name`` alone does not remove on POSIX.
    name = filename.replace("\\", "/").split("/")[-1]
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    name = _UNSAFE_FILENAME_CHARS.sub("_", name).strip("._-")
    if not name:
        return "document"
    return name[:180]


def detect_content_type(head: bytes, declared: str | None, filename: str | None) -> str:
    """Return the content type to trust, verified against the file's magic bytes.

    A browser-declared MIME type is attacker-controlled, so it is only honoured
    when the leading bytes agree with it.
    """
    signature: str | None = None
    for magic, kind in _MAGIC_SIGNATURES:
        if head.startswith(magic):
            signature = kind
            break

    declared = (declared or "").split(";")[0].strip().lower()
    extension = Path(sanitize_filename(filename)).suffix.lower()

    if signature == "zip":
        # All three OOXML types share the zip signature, so the extension picks
        # between them — but only among types that are actually allowed.
        for mime, extensions in ALLOWED_DOCUMENT_TYPES.items():
            if extension in extensions and mime.startswith("application/vnd.openxml"):
                return mime
        raise StorageError("Unsupported Office document type")

    if signature:
        if declared and declared != signature:
            raise StorageError(
                f"File content ({signature}) does not match its declared type ({declared})"
            )
        return signature

    # No recognised signature: text/csv has none, so accept it only when both
    # the declared type and the extension agree.
    if declared == "text/csv" and extension == ".csv":
        return "text/csv"

    raise StorageError("Unsupported or unrecognised file type")


def validate_upload(head: bytes, declared_type: str | None, filename: str | None) -> str:
    """Validate an upload's type and return the verified content type."""
    content_type = detect_content_type(head, declared_type, filename)
    if content_type not in ALLOWED_DOCUMENT_TYPES:
        raise StorageError(f"File type '{content_type}' is not permitted in a deal room")
    return content_type


def build_storage_key(deal_room_id: int, document_id: int) -> str:
    """Return a fresh, unguessable storage key scoped to a room and document.

    The random suffix means knowing a document id is not enough to name its file,
    and nothing in the key derives from user input.
    """
    return f"deal_rooms/{deal_room_id}/{document_id}/{secrets.token_urlsafe(24)}"


def _resolve(storage_key: str) -> Path:
    """Resolve a storage key to an absolute path, refusing anything outside the root.

    Defends against traversal even though keys are server-generated, because a
    corrupted or tampered database row must not be able to read ``/etc/passwd``.
    """
    root = storage_root().resolve()
    candidate = (root / storage_key).resolve()
    if candidate != root and root not in candidate.parents:
        raise StorageError("Refusing to access a path outside the storage root")
    return candidate


def save_bytes(storage_key: str, data: bytes) -> None:
    """Persist ``data`` at ``storage_key`` with owner-only permissions."""
    path = _resolve(storage_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(0o600)


def read_bytes(storage_key: str) -> bytes:
    """Return the stored bytes for ``storage_key``."""
    path = _resolve(storage_key)
    if not path.is_file():
        raise StorageError("Stored file is missing")
    return path.read_bytes()


def delete_object(storage_key: str) -> bool:
    """Delete a stored file. Returns True if a file was removed."""
    try:
        path = _resolve(storage_key)
    except StorageError:
        return False
    if path.is_file():
        path.unlink()
        return True
    return False


def sha256_hex(data: bytes) -> str:
    """Return the hex SHA-256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def store_upload(
    *,
    deal_room_id: int,
    document_id: int,
    data: bytes,
    declared_type: str | None,
    filename: str | None,
) -> StoredFile:
    """Validate and persist an uploaded document, returning its storage record."""
    if not data:
        raise StorageError("Uploaded file is empty")
    if len(data) > MAX_DOCUMENT_BYTES:
        raise StorageError(
            f"File exceeds the {MAX_DOCUMENT_BYTES // (1024 * 1024)} MB limit"
        )

    content_type = validate_upload(data[:512], declared_type, filename)
    storage_key = build_storage_key(deal_room_id, document_id)
    save_bytes(storage_key, data)

    return StoredFile(
        storage_key=storage_key,
        byte_size=len(data),
        sha256=sha256_hex(data),
        content_type=content_type,
        original_filename=sanitize_filename(filename),
    )
