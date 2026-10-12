"""Retrieval and citation metrics. Pure functions; article level so chunk sets are comparable."""

import math
from collections.abc import Iterable, Sequence

ArticleKey = tuple[str, int]  # (doc_slug, article number)


def first_hit_rank(retrieved: Sequence[Iterable[ArticleKey]], gold: set[ArticleKey]) -> int | None:
    """1-based rank of the first retrieved chunk touching any gold article, else None.

    Each retrieved item is the set of articles one chunk covers (fixed chunks may cover several).
    """
    for rank, covered in enumerate(retrieved, start=1):
        if gold & set(covered):
            return rank
    return None


def recall_at_k(ranks: Sequence[int | None], k: int) -> float:
    return sum(1 for r in ranks if r is not None and r <= k) / len(ranks) if ranks else 0.0


def mrr(ranks: Sequence[int | None]) -> float:
    return sum(1 / r for r in ranks if r) / len(ranks) if ranks else 0.0


def citation_precision_recall(
    cited: set[ArticleKey], gold: set[ArticleKey]
) -> tuple[float | None, float | None]:
    """Precision: share of cited articles that are gold. Recall: share of gold articles cited.

    None when undefined (nothing cited / no gold) so averages skip it instead of counting zero.
    """
    hits = len(cited & gold)
    precision = hits / len(cited) if cited else None
    recall = hits / len(gold) if gold else None
    return precision, recall


def mean(values: Iterable[float | None]) -> float | None:
    kept = [v for v in values if v is not None]
    return sum(kept) / len(kept) if kept else None


def percentile(values: Sequence[float], pct: float) -> float | None:
    """Nearest-rank percentile (pct in 0-100)."""
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(pct / 100 * len(ordered)) - 1)
    return ordered[index]


def latency_summary(values_ms: Sequence[float]) -> dict[str, float | None]:
    return {"p50": percentile(values_ms, 50), "p95": percentile(values_ms, 95)}
