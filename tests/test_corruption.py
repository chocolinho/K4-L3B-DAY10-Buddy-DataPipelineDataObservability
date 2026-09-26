from datetime import UTC, datetime
import json

from core.config import load_settings
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records


def _clean_snapshot():
    settings = load_settings()
    records = load_raw_records(settings.paths.raw_records_json)
    return build_clean_dataframe(records, datetime(2026, 9, 26, tzinfo=UTC))


def test_corruption_suite_is_complete_reproducible_and_non_mutating(tmp_path):
    clean = _clean_snapshot()
    original = clean.copy(deep=True)
    first_log = tmp_path / "first.json"
    second_log = tmp_path / "second.json"

    first = corrupt_clean_dataframe(clean, first_log, seed=42)
    second = corrupt_clean_dataframe(clean, second_log, seed=42)
    log = json.loads(first_log.read_text(encoding="utf-8"))

    assert clean.equals(original)
    assert first.equals(second)
    assert log == json.loads(second_log.read_text(encoding="utf-8"))
    assert set(log) == {
        "metadata",
        "drop_latest_records",
        "blank_summary",
        "inject_noise",
        "truncate_title",
        "stale_date",
        "duplicate_rows",
    }
    assert all(log[name]["count"] > 0 for name in log if name != "metadata")
    assert log["metadata"] == {"initial_rows": 24, "random_seed": 42, "final_rows": 25}

    assert len(first) == 25
    assert int(first["paper_id"].duplicated().sum()) == 5
    assert int(first["title"].str.len().lt(8).sum()) >= 2
    assert int(first["summary"].eq("").sum()) >= 2
    assert first["summary_chars"].equals(first["summary"].str.len())
    assert all(
        f"Summary: {row.summary}" in row.text_for_embedding
        for row in first.itertuples()
    )

