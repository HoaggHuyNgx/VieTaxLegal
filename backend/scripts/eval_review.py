"""Review pending eval questions in the terminal (the human verification step).

From backend/: .venv/Scripts/python.exe scripts/eval_review.py [--limit 20]
Keys: a approve | r reject | e edit the question text, then approve | s skip | q save and quit.
Progress is saved after every decision, so you can stop any time.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.rag.corpus_manifest import load_manifest  # noqa: E402
from rag_eval.dataset import load_questions, save_questions  # noqa: E402
from rag_eval.review import apply_key, gold_text  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20, help="questions per session")
    args = parser.parse_args()
    questions = load_questions()
    docs = {doc.slug: doc for doc in load_manifest()}
    pending = [q for q in questions if q.status == "pending"][: args.limit]
    approved = sum(q.status == "approved" for q in questions)
    print(f"{len(pending)} pending in this session; {approved} approved so far")

    for number, question in enumerate(pending, start=1):
        print(f"\n===== {number}/{len(pending)}  {question.id}  [{question.field}/{question.type}]")
        print(f"Q: {question.question}")
        if question.type == "out_of_corpus":
            print("Expected: no citations + a 'cannot verify' answer. Check no doc answers it.")
        else:
            law = gold_text(question, docs)
            print(f"GOLD ANSWER: {question.gold_answer}\n--- law text ---\n{law}")
        key = input("[a]pprove [r]eject [e]dit [s]kip [q]uit > ").strip().lower()
        if key == "q":
            break
        note = input("reason: ") if key == "r" else ""
        new_text = input("new question: ") if key == "e" else ""
        if apply_key(question, key, note, new_text):
            save_questions(questions)
    save_questions(questions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
