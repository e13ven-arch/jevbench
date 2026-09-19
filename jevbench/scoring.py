"""Distribution validation, argmax and ordinal expected-value scoring.

All scoring is deterministic and pure. Malformed distributions fail closed:
they are invalid and count as incorrect; callers must not invent calibration.
"""

from __future__ import annotations

import math

SUM_TOL = 1e-3


class InvalidDistribution(ValueError):
    pass


def validate_probs(probs: dict, labels: list, sum_tol: float = SUM_TOL) -> dict:
    """Validate a probability map against the exact label set.

    Keys must match labels exactly (no missing, no extra). Values must be
    finite floats in [0, 1] and sum to 1 within sum_tol. Returns a sanitized
    copy with plain float values.
    """
    if not isinstance(probs, dict):
        raise InvalidDistribution("probs is not a dict")
    want = set(labels)
    got = set(probs.keys())
    if got != want:
        raise InvalidDistribution(
            f"label keys mismatch: missing={sorted(want - got)} extra={sorted(got - want)}"
        )
    out = {}
    total = 0.0
    for k, v in probs.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise InvalidDistribution(f"prob[{k!r}] is not a number: {v!r}")
        f = float(v)
        if not math.isfinite(f):
            raise InvalidDistribution(f"prob[{k!r}] is not finite")
        if f < 0.0 or f > 1.0:
            raise InvalidDistribution(f"prob[{k!r}] out of [0,1]: {f}")
        out[str(k)] = f
        total += f
    if abs(total - 1.0) > sum_tol:
        raise InvalidDistribution(f"probs sum to {total}, tolerance {sum_tol}")
    return out


def argmax_label(probs: dict) -> str:
    """Deterministic argmax: ties broken by lexicographically smallest label."""
    best, best_p = None, -1.0
    for k in sorted(probs.keys()):
        if probs[k] > best_p:
            best, best_p = k, probs[k]
    return best


def expected_value(probs: dict) -> float:
    """Expected value over ordinal score levels keyed by string indices."""
    return sum(float(k) * v for k, v in probs.items())


def top_label_confidence(probs: dict) -> float:
    return max(probs.values()) if probs else 0.0


def score_task(probs: dict, task) -> dict:
    """Score one validated distribution against a canonical task.

    Returns dict with: valid, correct (None when expected is None),
    predicted (label or None), ordinal_ev (score family only).
    Invalid distributions: valid=False and correct=False (never skipped),
    but coverage/schema metrics remain separate from accuracy.
    """
    try:
        clean = validate_probs(probs, task.labels)
    except InvalidDistribution as e:
        return {"valid": False, "error": str(e), "correct": False, "predicted": None}

    if task.expected is None:
        correct = None
        pred = argmax_label(clean) if task.question["type"] != "score" else None
        out = {"valid": True, "correct": None, "predicted": pred}
        if task.question["type"] == "score":
            out["ordinal_ev"] = expected_value(clean)
        return out

    out = {"valid": True}
    if task.question["type"] == "score":
        ev = expected_value(clean)
        out["ordinal_ev"] = ev
        out["predicted"] = argmax_label(clean)
        out["correct"] = out["predicted"] == str(task.expected)
    else:
        pred = argmax_label(clean)
        out["predicted"] = pred
        out["correct"] = pred == task.expected
    return out
