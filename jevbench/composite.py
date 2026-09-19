"""JevBench v1.1 scoring: three sub-benchmarks and the Main Score.

Everything here is a pure function of published aggregates, so anyone can
recompute a system's Main Score from results/v1.1/jevbench-v1.1-results.json.

Capability  mean of the easy, standard and judge tier accuracies (1/3 each), x 100
Speed       latency t -> 100 * log10(10 s / t) / 2, clipped: 0.1 s = 100, 1 s = 50, 10 s = 0;
            Speed = mean of the p50 and p95 scores
Cost        $ per 1,000 decisions c -> 100 * log10($10 / c) / 3, clipped:
            $0.01 = 100, $0.10 = 67, $1 = 33, $10 = 0
Main Score  0.6 * Capability + 0.2 * Speed + 0.2 * Cost

Calibration (Brier, ECE) is reported beside these, not folded in: label-only
systems have no distribution, and a penalty for that would be our invention.
"""
import math

WEIGHTS = (0.6, 0.2, 0.2)
SENSITIVITY = {
    "60/20/20 (headline)": (0.6, 0.2, 0.2, "arith"),
    "capability only": (1.0, 0.0, 0.0, "arith"),
    "80/10/10": (0.8, 0.1, 0.1, "arith"),
    "50/25/25": (0.5, 0.25, 0.25, "arith"),
    "equal thirds": (1 / 3, 1 / 3, 1 / 3, "arith"),
    "60/20/20 geometric": (0.6, 0.2, 0.2, "geo"),
}


def log_score(x, best, worst):
    """Map x onto 0..100 on a log scale: best -> 100, worst -> 0, clipped."""
    if x is None:
        return None
    if x <= 0:
        return 100.0
    v = 100 * (math.log10(worst) - math.log10(x)) / (math.log10(worst) - math.log10(best))
    return max(0.0, min(100.0, v))


def capability(tier_accuracies):
    accs = list(tier_accuracies)
    if not accs or any(a is None for a in accs):
        return None
    return 100 * sum(accs) / len(accs)


def speed(p50_s, p95_s):
    a, b = log_score(p50_s, 0.1, 10), log_score(p95_s, 0.1, 10)
    return None if None in (a, b) else (a + b) / 2


def cost(usd_per_1000):
    return log_score(usd_per_1000, 0.01, 10)


def main_score(cap, spd, cst, weights=(0.6, 0.2, 0.2, "arith")):
    a, b, d = weights[:3]
    kind = weights[3] if len(weights) > 3 else "arith"
    if None in (cap, spd, cst):
        return None
    if kind == "geo":
        return (max(cap, 1e-9) ** a) * (max(spd, 1e-9) ** b) * (max(cst, 1e-9) ** d)
    return a * cap + b * spd + d * cst
