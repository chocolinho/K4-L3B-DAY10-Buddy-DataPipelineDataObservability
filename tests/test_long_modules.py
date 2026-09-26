from dataclasses import replace
from datetime import UTC, datetime

import pandas as pd

from core.config import load_settings
from core.utils import write_json
from evaluation import metrics as evaluation_metrics
from evaluation.metrics import _token_f1
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report, generate_phase1_report
from retrieval.qa import AnswerResult


def _snapshot():
    settings = load_settings()
    records = load_raw_records(settings.paths.raw_records_json)
    return settings, build_clean_dataframe(records, datetime(2026, 9, 26, tzinfo=UTC))


def test_quality_gate_detects_duplicate_and_short_summary(tmp_path):
    settings, clean = _snapshot()
    settings = replace(settings, paths=replace(settings.paths, quality_dir=tmp_path))
    assert run_data_quality_checks(clean, settings, "baseline")["success"]

    broken = clean.copy()
    broken.loc[1, "paper_id"] = broken.loc[0, "paper_id"]
    broken.loc[2, "summary"] = "short"
    report = run_data_quality_checks(broken, settings, "corrupted")
    assert not report["success"]
    failed = {item["expectation"] for item in report["checks"] if not item["success"]}
    assert "ExpectColumnValuesToBeUnique" in failed
    assert "ExpectColumnValueLengthsToBeBetween" in failed
    assert (tmp_path / "corrupted_quality_report.json").exists()


def test_freshness_boundaries(tmp_path):
    settings, clean = _snapshot()
    sample = clean.head(4).copy()
    sample["age_days"] = [180, 0, 0, 0]
    assert build_freshness_report(sample, settings, tmp_path / "fresh.json")["is_fresh"]
    sample["age_days"] = [181, 0, 0, 0]
    report = build_freshness_report(sample, settings, tmp_path / "fresh.json")
    assert report["stale_ratio"] == 0.25 and report["is_fresh"]
    sample["age_days"] = [181, 181, 0, 0]
    assert not build_freshness_report(sample, settings, tmp_path / "fresh.json")["is_fresh"]
    assert not build_freshness_report(sample.head(0), settings, tmp_path / "fresh.json")["is_fresh"]


def test_benchmark_is_stable_and_covers_four_types(tmp_path):
    _, clean = _snapshot()
    first = build_test_set(clean, tmp_path / "benchmark.json")
    second = build_test_set(clean.sample(frac=1, random_state=7), tmp_path / "benchmark.json")
    assert first == second
    assert len(first) == 10
    assert {item["question_type"] for item in first} == {"summary", "authors", "date", "categories"}
    assert all(item["ground_truth_doc_ids"] for item in first)
    assert all(item["ground_truth"] for item in first)


def test_metrics_and_reports_use_measured_values(tmp_path):
    assert _token_f1("a a b", "a b b") == 2 / 3
    metrics = {"samples": 10, "retrieval_hit_rate": 1.0, "mean_token_f1": 0.5,
               "judge_accuracy": 0.4, "mean_judge_score": 2.5, "judge_backend": "heuristic"}
    quality = {"success": True, "checks": []}
    freshness = {"is_fresh": True, "stale_rows": 0, "total_rows": 24,
                 "stale_ratio": 0.0, "threshold_days": 180, "max_stale_ratio": 0.25,
                 "oldest_published": "2026-04-07", "latest_published": "2026-09-15",
                 "invalid_age_rows": 0}
    generate_phase1_report(tmp_path / "baseline.md", {"raw_records": 24}, metrics, quality, freshness)
    assert "Judge backend: heuristic" in (tmp_path / "baseline.md").read_text()
    generate_corruption_report(tmp_path / "comparison.md", metrics, metrics, metrics,
                               quality, quality, freshness, freshness)
    content = (tmp_path / "comparison.md").read_text()
    assert "| retrieval_hit_rate | 1.000 | 1.000 | 1.000 |" in content


def test_evaluator_records_explicit_judge_backend(tmp_path, monkeypatch):
    questions = [{"id": "q01", "question_type": "authors", "question": "Who authored it?",
                  "ground_truth": "Alice", "ground_truth_doc_ids": ["paper-1"]}]
    test_set_path = tmp_path / "test_set.json"
    write_json(test_set_path, questions)
    monkeypatch.setattr(evaluation_metrics, "answer_question", lambda *args, **kwargs: AnswerResult(
        question="Who authored it?", answer="Alice", retrieved_doc_ids=["paper-1"],
        retrieved_contexts=["Authors: Alice"], retrieved_titles=["Paper 1"]))
    monkeypatch.setattr(evaluation_metrics, "_judge_answer", lambda *args: (
        evaluation_metrics.JudgeVerdict(score=5, correct=True, reasoning="test"), "heuristic"))
    monkeypatch.setattr(evaluation_metrics, "_run_ragas", lambda *args: {"skipped": "test"})
    bundle = evaluation_metrics.evaluate_pipeline(
        load_settings(), object(), test_set_path, tmp_path / "metrics.json", tmp_path / "answers.json")
    assert bundle.summary["retrieval_hit_rate"] == 1.0
    assert bundle.summary["judge_backend"] == "heuristic"
    assert bundle.answers[0]["judge_mode"] == "heuristic"
