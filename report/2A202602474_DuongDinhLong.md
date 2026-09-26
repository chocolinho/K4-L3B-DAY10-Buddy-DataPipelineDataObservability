# Member Role Report — Dương Đình Long

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Dương Đình Long |
| MSSV | 2A202602474 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | Buddy |
| Vai trò chính | Observability & Evaluation (Quality Gate, Freshness SLA, Benchmark & Reporting) |
| Repository | `K4-L3B-DAY10-Buddy-DataPipelineDataObservability` |
| Ngày thực hiện | 2026-09-26 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Data Quality Gate (GX 1.x) | `src/observability/quality.py`<br>- `run_data_quality_checks()` | DataFrame (baseline, corrupted, repaired), `Settings` | `baseline_quality_report.json`<br>`corrupted_quality_report.json`<br>`repaired_quality_report.json` | Hoàn thành |
| Freshness SLA Monitoring | `src/observability/quality.py`<br>- `build_freshness_report()` | DataFrame, ngưỡng 180 ngày, SLA 25% | `freshness_report.json`<br>`corrupted_freshness_report.json`<br>`repaired_freshness_report.json` | Hoàn thành |
| Benchmark Test Set Generator | `src/evaluation/testset.py`<br>- `build_test_set()` | Baseline Clean DataFrame | `data/eval/test_set.json` (10 câu hỏi cố định thuộc 4 nhóm) | Hoàn thành |
| Evaluation Metrics & Judge | `src/evaluation/metrics.py`<br>- `evaluate_pipeline()`<br>- `_token_f1()`<br>- `_judge_answer()` | Index, test set, Settings | `data/results/*_metrics.json`<br>`data/results/*_answers.json` | Hoàn thành |
| Báo cáo tự động hóa | `src/observability/reporting.py`<br>- `generate_phase1_report()`<br>- `generate_corruption_report()` | Metrics, quality, freshness từ 3 trạng thái | `data/reports/phase1_report.md`<br>`data/reports/corruption_report.md` | Hoàn thành |
| Báo cáo tổng hợp nhóm | `report/group_report.md` | Toàn bộ artifacts và kết quả tích hợp | Báo cáo phân công, kiến trúc, metrics đối chiếu 3 trạng thái | Hoàn thành |
| Bộ test tự động module | `tests/test_long_modules.py` | Fixtures dữ liệu và snapshot | 5 unit tests kiểm thử quality gate, freshness, benchmark, metrics | Hoàn thành (5/5 PASSED) |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Kiểm tra chất lượng dữ liệu sạch | Vũ Tiến Linh (`src/ingestion/cleaning.py`) | Xác minh DataFrame sau khi làm sạch vượt qua 7/7 expectations của Great Expectations và đạt chuẩn Freshness. |
| Tích hợp luồng đánh giá vào Pipeline | Nguyễn Đình Thái (`src/pipelines/`) | Thống nhất cấu trúc trả về của `evaluate_pipeline` và `run_data_quality_checks` để tích hợp mượt mà vào `phase1.py` và `corruption_flow.py`. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Thiết lập chốt kiểm dịch GX 1.x | `src/observability/quality.py` | Phát hiện chính xác lỗi rỗng, ngắn và trùng lặp; tạo JSON report chi tiết | Chạy kiểm tra trên corrupted: `success=False`, `ExpectColumnValuesToBeUnique` FAIL |
| Giám sát độ trễ dữ liệu Freshness | `src/observability/quality.py` | Đo lường tỷ lệ `age_days > 180`, kiểm soát SLA 25% | Test biên 180 ngày và 25% tỷ lệ stale tại `test_freshness_boundaries` |
| Xây dựng bộ test đánh giá chuẩn | `src/evaluation/testset.py` | 10 câu hỏi bao phủ 4 nhóm: 3 summary, 3 authors, 2 date, 2 categories | File `data/eval/test_set.json` sinh xác định, cố định ground truth doc IDs |
| Đo lường hiệu năng 3 trạng thái | `src/evaluation/metrics.py` | Bảng so sánh lượng hóa Hit Rate sụt giảm (-0.100) và phục hồi hoàn toàn | Đối chiếu file `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json` |
| Sinh báo cáo đối chiếu tự động | `src/observability/reporting.py` | Báo cáo Markdown 3 cột so sánh trực quan, minh bạch | File `data/reports/corruption_report.md` |

**Output cụ thể bàn giao:**
- `data/quality/baseline_quality_report.json`: 7/7 checks đạt, `success = true`.
- `data/quality/corrupted_quality_report.json`: `success = false`, chỉ rõ vi phạm ở `summary` rỗng và `paper_id` trùng lặp.
- `data/quality/freshness_report.json`: Baseline 0% stale; Corrupted 12% stale (3/25 bài), vẫn tuân thủ SLA 25%.
- `data/eval/test_set.json`: 10 câu hỏi chuẩn, có ground truth trích xuất từ dữ liệu sạch.
- `data/reports/corruption_report.md`: Bảng so sánh 3 trạng thái Baseline vs Corrupted vs Repaired.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Thiếu khả năng quan sát dữ liệu (Data Observability):** Trong các hệ thống RAG truyền thống, dữ liệu bẩn đi thẳng vào vector database mà không có cảnh báo nào, dẫn đến "Silent Failure" (AI trả lời sai mà không biết nguyên nhân). Cần thiết lập chốt chặn tự động (Quality Gate) bằng Great Expectations 1.x.
2. **Quản lý độ tươi mới dữ liệu (Data Freshness SLA):** Bài báo nghiên cứu khoa học cần cập nhật. Nếu tỷ lệ bài báo quá hạn (>180 ngày) vượt quá ngưỡng cho phép (>25%), hệ thống phải phát cảnh báo vi phạm SLA.
3. **Đánh giá chuẩn hóa và công bằng:** Cần một bộ benchmark 10 câu hỏi ổn định, bao phủ nhiều khía cạnh thông tin (tóm tắt, tác giả, ngày tháng, chuyên mục) và giữ nguyên ground-truth IDs qua các thí nghiệm.
4. **Minh bạch cơ chế chấm điểm (Judge Backend):** Cần phân định rõ ràng khi nào hệ thống sử dụng LLM Judge và khi nào dùng Fallback Heuristic Judge để tránh ngộ nhận về kết quả.

### Cách triển khai

1. **Chốt kiểm dịch Great Expectations 1.x (`quality.py`):**
   - Áp dụng chuẩn **GX 1.x Ephemeral Context**:
     ```python
     context = gx.get_context(mode="ephemeral")
     source = context.data_sources.add_pandas(name="papers_source")
     asset = source.add_dataframe_asset(name="papers_asset")
     batch_def = asset.add_batch_definition_whole_dataframe("papers_batch")
     batch = batch_def.get_batch(batch_parameters={"dataframe": df})
     ```
   - Định nghĩa 4 nhóm Expectations thiết yếu (7 checks):
     - `ExpectTableRowCountToBeBetween(min_value=24, max_value=24)`
     - `ExpectColumnValuesToNotBeNull(column="paper_id")`
     - `ExpectColumnValuesToBeUnique(column="paper_id")`
     - `ExpectColumnValuesToNotBeNull(column="title")`
     - `ExpectColumnValueLengthsToBeBetween(column="title", min_value=8)`
     - `ExpectColumnValuesToNotBeNull(column="summary")`
     - `ExpectColumnValueLengthsToBeBetween(column="summary", min_value=50)`
   - Kết quả trả về gồm `success: bool`, chi tiết từng check và báo cáo freshness kèm theo.

2. **Freshness SLA Monitoring (`_freshness` trong `quality.py`):**
   - Xác định `stale_rows = sum(df["age_days"] > 180)`.
   - Tính `stale_ratio = stale_rows / total`.
   - Đánh giá `is_fresh`: Đạt khi và chỉ khi dữ liệu không rỗng (`total > 0`), không có dòng lỗi ngày (`invalid_age_rows == 0`), và `stale_ratio <= 0.25`.

3. **Benchmark Testset Generator (`testset.py`):**
   - Trích xuất từ clean dataframe: lọc bỏ các tiêu đề có chứa dấu nháy đơn (`'`) để tránh lỗi regex khi parse câu hỏi.
   - Sắp xếp ổn định theo `paper_id` và lấy 10 bài đầu tiên.
   - Phân bổ 10 câu hỏi theo 4 nhóm nghiệp vụ:
     - 3 câu `summary`: "Summarize the paper '{title}'." $\rightarrow$ Ground truth: câu đầu tiên của summary.
     - 3 câu `authors`: "Who authored the paper '{title}'?" $\rightarrow$ Ground truth: danh sách tác giả nối chuỗi.
     - 2 câu `date`: "When was the paper '{title}' published?" $\rightarrow$ Ground truth: ngày ISO `YYYY-MM-DD`.
     - 2 câu `categories`: "Which categories are listed for the paper '{title}'?" $\rightarrow$ Ground truth: chuyên mục hoặc câu mặc định nguồn.

4. **Đo lường và Đánh giá (`metrics.py`):**
   - `retrieval_hit_rate`: Đếm tỷ lệ câu hỏi mà top-k retrieved documents chứa ít nhất 1 `paper_id` thuộc `ground_truth_doc_ids`.
   - `_token_f1`: Tính F1 dựa trên tập token trùng lặp (Counter intersection) giữa câu trả lời và ground truth.
   - `_judge_answer`: Thử nghiệm gọi LLM Judge với structured output `JudgeVerdict(score, correct, reasoning)`. Nếu không có LLM credentials hoặc lỗi kết nối, tự động fallback sang Heuristic Judge dựa trên ngưỡng Token F1 ($\ge 0.95 \rightarrow 5$đ, $\ge 0.5 \rightarrow 3$đ, $< 0.5 \rightarrow 1$đ). Ghi nhận nhãn `judge_backend = "heuristic"` để đảm bảo tính trung thực trong báo cáo.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input Quality Gate | DataFrame bất kỳ + `Settings` |
| Output Quality Gate | `dict` có `success: bool`, `checks: list[dict]`, `freshness: dict` |
| Input Freshness | DataFrame + `report_path: Path` |
| Output Freshness | `dict` có `stale_rows`, `stale_ratio`, `is_fresh: bool`, dải ngày xuất bản |
| Input Benchmark | Clean DataFrame |
| Output Benchmark | `data/eval/test_set.json` (list 10 dicts) |
| Output Reporting | File Markdown tổng hợp: `phase1_report.md` và `corruption_report.md` |

### Cách xác minh

```bash
# Kiểm tra toàn bộ 5 unit tests của module Observability & Evaluation
python -B -m pytest -v tests/test_long_modules.py
```

- **Kết quả mong đợi:** Vượt qua toàn bộ 5/5 tests:
  - `test_quality_gate_detects_duplicate_and_short_summary`: PASSED
  - `test_freshness_boundaries`: PASSED
  - `test_benchmark_is_stable_and_covers_four_types`: PASSED
  - `test_metrics_and_reports_use_measured_values`: PASSED
  - `test_evaluator_records_explicit_judge_backend`: PASSED
- **Kết quả thực tế:** 5/5 tests đều PASSED, thời gian chạy hoàn tất trong ~85 giây.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi chạy pipeline trên dữ liệu bị tiêm lỗi (`corrupted_df`), Quality Gate chắc chắn sẽ phát hiện lỗi và trả về `success = False`. Theo nguyên tắc nghiêm ngặt của chốt kiểm dịch (Quality Gate), khi dữ liệu lỗi thì pipeline phải dừng lại ngay lập tức (raise RuntimeError).
- **Các phương án đã cân nhắc:**
  1. *Phương án A (Chặn tuyệt đối):* Khi Quality Gate fail, ném exception và dừng chương trình, không cho phép sinh index hay đo metrics trên corrupted data.
  2. *Phương án B (Phân nhánh mục đích thí nghiệm):* Tại pipeline baseline và repaired (môi trường sản xuất), bắt buộc `success == True` mới cho phép index; nhưng tại pipeline corrupted (nhánh đo lường suy giảm), ghi nhận trạng thái FAIL vào báo cáo chất lượng nhưng vẫn cho phép luồng tiếp tục index và đánh giá nhằm đo lường mức độ sụp đổ hiệu năng của AI.
- **Phương án đã chọn:** Chọn **Phương án B**.
- **Lý do:** Mục tiêu cốt lõi của bài Lab 10 là chứng minh hiện tượng **Silent Failure** và định lượng sự sụt giảm của RAG khi dữ liệu bẩn lọt qua. Nếu chặn ngay tại Quality Gate, nhóm sẽ không thể thu thập được số liệu thực tế cho cột `Corrupted` trong bảng đối chiếu 3 trạng thái.
- **Bằng chứng:** Trong `corruption_report.md`, cột Corrupted ghi nhận `Quality success = FAIL` nhưng vẫn đo được `retrieval_hit_rate = 0.900`, chứng minh sự sụt giảm 10% so với baseline 1.000.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi:** Lỗi crash khi nâng cấp lên Great Expectations 1.x: `AttributeError: 'DataContext' object has no attribute 'sources'` hoặc `ExpectationSuiteValidationResult` không khớp cấu trúc khi chạy lệnh kiểm thử cũ.
- **Nguyên nhân gốc:** Phiên bản Great Expectations 1.16+ đã loại bỏ cú pháp cũ (v0.x / Early v1) của Checkpoint và DataContext dạng file tĩnh. Chuẩn mới 1.x yêu cầu sử dụng `gx.get_context(mode="ephemeral")`, định nghĩa DataSource qua `add_pandas()`, gán DataAsset, tạo BatchDefinition và gọi `batch.validate(expectation)`.
- **Cách xử lý:** 
  1. Tái cấu trúc toàn bộ hàm `run_data_quality_checks` theo đúng kiến trúc Batch Definition của GX 1.x.
  2. Khởi tạo expectation trực tiếp từ package `gx.expectations.Expect*`.
  3. Bóc tách kết quả từ `validation_result.result` một cách an toàn.
- **Cách xác minh sau khi sửa:** Chạy kiểm thử tự động, hàm khởi tạo ephemeral context sạch sẽ, không tạo các thư mục cấu hình rác `great_expectations/` trong repository, phát hiện chuẩn xác vi phạm trùng lặp và độ dài chuỗi.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index:** Dữ liệu thô từ Crossref REST API được làm sạch, loại bỏ thẻ XML và khoảng trắng, tính toán `age_days`, lọc trùng lặp và cấu trúc thành trường `text_for_embedding`. Chuỗi văn bản này được mô hình MiniLM nhúng thành vector ngữ nghĩa và nạp vào ChromaDB theo từng collection biệt lập.
2. **Evaluation set và ground-truth document IDs:** Bộ câu hỏi benchmark được tạo một lần duy nhất từ dữ liệu sạch ban đầu, gồm 10 câu hỏi thuộc 4 nhóm nghiệp vụ. Mỗi câu hỏi đi kèm danh sách ID tài liệu gốc. Trong quá trình đánh giá, hệ thống kiểm tra xem các tài liệu mà ChromaDB truy xuất được có chứa ID gốc hay không để đo lường `retrieval_hit_rate`.
3. **Quality checks khác freshness monitoring ở chỗ:** Quality Gate sử dụng Great Expectations để kiểm tra tính toàn vẹn cấu trúc tĩnh (schema, không rỗng, duy nhất, độ dài chuỗi tối thiểu). Freshness SLA đo lường tính kịp thời động của dữ liệu theo thời gian thực (đảm bảo tỷ lệ tài liệu quá hạn 180 ngày không vượt quá 25%).
4. **Vì sao phải dùng cùng test set cho cả 3 trạng thái:** Đảm bảo nguyên tắc kiểm soát biến độc lập trong nghiên cứu thực nghiệm. Nếu dùng các bộ test khác nhau cho baseline, corrupted và repaired, sự thay đổi của các chỉ số hiệu năng sẽ bị nhiễu do độ khó của câu hỏi chứ không phản ánh đúng tác động của chất lượng dữ liệu.
5. **Repair được xem là thành công khi:** Dữ liệu khôi phục vượt qua toàn bộ 7/7 kiểm tra của Quality Gate (`success = true`), đạt chuẩn Freshness SLA, và chỉ số `retrieval_hit_rate` trên ChromaDB phục hồi trọn vẹn từ 0.900 trở lại 1.000.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | **1.000** | **0.900** | **1.000** | Sụt giảm 0.100 khi dữ liệu lỗi và phục hồi 100% sau repair |
| `mean_token_f1` | 0.800 | 0.800 | 0.800 | Độ trùng khớp từ ngữ ổn định trên các câu hỏi còn context |
| `judge_accuracy` | 0.800 | 0.800 | 0.800 | Đánh giá tính đúng đắn ngữ nghĩa của câu trả lời |
| `mean_judge_score` | 4.200 | 4.200 | 4.200 | Điểm chất lượng trung bình (thang điểm 5) |
| Quality checks | **PASS** | **FAIL** | **PASS** | Bắt trúng vi phạm uniqueness do duplicate và length do rỗng summary |
| Freshness status | PASS | PASS | PASS | Baseline 0% stale, Corrupted 12% stale (3 bài), Repaired 0% stale |

### Kết luận từ số liệu

1. **Chuỗi lỗi dữ liệu:** `Data Corruption (Drop latest & Blank summary)` $\rightarrow$ `Quality Gate chuyển sang FAIL` $\rightarrow$ `Retrieval Hit Rate giảm từ 1.000 xuống 0.900`.
2. **Chuỗi phục hồi:** `Idempotent Repair từ raw` $\rightarrow$ `Quality Gate trở lại PASS` $\rightarrow$ `Retrieval Hit Rate hồi phục về 1.000`.
3. **Phân tích nguyên nhân:** Chỉ số Hit Rate bị giảm 10% ở dữ liệu corrupted là do 20% bản ghi mới nhất bị cắt bỏ. Khi benchmark hỏi về một bài báo nằm trong số bị xóa, Vector Search không thể tìm thấy document ID đó trong top-k kết quả. Sau khi chạy Repair khôi phục từ raw records, các bài báo này xuất hiện trở lại trong ChromaDB và Hit Rate lập tức hồi phục về 1.000.
4. **Tính minh bạch:** Báo cáo ghi nhận rõ `judge_backend = "heuristic"` do môi trường nghiệm thu không sử dụng API key ngoài.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Data Observability là tuyến phòng thủ hàng đầu:** Trước khi đổ lỗi cho thuật toán embedding hay LLM khi AI trả lời sai, cần kiểm tra Data Quality Gate đầu tiên.
2. **Tính nghiêm ngặt của Freshness SLA:** Không bao giờ được phép sửa ngày xuất bản hoặc hạ ngưỡng SLA để ép pipeline đạt pass giả tạo. Cảnh báo freshness phải được báo cáo trung thực.
3. **Kiểm thử tự động hóa cho Data Pipeline:** Xây dựng unit tests cho các hàm tính metrics và boundary checks giúp phát hiện sớm các lỗi ngầm trước khi đưa vào pipeline chính.

### Nếu có thêm thời gian
Tôi sẽ xây dựng một **Interactive Observability Dashboard** bằng Streamlit hiển thị trực quan các biểu đồ phân bố độ tuổi bài báo (`age_days`), trạng thái từng expectation của Great Expectations và biểu đồ radar so sánh hiệu năng giữa 3 trạng thái theo thời gian thực.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Dương Đình Long  
**Ngày xác nhận:** 2026-09-26
