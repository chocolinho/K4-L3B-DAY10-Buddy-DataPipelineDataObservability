# Baseline pipeline report

## Source

- source: Crossref REST API
- mode: local_raw_snapshot
- query: agentic retrieval augmented generation large language model
- filter: from-pub-date:2026-03-30,has-abstract:true
- raw_records: 24
- clean_records: 24
- run_at_utc: 2026-09-26T05:39:38.437867+00:00
- raw_response_path: data\raw\crossref_response.json
- raw_records_path: data\raw\crossref_records.json

## Evaluation

- Samples: 10
- retrieval_hit_rate: 1.000
- mean_token_f1: 0.800
- judge_accuracy: 0.800
- mean_judge_score: 4.200
- Judge backend: heuristic

## Data quality

- Overall quality: PASS
- ExpectTableRowCountToBeBetween: PASS
- ExpectColumnValuesToNotBeNull (paper_id): PASS
- ExpectColumnValuesToBeUnique (paper_id): PASS
- ExpectColumnValuesToNotBeNull (title): PASS
- ExpectColumnValueLengthsToBeBetween (title): PASS
- ExpectColumnValuesToNotBeNull (summary): PASS
- ExpectColumnValueLengthsToBeBetween (summary): PASS

## Freshness

- Freshness SLA: PASS
- Stale papers: 0/24 (0.000); threshold: >180 days, max ratio 0.250
- Published date range: 2026-04-07 to 2026-09-15
- Invalid age rows: 0

## Ragas

- Result: {'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'}
