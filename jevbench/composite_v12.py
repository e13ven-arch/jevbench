"""JevBench v1.2 scoring additions: hard-tier-weighted Capability and the Calibration sub-score.

Speed, Cost and the Main Score formula are unchanged from v1.1.2 (jevbench.composite); v1.2 pools cost over
all 534 decisions and weights Capability towards the new hard tier. Pure functions of published aggregates.

Capability   100 * (0.10 easy + 0.20 standard + 0.20 judge + 0.50 hard)
Calibration  hard tier, distribution-returning systems only:
             mean of 100 * (1 - ECE / 0.5)  (clipped at 0)  and  100 * (1 - mean TVD to the exact gold distribution
             on the probability items); label-only systems have none (the 'Balanced + Calibration' preset scores a bare
             label as 100 % confidence).
"""
from jevbench.composite import log_score  # noqa: F401  (re-exported for callers)

TIER_WEIGHTS = {"easy": 0.10, "standard": 0.20, "judge": 0.20, "hard": 0.50}
PRESETS = {  # capability, speed, cost, calibration
    "Balanced 33:33:33 (Main Score)": (1 / 3, 1 / 3, 1 / 3, 0.0),
    "Emphasis on Accuracy 60:20:20": (0.6, 0.2, 0.2, 0.0),
    "Emphasis on Speed 20:60:20": (0.2, 0.6, 0.2, 0.0),
    "Emphasis on Cost 20:20:60": (0.2, 0.2, 0.6, 0.0),
    "Capability only": (1.0, 0.0, 0.0, 0.0),
    "Balanced + Calibration 25:25:25:25": (0.25, 0.25, 0.25, 0.25),
}


def capability(tiers):
    if any(tiers.get(t) is None for t in TIER_WEIGHTS):
        return None
    return 100 * sum(w * tiers[t] for t, w in TIER_WEIGHTS.items())


def tvd(p, q, labels):
    return 0.5 * sum(abs(p.get(l, 0.0) - q.get(l, 0.0)) for l in labels)


def calibration(ece, mean_tvd=None):
    if ece is None:
        return None
    a = max(0.0, 100 * (1 - ece / 0.5))
    return a if mean_tvd is None else (a + 100 * (1 - mean_tvd)) / 2


def preset_score(cap, spd, cst, cal, weights):
    a, b, c, d = weights
    vals = (cap, spd, cst, cal if d else 0.0)
    return None if any(v is None for v in vals) else a * cap + b * spd + c * cst + d * vals[3]
