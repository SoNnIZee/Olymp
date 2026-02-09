from __future__ import annotations

import math


def expected_score(rating_a: int, rating_b: int) -> float:
    return 1.0 / (1.0 + math.pow(10.0, (rating_b - rating_a) / 400.0))


def update_elo(*, rating_a: int, rating_b: int, score_a: float, k: int) -> tuple[int, int]:
    """
    Returns (new_a, new_b).
    score_a: 1.0 win, 0.5 draw, 0.0 loss
    """
    exp_a = expected_score(rating_a, rating_b)
    exp_b = 1.0 - exp_a
    score_b = 1.0 - score_a

    new_a = rating_a + k * (score_a - exp_a)
    new_b = rating_b + k * (score_b - exp_b)

    return int(round(new_a)), int(round(new_b))

