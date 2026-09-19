from jevbench.composite_v12 import PRESETS, TIER_WEIGHTS, calibration, capability, preset_score, tvd


def test_tier_weights_sum_to_one():
    assert abs(sum(TIER_WEIGHTS.values()) - 1) < 1e-12
    for w in PRESETS.values():
        assert abs(sum(w) - 1) < 1e-9


def test_capability_weights_hard_half():
    assert capability({"easy": 1, "standard": 1, "judge": 1, "hard": 0}) == 50.0
    assert capability({"easy": 1, "standard": 1, "judge": 1, "hard": None}) is None


def test_calibration():
    assert calibration(0.0) == 100.0
    assert calibration(0.5) == 0.0
    assert calibration(0.9) == 0.0
    assert calibration(0.1, 0.2) == (80.0 + 80.0) / 2
    assert calibration(None) is None


def test_tvd_and_presets():
    assert tvd({"a": 1.0}, {"a": 0.6, "b": 0.4}, ["a", "b"]) == 0.4
    main = PRESETS["Balanced 33:33:33 (Main Score)"]
    assert abs(preset_score(90, 60, 30, None, main) - 60) < 1e-9
    assert preset_score(90, 60, 30, None, PRESETS["Balanced + Calibration 25:25:25:25"]) is None
