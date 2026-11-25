"""Reciprocal Rank Fusion with a deterministic tie-break.

Server-side RRF scores tie often (equal ranks swapped between the two lists) and Qdrant orders
ties arbitrarily, which made hybrid recall@1 vary run to run on identical data. Fusing here lets
us break ties by the first ranking (dense) and then by id, so results are reproducible.
"""

from collections.abc import Sequence

RRF_K = 60


def rrf_fuse(rankings: Sequence[Sequence[str]], k: int = RRF_K) -> list[tuple[str, float]]:
    """Fuse ranked id lists. Returns (id, score) best first.

    Ties break by best position in the earlier rankings (dense first), then by id.
    """
    scores: dict[str, float] = {}
    positions: dict[str, list[int]] = {}
    for ranking in rankings:
        seen = set()
        for rank, item in enumerate(ranking, start=1):
            if item in seen:
                continue
            seen.add(item)
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    for item in scores:
        positions[item] = [
            next((r for r, x in enumerate(ranking, start=1) if x == item), len(ranking) + 1)
            for ranking in rankings
        ]
    return sorted(scores.items(), key=lambda pair: (-pair[1], positions[pair[0]], pair[0]))
