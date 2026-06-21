from typing import Sequence


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]],
    rrf_k: int = 60,
    max_results: int | None = None,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}

    for ranking in rankings:
        for rank_index, item_id in enumerate(ranking):
            rank = rank_index + 1
            scores[item_id] = scores.get(item_id, 0.0) + (1.0 / (rrf_k + rank))

    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if max_results is not None and max_results > 0:
        return fused[:max_results]
    return fused
