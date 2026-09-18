from __future__ import annotations

from pathlib import Path

import chardet


TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".tsv", ".json", ".jsonl", ".xml", ".html", ".htm",
    ".log", ".yml", ".yaml", ".ini", ".cfg", ".conf", ".py", ".js", ".ts",
    ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rs", ".sql", ".sh", ".ps1",
    ".bat", ".env", ".properties", ".rtf", ".docx", ".pdf", ".xlsx", ".xls",
}

# Never decode these as text — binary noise creates fake MONEY/PERCENTAGE hits.
BINARY_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".ico",
    ".svg", ".heic", ".raw",
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a",
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv",
    ".zip", ".rar", ".7z", ".gz", ".tar", ".bz2",
    ".exe", ".dll", ".so", ".bin", ".dat", ".iso",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".psd", ".ai", ".sketch",
}


def _decode_bytes(data: bytes) -> str:
    if not data:
        return ""
    detected = chardet.detect(data) or {}
    encoding = detected.get("encoding") or "utf-8"
    try:
        return data.decode(encoding, errors="replace")
    except Exception:
        return data.decode("utf-8", errors="replace")


def _is_mostly_binary(data: bytes) -> bool:
    if not data:
        return True
    sample = data[:65536]
    if sample.count(b"\x00") > max(8, len(sample) // 100):
        return True
    # High share of non-text bytes (control chars except tab/newline/cr)
    non_text = 0
    for byte in sample:
        if byte in (9, 10, 13):
            continue
        if byte < 32 or byte == 127:
            non_text += 1
    return (non_text / max(len(sample), 1)) > 0.30


def _is_low_quality_text(text: str) -> bool:
    """Reject decoded garbage that still has printable noise."""
    if not text or not text.strip():
        return True
    sample = text[:8000]
    printable = sum(1 for ch in sample if ch.isprintable() or ch in "\n\r\t")
    if printable / max(len(sample), 1) < 0.85:
        return True
    # Too few letters relative to length → not a real document
    letters = sum(1 for ch in sample if ch.isalpha())
    if letters < 40 and len(sample.strip()) > 80:
        return True
    if letters / max(len(sample), 1) < 0.15:
        return True
    return False


def extract_text_from_file(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix in BINARY_EXTENSIONS:
            return ""

        if suffix in {".docx"}:
            from docx import Document

            document = Document(str(path))
            return "\n".join(p.text for p in document.paragraphs if p.text)

        if suffix in {".pdf"}:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            parts = []
            for page in reader.pages:
                parts.append(page.extract_text() or "")
            return "\n".join(parts)

        if suffix in {".xlsx", ".xls"}:
            import pandas as pd

            frames = pd.read_excel(path, sheet_name=None, dtype=str)
            chunks = []
            for name, frame in frames.items():
                chunks.append(f"[Sheet: {name}]")
                chunks.append(frame.fillna("").to_csv(index=False))
            return "\n".join(chunks)

        if suffix == ".csv":
            text = _decode_bytes(path.read_bytes())
            return "" if _is_low_quality_text(text) else text

        if suffix in {".html", ".htm", ".xml"}:
            from bs4 import BeautifulSoup

            raw = _decode_bytes(path.read_bytes())
            soup = BeautifulSoup(raw, "lxml")
            text = soup.get_text("\n", strip=True)
            return "" if _is_low_quality_text(text) else text

        data = path.read_bytes()
        if _is_mostly_binary(data):
            return ""

        text = _decode_bytes(data)
        if _is_low_quality_text(text):
            return ""
        return text
    except Exception:
        return ""
