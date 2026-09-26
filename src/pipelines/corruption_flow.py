from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from pipelines.phase1 import dataframe_records
from retrieval.index import LocalEmbeddingIndex


METRIC_KEYS = (
    "retrieval_hit_rate",
    "mean_token_f1",
    "judge_accuracy",
    "mean_judge_score",
)


def _require_artifacts(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        formatted = "\n- ".join(missing)
        raise FileNotFoundError(
            "Required baseline artifacts are missing. Run "
            f"`python script/run_phase1.py` first:\n- {formatted}"
        )


def _load_clean_dataframe(path: Path) -> pd.DataFrame:
    df = pd.read_json(path)
    required_columns = {
        "paper_id",
        "title",
        "summary",
        "published",
        "age_days",
        "text_for_embedding",
    }
    missing_columns = sorted(required_columns.difference(df.columns))
    if missing_columns:
        raise ValueError(
            f"Clean artifact {path} is missing columns: {', '.join(missing_columns)}"
        )
    if df.empty:
        raise ValueError(f"Clean artifact {path} contains no records.")
    return df


def _write_dataframe(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    write_csv(df, csv_path)
    write_json(json_path, dataframe_records(df))


def _validate_metrics(metrics: Any, label: str) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        raise ValueError(f"{label} metrics must be a JSON object.")
    missing = [key for key in METRIC_KEYS if key not in metrics]
    if missing:
        raise ValueError(f"{label} metrics are missing: {', '.join(missing)}")
    return metrics


def _print_comparison(
    baseline: dict[str, Any],
    corrupted: dict[str, Any],
    repaired: dict[str, Any],
) -> None:
    print("\nBaseline vs Corrupted vs Repaired")
    print(f"{'Metric':<24} {'Baseline':>12} {'Corrupted':>12} {'Repaired':>12}")
    print("-" * 63)
    for key in METRIC_KEYS:
        print(
            f"{key:<24} "
            f"{float(baseline[key]):>12.4f} "
            f"{float(corrupted[key]):>12.4f} "
            f"{float(repaired[key]):>12.4f}"
        )


def main() -> None:
    """Run corruption, measurement, raw-based repair, and comparison."""
    settings = load_settings()
    paths = settings.paths
    _require_artifacts(
        [
            paths.clean_json,
            paths.raw_records_json,
            paths.eval_testset,
            paths.baseline_metrics,
        ]
    )

    baseline_metrics = _validate_metrics(read_json(paths.baseline_metrics), "Baseline")
    baseline_df = _load_clean_dataframe(paths.clean_json)

    corrupted_df = corrupt_clean_dataframe(baseline_df.copy(deep=True), paths.corruption_log)
    if corrupted_df.empty:
        raise RuntimeError("Corruption produced an empty dataframe; evaluation cannot continue.")
    _write_dataframe(corrupted_df, paths.corrupted_clean_csv, paths.corrupted_clean_json)

    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings,
        paths.corrupted_freshness_report,
    )
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings,
        paths.corrupted_embeddings_json,
    )
    corrupted_evaluation = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.corrupted_metrics,
        answers_output_path=paths.corrupted_answers,
    )
    corrupted_metrics = _validate_metrics(corrupted_evaluation.summary, "Corrupted")

    repair_run_date = now_utc()
    raw_records = load_raw_records(paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, repair_run_date)
    repeated_repair_df = build_clean_dataframe(raw_records, repair_run_date)
    if repaired_df.empty:
        raise RuntimeError("Repair from the raw snapshot produced no records.")
    if not repaired_df.equals(repeated_repair_df):
        raise RuntimeError("Repair is not idempotent for the same raw snapshot and run_date.")
    _write_dataframe(repaired_df, paths.repaired_clean_csv, paths.repaired_clean_json)

    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings,
        paths.repaired_freshness_report,
    )
    if not repaired_quality.get("success", False):
        raise RuntimeError(
            "Repaired data failed the quality gate. Inspect "
            f"{paths.repaired_quality_report}."
        )

    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings,
        paths.repaired_embeddings_json,
    )
    repaired_evaluation = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=paths.eval_testset,
        metrics_output_path=paths.repaired_metrics,
        answers_output_path=paths.repaired_answers,
    )
    repaired_metrics = _validate_metrics(repaired_evaluation.summary, "Repaired")

    generate_corruption_report(
        paths.comparison_report,
        baseline_metrics,
        corrupted_metrics,
        repaired_metrics,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    _print_comparison(baseline_metrics, corrupted_metrics, repaired_metrics)
    print(f"\nComparison report: {paths.comparison_report}")
