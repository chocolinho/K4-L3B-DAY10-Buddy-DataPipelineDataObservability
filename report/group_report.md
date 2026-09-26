# Báo cáo nhóm Buddy — Day 10: Data Pipeline & Data Observability

> Trạng thái: báo cáo kết quả tích hợp dựa trên artifacts sinh ngày 26/09/2026.

## Nhóm và phân công

| Thành viên | MSSV | Phạm vi được giao |
|---|---|---|
| Nguyễn Đình Thái | 2A202602718 | Cấu hình, RAG, pipeline và tích hợp |
| Vũ Tiến Linh | 2A202602657 | Ingestion, cleaning, corruption và repair data |
| Dương Đình Long | 2A202602474 | Quality, freshness, evaluation và reporting |

Phân công là kế hoạch làm việc. Đóng góp cá nhân cần được xác nhận bằng commit và phần tự khai trong `docs/TEAM.md` trước khi nộp.

## Kiến trúc và dữ liệu

`Crossref raw → cleaning → quality/freshness → Chroma index → QA/evaluation → báo cáo baseline`.

Luồng thí nghiệm tiếp tục từ baseline qua corruption, đánh giá dữ liệu lỗi, repair từ raw, rồi đánh giá lại bằng cùng test set. Baseline và repair dùng cùng raw snapshot và cùng mốc `run_date` trong một lần so sánh.

Snapshot hiện có tại `data/raw/crossref_records.json` gồm 24 bài. Cleaning tạo 24 dòng, 24 `paper_id` duy nhất và các cột phục vụ embedding/evaluation. Không có bài nào trong snapshot có category nguồn; hai câu hỏi category trong benchmark dùng ground truth “No categories listed in the source metadata.” Đây là giới hạn của dữ liệu, không phải bằng chứng hệ thống suy luận được category.

## Quality Gate và freshness đã xác minh

| Tín hiệu | Baseline hiện tại | Bằng chứng |
|---|---:|---|
| Số dòng | 24 | `data/quality/baseline_quality_report.json` |
| GX expectations | 7/7 đạt | `data/quality/baseline_quality_report.json` |
| Quality success | `true` | `data/quality/baseline_quality_report.json` |
| Stale rows (`age_days > 180`) | 0/24 | `data/quality/freshness_report.json` |
| Freshness SLA | `true` | `data/quality/freshness_report.json` |

SLA chỉ vi phạm khi tỷ lệ stale vượt 25%. Các kiểm tra tự động xác nhận biên 180 ngày, đúng 25%, dữ liệu rỗng, `paper_id` trùng và summary quá ngắn. Lệnh kiểm tra: `python -B -m pytest -q tests/test_long_modules.py`.

## Benchmark và metrics

`data/eval/test_set.json` chứa 10 câu: 3 `summary`, 3 `authors`, 2 `date`, 2 `categories`. Mỗi câu có `ground_truth_doc_ids` từ baseline sạch. Test set được chọn theo `paper_id`, nên thứ tự dataframe đầu vào không làm đổi bộ câu hỏi.

Evaluator tính `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score`; mỗi câu ghi `judge_mode`, summary ghi `judge_backend` để phân biệt LLM và heuristic. Ragas chỉ chạy khi bật `RUN_RAGAS=1`.

| Metric | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| `retrieval_hit_rate` | 1.000 | 0.900 | 1.000 |
| `mean_token_f1` | 0.800 | 0.800 | 0.800 |
| `judge_accuracy` | 0.800 | 0.800 | 0.800 |
| `mean_judge_score` | 4.200 | 4.200 | 4.200 |

Ba file metrics được tạo từ cùng benchmark 10 câu. Corruption làm Hit Rate giảm 0.100 và repair phục hồi về 1.000. Token F1 và chỉ số judge không đổi trong lần chạy heuristic. Corrupted Quality Gate thất bại, trong khi baseline và repaired đều đạt; corrupted có 3/25 dòng stale (12%) nên vẫn nằm trong Freshness SLA 25%.

## Trạng thái tích hợp và nghiệm thu

- `script/run_phase1.py` và `script/run_corruption_flow.py` đều kết thúc với exit code 0.
- ChromaDB có ba collection độc lập: baseline 24, corrupted 25 và repaired 24 document.
- Corruption log ghi đủ 6 dạng lỗi: bỏ 4 bản ghi mới, blank 2 summary, chèn noise 2 summary, rút ngắn 2 title, làm cũ 2 ngày xuất bản và thêm 5 dòng trùng.
- Chạy lại corruption flow giữ repaired JSON cùng SHA-256 và collection repaired vẫn có 24 document, xác nhận repair không tích lũy dòng trùng.
- Metrics dùng heuristic judge vì nghiệm thu chạy với `LLM_PROVIDER=mock`; Ragas chưa bật. Mỗi thành viên vẫn cần xác nhận phần tự khai và nộp link LMS cá nhân.

Không chỉnh ngày xuất bản, ngưỡng freshness hoặc số liệu báo cáo để làm đẹp kết quả.
