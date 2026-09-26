from __future__ import annotations

from typing import Any

from core.utils import write_text


METRICS = ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")


def _cell(value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "PASS" if value else "FAIL"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _quality_lines(quality: dict[str, Any]) -> list[str]:
    lines = [f"- Overall quality: {_cell(quality.get('success'))}"]
    for check in quality.get("checks", []):
        name = check.get("expectation", "unknown")
        column = check.get("column")
        lines.append(f"- {name}{f' ({column})' if column else ''}: {_cell(check.get('success'))}")
    if quality.get("missing_columns"):
        lines.append(f"- Missing columns: {_cell(', '.join(quality['missing_columns']))}")
    return lines


def _freshness_lines(freshness: dict[str, Any]) -> list[str]:
    return [
        f"- Freshness SLA: {_cell(freshness.get('is_fresh'))}",
        f"- Stale papers: {_cell(freshness.get('stale_rows'))}/{_cell(freshness.get('total_rows'))} "
        f"({_cell(freshness.get('stale_ratio'))}); threshold: "
        f">{_cell(freshness.get('threshold_days'))} days, max ratio "
        f"{_cell(freshness.get('max_stale_ratio'))}",
        f"- Published date range: {_cell(freshness.get('oldest_published'))} to "
        f"{_cell(freshness.get('latest_published'))}",
        f"- Invalid age rows: {_cell(freshness.get('invalid_age_rows'))}",
    ]


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Write a baseline report using only measured inputs."""
    lines = ["# Baseline pipeline report", "", "## Source", ""]
    lines.extend(f"- {key}: {_cell(value)}" for key, value in source_summary.items())
    lines += ["", "## Evaluation", "", f"- Samples: {_cell(metrics.get('samples'))}"]
    lines.extend(f"- {key}: {_cell(metrics.get(key))}" for key in METRICS)
    lines += [f"- Judge backend: {_cell(metrics.get('judge_backend'))}", "", "## Data quality", ""]
    lines.extend(_quality_lines(quality))
    lines += ["", "## Freshness", ""]
    lines.extend(_freshness_lines(freshness))
    if metrics.get("ragas"):
        lines += ["", "## Ragas", "", f"- Result: {_cell(metrics['ragas'])}"]
    write_text(report_path, "\n".join(lines) + "\n")


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Compare measured results from three runs without assuming recovery."""
    lines = [
        "# Baseline, corrupted and repaired comparison",
        "",
        "## Evaluation metrics",
        "",
        "| Metric | Baseline | Corrupted | Repaired |",
        "|---|---:|---:|---:|",
    ]
    for key in ("samples", *METRICS, "judge_backend"):
        lines.append(
            f"| {key} | {_cell(baseline_metrics.get(key))} | "
            f"{_cell(corrupted_metrics.get(key))} | {_cell(repaired_metrics.get(key))} |"
        )
    lines += [
        "",
        "## Data quality and freshness",
        "",
        "| Signal | Corrupted | Repaired |",
        "|---|---:|---:|",
        f"| Quality success | {_cell(corrupted_quality.get('success'))} | {_cell(repaired_quality.get('success'))} |",
        f"| Freshness SLA | {_cell(corrupted_freshness.get('is_fresh'))} | {_cell(repaired_freshness.get('is_fresh'))} |",
        f"| Stale rows | {_cell(corrupted_freshness.get('stale_rows'))} | {_cell(repaired_freshness.get('stale_rows'))} |",
        f"| Stale ratio | {_cell(corrupted_freshness.get('stale_ratio'))} | {_cell(repaired_freshness.get('stale_ratio'))} |",
        "",
        "## Observed change",
        "",
    ]
    for key in METRICS:
        baseline = baseline_metrics.get(key)
        corrupted = corrupted_metrics.get(key)
        repaired = repaired_metrics.get(key)
        if all(isinstance(value, (int, float)) for value in (baseline, corrupted, repaired)):
            lines.append(
                f"- {key}: corrupted − baseline = {corrupted - baseline:+.3f}; "
                f"repaired − baseline = {repaired - baseline:+.3f}."
            )
        else:
            lines.append(f"- {key}: insufficient measured values for comparison.")
    lines += [
        "",
        "A positive or negative change describes these runs only; it does not establish a cause by itself.",
        "Baseline quality and freshness are not included in this function's inputs; consult the baseline reports.",
    ]
    write_text(report_path, "\n".join(lines) + "\n")
