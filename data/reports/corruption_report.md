# Baseline, corrupted and repaired comparison

## Evaluation metrics

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| samples | 10 | 10 | 10 |
| retrieval_hit_rate | 1.000 | 0.900 | 1.000 |
| mean_token_f1 | 0.800 | 0.800 | 0.800 |
| judge_accuracy | 0.800 | 0.800 | 0.800 |
| mean_judge_score | 4.200 | 4.200 | 4.200 |
| judge_backend | heuristic | heuristic | heuristic |

## Data quality and freshness

| Signal | Corrupted | Repaired |
|---|---:|---:|
| Quality success | FAIL | PASS |
| Freshness SLA | PASS | PASS |
| Stale rows | 3 | 0 |
| Stale ratio | 0.120 | 0.000 |

## Observed change

- retrieval_hit_rate: corrupted − baseline = -0.100; repaired − baseline = +0.000.
- mean_token_f1: corrupted − baseline = +0.000; repaired − baseline = +0.000.
- judge_accuracy: corrupted − baseline = +0.000; repaired − baseline = +0.000.
- mean_judge_score: corrupted − baseline = +0.000; repaired − baseline = +0.000.

A positive or negative change describes these runs only; it does not establish a cause by itself.
Baseline quality and freshness are not included in this function's inputs; consult the baseline reports.
