"""Typed access to backend/corpus/manifest.json (the human-curated source of truth).

``status`` and the effective dates are set by a person after checking the official source and are
never inferred here. ``None`` means "not verified yet".
"""

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parents[3] / "corpus"
VALID_STATUSES = frozenset({"in_force", "expired", "superseded"})


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class CorpusDoc:
    slug: str
    number: str
    title: str
    doc_type: str
    field: str
    file: str
    sha256: str
    source_url: str
    is_amending: bool = False
    status: str | None = None
    issued_on: str | None = None
    effective_from: str | None = None
    effective_to: str | None = None
    superseded_by: str | None = None
    # Dieu labels ("5", "5a") dropped at ingest (repealed/superseded but still in the base text).
    excluded_articles: tuple[str, ...] = ()
    # Dieu numbers allowed to be missing from the parsed sequence (explained gaps).
    known_gaps: tuple[int, ...] = ()
    # True when the downloaded text is only part of the document ("Xem tiep Cong bao ..."),
    # False when a person confirmed it is complete, None when nobody has checked.
    # Further source files appended after `file` for documents published in several parts.
    extra_files: tuple[dict, ...] = ()
    truncated: bool | None = None
    # False keeps the file in the manifest but out of the index (e.g. unusable OCR text).
    ingest: bool = True
    notes: str = field(default="", compare=False)

    @property
    def text_path(self) -> Path:
        return CORPUS_DIR / "texts" / f"{self.slug}.txt"


def _build(entry: dict) -> CorpusDoc:
    status = entry.get("status")
    if status is not None and status not in VALID_STATUSES:
        raise ManifestError(f"{entry.get('slug')}: invalid status {status!r}")
    try:
        return CorpusDoc(
            slug=entry["slug"],
            number=entry["number"],
            title=entry["title"],
            doc_type=entry["doc_type"],
            field=entry["field"],
            file=entry["file"],
            sha256=entry["sha256"],
            source_url=entry["source_url"],
            is_amending=bool(entry.get("is_amending", False)),
            status=status,
            issued_on=entry.get("issued_on"),
            effective_from=entry.get("effective_from"),
            effective_to=entry.get("effective_to"),
            superseded_by=entry.get("superseded_by"),
            excluded_articles=tuple(str(label) for label in entry.get("excluded_articles", ())),
            known_gaps=tuple(entry.get("known_gaps", ())),
            extra_files=tuple(entry.get("extra_files", ())),
            truncated=entry.get("truncated"),
            ingest=bool(entry.get("ingest", True)),
            notes=entry.get("notes", ""),
        )
    except KeyError as missing:
        raise ManifestError(f"{entry.get('slug', '?')}: missing field {missing}") from None


def load_manifest(path: Path | None = None) -> list[CorpusDoc]:
    manifest_path = path or CORPUS_DIR / "manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    docs = [_build(entry) for entry in data["documents"]]
    slugs = [doc.slug for doc in docs]
    if len(slugs) != len(set(slugs)):
        raise ManifestError("Duplicate slug in manifest.")
    return docs


def verify_raw_file(doc: CorpusDoc) -> bool:
    """True when the raw file on disk still matches the sha256 recorded at download time."""
    parts = [(doc.file, doc.sha256), *((p["file"], p["sha256"]) for p in doc.extra_files)]
    for name, expected in parts:
        path = CORPUS_DIR / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            return False
    return True
