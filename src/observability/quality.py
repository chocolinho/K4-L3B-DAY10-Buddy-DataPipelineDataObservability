from __future__ import annotations

from pathlib import Path
from typing import Any

import great_expectations as gx
import pandas as pd

from core.config import Settings
from core.utils import safe_slug, write_json


def _freshness(df: pd.DataFrame, settings: Settings) -> dict[str, Any]:
    total = len(df)
    ages = pd.to_numeric(df["age_days"], errors="coerce") if "age_days" in df else pd.Series(dtype=float)
    stale_rows = int(ages.gt(settings.freshness_threshold_days).sum())
    invalid_rows = total - int(ages.notna().sum())
    stale_ratio = stale_rows / total if total else 0.0
    dates = pd.to_datetime(df["published"], errors="coerce", utc=True) if "published" in df else pd.Series(dtype="datetime64[ns, UTC]")
    valid_dates = dates.dropna()
    return {
        "latest_published": valid_dates.max().date().isoformat() if not valid_dates.empty else None,
        "oldest_published": valid_dates.min().date().isoformat() if not valid_dates.empty else None,
        "stale_rows": stale_rows,
        "invalid_age_rows": invalid_rows,
        "total_rows": total,
        "stale_ratio": stale_ratio,
        "threshold_days": settings.freshness_threshold_days,
        "max_stale_ratio": 0.25,
        "is_fresh": total > 0 and invalid_rows == 0 and len(valid_dates) == total and stale_ratio <= 0.25,
    }


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path) -> dict[str, Any]:
    """Measure publication age and save the freshness SLA result."""
    report = _freshness(df, settings)
    write_json(Path(report_path), report)
    return report


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Validate clean papers with GX 1.x and include the freshness SLA."""
    required = {"paper_id", "title", "summary", "published", "age_days"}
    missing = sorted(required - set(df.columns))
    freshness = _freshness(df, settings)
    checks: list[dict[str, Any]] = []

    if not missing:
        context = gx.get_context(mode="ephemeral")
        source = context.data_sources.add_pandas(name="papers_source")
        asset = source.add_dataframe_asset(name="papers_asset")
        batch_def = asset.add_batch_definition_whole_dataframe("papers_batch")
        batch = batch_def.get_batch(batch_parameters={"dataframe": df})
        expectations = [
            gx.expectations.ExpectTableRowCountToBeBetween(min_value=24, max_value=24),
            gx.expectations.ExpectColumnValuesToNotBeNull(column="paper_id"),
            gx.expectations.ExpectColumnValuesToBeUnique(column="paper_id"),
            gx.expectations.ExpectColumnValuesToNotBeNull(column="title"),
            gx.expectations.ExpectColumnValueLengthsToBeBetween(column="title", min_value=8),
            gx.expectations.ExpectColumnValuesToNotBeNull(column="summary"),
            gx.expectations.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=50),
        ]
        for expectation in expectations:
            result = batch.validate(expectation)
            checks.append({
                "expectation": type(expectation).__name__,
                "column": getattr(expectation, "column", None),
                "success": bool(result.success),
                "result": result.result,
            })

    report = {
        "report_name": report_name,
        "success": not missing and all(check["success"] for check in checks) and freshness["is_fresh"],
        "missing_columns": missing,
        "checks": checks,
        "freshness": freshness,
    }
    report_path = settings.paths.quality_dir / f"{safe_slug(report_name)}_quality_report.json"
    write_json(report_path, report)
    return report
