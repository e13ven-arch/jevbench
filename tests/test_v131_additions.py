"""v1.3.1: round-4 additions on the frozen v1.2 task set and v1.3.0 scorer."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/v1.2"
ART = json.loads((RESULTS / "jevbench-v1.2-results.json").read_text())
SYS = {row["key"]: row for row in ART["systems"]}
NEW = {
    "localjev-qwen3.5-4b", "metask-jev-4b", "jobe-qwen3.5-4b",
    "ninfer-qwen3.8-27b", "ninfer-qwen3.8-27b-t1.5", "ninfer-qwen3.8-flash-next",
    "hopper", "mirror", "jevone", "swanone", "jev-qwen3.5-9b-base-nvfp4",
    "simplejev-qwen3.5-0.8b", "raw-qwen3-0.6b", "raw-qwen3-1.7b",
    "raw-qwen3-8b", "raw-qwen3-4b-instruct-2507", "raw-phi-4-mini",
    "open-jev-json-canvas-joshuasp",
}


def test_v131_artifacts_are_paired_and_revisioned():
    assert ART["revision"] == "v1.3.1"
    assert "Added 18 independently reviewed rows" in next(
        entry["note"] for entry in ART["revision_log"] if entry["revision"] == "v1.3.1"
    )
    for key in NEW:
        assert (RESULTS / "additions" / f"{key}.json").is_file()
        task = json.loads((RESULTS / "additions" / f"{key}-per-task.json").read_text())
        assert task["partial"] is False
        assert task["public_tasks"]


def test_v131_rows_cover_all_534_decisions_and_are_costed():
    for key in NEW:
        row = SYS[key]
        assert row["ranked"] and not row["partial"], key
        assert row["hard"]["n_items"] == row["hard"]["n_attempted"] == 220, key
        source = json.loads((RESULTS / "additions" / f"{key}.json").read_text())
        assert sum(source["tier_blocks_v11"][tier]["n_attempted"] for tier in ("easy", "standard", "judge")) + row["hard"]["n_attempted"] == 534, key
        assert row["cost"]["usd_per_1000"] > 0 and row["axes"]["cost"] < 100, key
        assert row["licence"], key


def test_unreviewed_placeholders_and_private_work_are_absent():
    assert not any("reflex-0.8" in key or "typed-engine" in key for key in SYS)
    assert not any("private" in key and "djev" in key for key in SYS)
