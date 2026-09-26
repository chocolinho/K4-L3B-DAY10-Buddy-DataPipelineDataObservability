# Báo cáo nhóm Buddy — Day 10: Data Pipeline & Data Observability

> Trạng thái: báo cáo tiến độ dựa trên artifact trong repository ngày 26/09/2026. Chưa phải báo cáo kết quả ba trạng thái để nộp cuối cùng.

## Nhóm và phân công

| Thành viên | MSSV | Phạm vi được giao |
|---|---|---|
| Nguyễn Đình Thái | 2A202602718 | Cấu hình, RAG, pipeline và tích hợp |
| Vũ Tiến Linh | 2A202602657 | Ingestion, cleaning, corruption và repair data |
| Dương Đình Long | 2A202602474 | Quality, freshness, evaluation và reporting |

Phân công là kế hoạch làm việc. Đóng góp cá nhân cần được xác nhận bằng commit và phần tự khai trong `docs/TEAM.md` trước khi nộp.

## Kiến trúc và dữ liệu

`Crossref raw → cleaning → quality/freshness → Chroma index → QA/evaluation → báo cáo baseline`.

Luồng thí nghiệm dự kiến tiếp tục từ baseline qua corruption, đánh giá dữ liệu lỗi, repair từ raw, rồi đánh giá lại bằng cùng test set. Baseline và repair phải dùng cùng raw snapshot và cùng mốc `run_date` trong một lần so sánh.

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
| `retrieval_hit_rate` | Chưa đo | Chưa đo | Chưa đo |
| `mean_token_f1` | Chưa đo | Chưa đo | Chưa đo |
| `judge_accuracy` | Chưa đo | Chưa đo | Chưa đo |
| `mean_judge_score` | Chưa đo | Chưa đo | Chưa đo |

Không có kết luận về suy giảm hay phục hồi trước khi ba file metrics thực tế được tạo từ cùng benchmark.

## Trạng thái tích hợp và bước còn lại

- Baseline đã tạo clean data, quality report, freshness report và test set. Bước embedding cần tải mô hình `sentence-transformers/all-MiniLM-L6-v2`; lần chạy hiện tại chưa tạo index, metrics hoặc `phase1_report.md`.
- `src/ingestion/corruption.py` và `src/pipelines/corruption_flow.py` còn `NotImplementedError`; chưa thể đo corrupted/repaired hoặc xuất `corruption_report.md`.
- Sau khi hai luồng chạy thành công, điền bảng metrics ở trên từ `data/results/*.json`, phân tích từng corruption bằng `corruption_log.json`, rồi kiểm tra báo cáo sinh tự động khớp artifact.
- Mỗi thành viên xác nhận đóng góp trong `docs/TEAM.md`, nộp báo cáo cá nhân và có commit đúng tác giả trên nhánh `main`.

Không chỉnh ngày xuất bản, ngưỡng freshness hoặc số liệu báo cáo để làm đẹp kết quả.
