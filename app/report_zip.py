"""Validate and read Playwright-style HTML report ZIPs (multi-file reports)."""

from __future__ import annotations

import io
import zipfile
from typing import Optional

# GitHub artifact zips are often a few MB; keep headroom for large suites.
MAX_ZIP_BYTES = 40 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 120 * 1024 * 1024


class ReportZipError(ValueError):
    pass


def _normalize_member(name: str) -> Optional[str]:
    n = name.replace('\\', '/').strip()
    if not n or n.endswith('/'):
        return None
    if n.startswith('/') or '..' in n.split('/'):
        return None
    return n


def find_index_html_path(zf: zipfile.ZipFile) -> str:
    members: list[str] = []
    for raw in zf.namelist():
        m = _normalize_member(raw)
        if m is None:
            continue
        members.append(m)
    candidates = [m for m in members if m.lower().endswith('index.html')]
    if not candidates:
        raise ReportZipError('ZIP must contain an index.html file (Playwright HTML report).')
    # Prefer shallow paths (e.g. index.html or playwright-report/index.html).
    candidates.sort(key=lambda p: (p.count('/'), len(p), p))
    return candidates[0]


def validate_report_zip_bytes(data: bytes) -> str:
    if len(data) > MAX_ZIP_BYTES:
        raise ReportZipError(f'ZIP file exceeds {MAX_ZIP_BYTES // (1024 * 1024)} MB limit.')
    if len(data) < 22:  # smallest zip
        raise ReportZipError('Invalid or empty ZIP file.')
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        raise ReportZipError('Invalid ZIP file.') from e
    try:
        total_uncompressed = sum(info.file_size for info in zf.infolist())
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise ReportZipError('ZIP uncompressed size too large.')
        return find_index_html_path(zf)
    finally:
        zf.close()


def read_member(data: bytes, member_path: str) -> tuple[bytes, str]:
    """Return file bytes and a suggested MIME type (best-effort)."""
    import mimetypes

    want = member_path.replace('\\', '/').lstrip('/')
    if not want or '..' in want.split('/'):
        raise ReportZipError('Invalid path')

    zf = zipfile.ZipFile(io.BytesIO(data))
    try:
        # Match exact normalized archive member.
        names = {_normalize_member(n): n for n in zf.namelist() if _normalize_member(n)}
        if want not in names:
            raise ReportZipError('File not found in report archive.')
        raw_name = names[want]
        with zf.open(raw_name) as f:
            body = f.read()
        mime, _ = mimetypes.guess_type(want)
        if mime is None:
            if want.endswith('.js'):
                mime = 'text/javascript; charset=utf-8'
            elif want.endswith('.html'):
                mime = 'text/html; charset=utf-8'
            elif want.endswith('.css'):
                mime = 'text/css; charset=utf-8'
            else:
                mime = 'application/octet-stream'
        return body, mime
    finally:
        zf.close()
