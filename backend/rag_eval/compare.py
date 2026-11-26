"""Paired comparison of two retrieval runs: is B really better than A on the same questions?

With ~44 test questions a 0.05 gap in Hit@1 is two questions, so a difference is only reported as
real when the paired bootstrap interval excludes zero (and, for Hit@k, McNemar's exact test agrees).
Pure functions; `scripts/eval_compare.py` does the file I/O.
"""

import math
import random

HIT_KS = (1, 5)
BOOTSTRAP_SAMPLES = 10_000


def mcnemar_exact(only_a: int, only_b: int) -> float:
    """Two-sided exact McNemar p-value from the discordant pairs (binomial, p = 0.5)."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(only_a, only_b) + 1)) / 2**n
    return min(1.0, 2 * tail)


def paired_bootstrap(
    a: list[float], b: list[float], samples: int = BOOTSTRAP_SAMPLES, seed: int = 0
) -> tuple[float, float, float]:
    """Mean of b - a and its 95% percentile interval, resampling questions with replacement."""
    diffs = [y - x for x, y in zip(a, b, strict=True)]
    if not diffs:
        return 0.0, 0.0, 0.0
    rng = random.Random(seed)  # fixed seed: the same report on every run
    means = sorted(sum(rng.choices(diffs, k=len(diffs))) / len(diffs) for _ in range(samples))
    return sum(diffs) / len(diffs), means[int(0.025 * samples)], means[int(0.975 * samples) - 1]


def _ranks(result: dict) -> dict[str, int | None]:
    """First-hit rank per in-corpus question (out-of-corpus rows carry no rank)."""
    return {row["id"]: row["rank"] for row in result["questions"] if "rank" in row}


def _per_question(ranks: list[int | None]) -> dict[str, list[float]]:
    values = {f"hit@{k}": [float(r is not None and r <= k) for r in ranks] for k in HIT_KS}
    values["mrr"] = [1 / r if r else 0.0 for r in ranks]
    return values


def _condition_warnings(a: dict, b: dict) -> list[str]:
    """Differences that can explain a gap by themselves. A warning, not an error: comparing chunk
    sets, for example, is a legitimate experiment."""
    warnings = []
    for section, keys in (
        ("config", ("chunk_set", "top_k", "depth")),
        ("meta", ("corpus_manifest_sha", "corpus_texts_sha")),
    ):
        for key in keys:
            side_a = a["meta"]["config"] if section == "config" else a["meta"]
            side_b = b["meta"]["config"] if section == "config" else b["meta"]
            if side_a.get(key) != side_b.get(key):
                warnings.append(f"Different {key}: {side_a.get(key)} vs {side_b.get(key)}.")
    gold_a = {row["id"]: row.get("gold") for row in a["questions"]}
    moved = [
        r["id"] for r in b["questions"] if r["id"] in gold_a and gold_a[r["id"]] != r.get("gold")
    ]
    if moved:
        warnings.append(
            f"Different gold answers for {len(moved)} question(s): {', '.join(moved[:5])}."
        )
    return warnings


def compare_runs(a: dict, b: dict, seed: int = 0) -> dict:
    ranks_a, ranks_b = _ranks(a), _ranks(b)
    shared = sorted(ranks_a.keys() & ranks_b.keys())
    warnings = []
    split_a = a["meta"]["config"].get("split")
    split_b = b["meta"]["config"].get("split")
    if split_a != split_b:
        warnings.append(f"Different splits ({split_a} vs {split_b}): not a paired comparison.")
    warnings += _condition_warnings(a, b)
    only_a, only_b = len(ranks_a.keys() - ranks_b.keys()), len(ranks_b.keys() - ranks_a.keys())
    if only_a or only_b:
        warnings.append(f"Question sets differ: {only_a} only in A, {only_b} only in B (ignored).")

    values_a = _per_question([ranks_a[q] for q in shared])
    values_b = _per_question([ranks_b[q] for q in shared])
    metrics = {}
    for name in values_a:
        xs, ys = values_a[name], values_b[name]
        diff, low, high = paired_bootstrap(xs, ys, seed=seed)
        p_value = None
        if name.startswith("hit@"):
            p_value = mcnemar_exact(
                sum(x > y for x, y in zip(xs, ys)), sum(y > x for x, y in zip(xs, ys))
            )
        metrics[name] = {
            "a": sum(xs) / len(xs) if xs else 0.0,
            "b": sum(ys) / len(ys) if ys else 0.0,
            "diff": diff,
            "ci": (low, high),
            "p": p_value,
        }

    text = {row["id"]: row.get("question", "") for row in b["questions"]}
    changes = []
    for qid in shared:
        rank_a, rank_b = ranks_a[qid], ranks_b[qid]
        if rank_a == rank_b:
            continue
        better = "b" if (rank_b or math.inf) < (rank_a or math.inf) else "a"
        changes.append(
            {"id": qid, "question": text.get(qid, ""), "rank_a": rank_a, "rank_b": rank_b,
             "better": better}
        )  # fmt: skip
    changes.sort(key=lambda c: (c["better"] != "b", c["id"]))
    return {
        "n": len(shared),
        "only_a": only_a,
        "only_b": only_b,
        "warnings": warnings,
        "metrics": metrics,
        "changes": changes,
    }


def _rank(value: int | None) -> str:
    return "miss" if value is None else str(value)


def to_markdown(result: dict, name_a: str, name_b: str) -> str:
    lines = [f"## {name_b} vs {name_a} ({result['n']} paired in-corpus questions)", ""]
    lines += [f"> Warning: {warning}" for warning in result["warnings"]]
    if result["warnings"]:
        lines.append("")
    lines += [
        "| metric | A | B | B - A | 95% CI | McNemar p | real gap? |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, m in result["metrics"].items():
        low, high = m["ci"]
        if not (low > 0 or high < 0):
            real = "no (CI includes 0)"
        elif m["p"] is not None and m["p"] >= 0.05:
            real = "no (McNemar p >= 0.05)"
        else:
            real = "yes"
        p_value = "-" if m["p"] is None else "<0.001" if m["p"] < 0.001 else f"{m['p']:.3f}"
        lines.append(
            f"| {name} | {m['a']:.3f} | {m['b']:.3f} | {m['diff']:+.3f} | "
            f"[{low:+.3f}, {high:+.3f}] | {p_value} | {real} |"
        )
    lines += ["", f"### Questions whose first-hit rank changed ({len(result['changes'])})", ""]
    lines += ["| id | better | rank A | rank B | question |", "|---|---|---|---|---|"]
    for c in result["changes"]:
        question = c["question"][:80] + ("..." if len(c["question"]) > 80 else "")
        lines.append(
            f"| {c['id']} | {c['better'].upper()} | {_rank(c['rank_a'])} | "
            f"{_rank(c['rank_b'])} | {question} |"
        )
    return "\n".join(lines) + "\n"
