"""Server-side thumbnail generation for harvested DSpace items.

Generates a JPEG thumbnail from the ORIGINAL bitstream of a publication when
DSpace itself didn't produce one (the common case for UNILAG records).

Supported source formats:
  - PDF                        → pdf2image (poppler-utils)
  - DOC / DOCX / PPT / PPTX
    ODT / ODP                  → LibreOffice headless → PDF → first page
  - JPG / JPEG / PNG / GIF
    BMP / WEBP / TIFF          → Pillow resize directly

Output:
  - JPEG, 800px on the long edge, ~80% quality
  - Saved relative to the configured UPLOADS_DIRECTORY as
    `thumb_<sha8>.jpg` so the same bitstream always produces the same file
    (idempotent on re-runs).

System dependencies (added to Dockerfile, not requirements.txt):
  - poppler-utils  (for pdf2image)
  - libreoffice    (for office docs, headless conversion)
"""
from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import requests
from PIL import Image

logger = logging.getLogger(__name__)


THUMBNAIL_MAX_PX = 800
THUMBNAIL_JPEG_QUALITY = 80

PDF_EXT = {".pdf"}
OFFICE_EXT = {".doc", ".docx", ".ppt", ".pptx", ".odt", ".odp", ".rtf"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}
SUPPORTED_EXT = PDF_EXT | OFFICE_EXT | IMAGE_EXT


def _detect_ext(filename: str, content_type: Optional[str] = None) -> str:
    """Best-effort extension detection from filename or Content-Type."""
    ext = Path(filename or "").suffix.lower()
    if ext:
        return ext
    if content_type:
        guess = mimetypes.guess_extension((content_type or "").split(";")[0].strip())
        if guess:
            return guess.lower()
    return ""


def _download(url: str, timeout: int = 60) -> tuple[bytes, Optional[str]]:
    response = requests.get(url, timeout=timeout, stream=True)
    response.raise_for_status()
    return response.content, response.headers.get("Content-Type")


def _resize_to_thumbnail(img: Image.Image, out_path: Path) -> None:
    # Convert palette/RGBA to RGB so JPEG encoding works
    if img.mode in ("P", "RGBA", "LA"):
        img = img.convert("RGB")
    img.thumbnail((THUMBNAIL_MAX_PX, THUMBNAIL_MAX_PX))
    img.save(out_path, "JPEG", quality=THUMBNAIL_JPEG_QUALITY, optimize=True)


def _pdf_first_page_to_jpeg(pdf_bytes: bytes, out_path: Path) -> bool:
    try:
        from pdf2image import convert_from_bytes
    except ImportError:
        logger.error("pdf2image not installed; cannot generate PDF thumbnail")
        return False
    try:
        images = convert_from_bytes(pdf_bytes, dpi=100, first_page=1, last_page=1)
    except Exception as exc:  # poppler errors, corrupt PDF, etc.
        logger.warning(f"pdf2image conversion failed: {exc}")
        return False
    if not images:
        return False
    _resize_to_thumbnail(images[0], out_path)
    return True


def _office_to_jpeg(src_bytes: bytes, src_ext: str, out_path: Path) -> bool:
    """Convert an office document → PDF (via LibreOffice) → thumbnail."""
    if not shutil.which("libreoffice") and not shutil.which("soffice"):
        logger.error("libreoffice not installed; cannot generate office-doc thumbnail")
        return False
    bin_name = "soffice" if shutil.which("soffice") else "libreoffice"
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = Path(tmpdir) / f"src{src_ext}"
        src_path.write_bytes(src_bytes)
        try:
            subprocess.run(
                [bin_name, "--headless", "--convert-to", "pdf", "--outdir", tmpdir, str(src_path)],
                check=True,
                timeout=120,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.SubprocessError as exc:
            logger.warning(f"libreoffice conversion failed for {src_ext}: {exc}")
            return False
        pdf_path = src_path.with_suffix(".pdf")
        if not pdf_path.exists():
            logger.warning(f"libreoffice produced no PDF for {src_ext}")
            return False
        return _pdf_first_page_to_jpeg(pdf_path.read_bytes(), out_path)


def _image_bytes_to_jpeg(src_bytes: bytes, out_path: Path) -> bool:
    try:
        with Image.open(tempfile.SpooledTemporaryFile()) as _:
            pass
    except Exception:
        pass
    try:
        import io
        img = Image.open(io.BytesIO(src_bytes))
        _resize_to_thumbnail(img, out_path)
        return True
    except Exception as exc:
        logger.warning(f"image resize failed: {exc}")
        return False


def generate_thumbnail_from_bytes(
    src_bytes: bytes,
    filename: str,
    uploads_dir: str,
    content_type: Optional[str] = None,
) -> Optional[str]:
    """Generate thumbnail from raw bytes, return the relative /uploads/... path or None.

    The output filename is deterministic from a sha1 of the source bytes, so
    calling this twice for the same bitstream is a no-op the second time.
    """
    ext = _detect_ext(filename, content_type)
    if ext not in SUPPORTED_EXT:
        logger.debug(f"unsupported ext for thumbnail: {ext or '<none>'} ({filename})")
        return None

    digest = hashlib.sha1(src_bytes).hexdigest()[:16]
    out_name = f"thumb_{digest}.jpg"
    out_path = Path(uploads_dir) / out_name

    if out_path.exists():
        return f"/uploads/{out_name}"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok = False
    if ext in PDF_EXT:
        ok = _pdf_first_page_to_jpeg(src_bytes, out_path)
    elif ext in OFFICE_EXT:
        ok = _office_to_jpeg(src_bytes, ext, out_path)
    elif ext in IMAGE_EXT:
        ok = _image_bytes_to_jpeg(src_bytes, out_path)

    if not ok:
        if out_path.exists():
            try:
                out_path.unlink()
            except OSError:
                pass
        return None
    return f"/uploads/{out_name}"


def generate_thumbnail_from_url(
    bitstream_url: str,
    filename: str,
    uploads_dir: str,
) -> Optional[str]:
    """Download a bitstream URL and generate a thumbnail. Returns /uploads/... path or None.

    All exceptions are caught and logged — never raises into the caller (harvester
    or backfill loop) since one bad item shouldn't kill a batch.
    """
    try:
        src_bytes, content_type = _download(bitstream_url)
    except Exception as exc:
        logger.warning(f"thumbnail: download failed {bitstream_url}: {exc}")
        return None
    try:
        return generate_thumbnail_from_bytes(src_bytes, filename, uploads_dir, content_type)
    except Exception as exc:
        logger.warning(f"thumbnail: generation failed for {filename}: {exc}")
        return None


def get_uploads_dir() -> str:
    """Resolve where to write thumbnails. Mirrors what publications.py uses."""
    return os.environ.get("UPLOADS_DIRECTORY", "/app/uploads")
