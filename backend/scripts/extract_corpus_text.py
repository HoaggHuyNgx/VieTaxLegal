"""Extract every manifest document from corpus/raw/ into corpus/texts/<slug>.txt.

Usage (from backend/): .venv/Scripts/python.exe scripts/extract_corpus_text.py
"""

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.services.rag.corpus_manifest import CORPUS_DIR, load_manifest  # noqa: E402
from app.services.rag.text_extraction import extract_text, join_parts  # noqa: E402


def main() -> int:
    texts_dir = CORPUS_DIR / "texts"
    texts_dir.mkdir(exist_ok=True)
    failures = 0
    for doc in load_manifest():
        try:
            parts = [
                extract_text(CORPUS_DIR / name)
                for name in [doc.file, *(p["file"] for p in doc.extra_files)]
            ]
            text = parts[0] if len(parts) == 1 else join_parts(parts)
        except Exception as error:  # report every file, do not stop at the first bad one
            failures += 1
            print(f"FAIL {doc.slug}: {error}")
            continue
        (texts_dir / f"{doc.slug}.txt").write_text(text, encoding="utf-8", newline="\n")
        print(f"ok   {doc.slug}: {len(text):,} chars")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
