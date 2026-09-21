import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = json.loads((ROOT / "results/v1.2/jevbench-v1.2-results.json").read_text())
SYS = {row["key"]: row for row in ART["systems"]}


def test_zefan_open_jev_rows_are_complete_distinct_and_provenanced():
    expected = {
        "open-jev-zefan-2b": ("Open-Jev 2B (Zefan Cai)", 41, 53.8),
        "open-jev-zefan-9b": ("Open-Jev 9B (Zefan Cai)", 39, 56.7),
    }
    for key, (display, rank, score) in expected.items():
        row = SYS[key]
        assert row["display"] == display
        assert row["rank"] == rank
        assert round(row["jevbench_score"], 1) == score
        assert row["ranked"] and not row["partial"]
        assert row["hard"]["n_items"] == row["hard"]["n_attempted"] == 220
        assert row["hard"]["coverage"] == 1
        assert row["cost"]["kind"] == "estimate"
        assert row["cost"]["usd_per_1000"] > 0
        assert row["axes"]["cost"] < 100
        assert "Apache-2.0" in row["licence"] and "MIT" in row["licence"]


def test_revision_uses_semantic_double_digit_version():
    assert ART["revision"] == "v1.2.15"


def test_zefan_rows_did_not_move_any_measured_score():
    ranked = sorted((r for r in ART["systems"] if r["ranked"]), key=lambda r: r["rank"])
    assert [r["rank"] for r in ranked] == list(range(1, len(ranked) + 1))
    assert SYS["winnow-12b"]["rank"] == 5 and round(SYS["winnow-12b"]["jevbench_score"], 1) == 72.5
