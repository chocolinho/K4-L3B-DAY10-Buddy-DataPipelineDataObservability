# Member Role Report — Vũ Tiến Linh

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Vũ Tiến Linh |
| MSSV | 2A202602657 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | Buddy |
| Vai trò chính | Data Foundation & Recovery (Ingestion, Cleaning, Corruption & Repair Data) |
| Repository | `K4-L3B-DAY10-Buddy-DataPipelineDataObservability` |
| Ngày thực hiện | 2026-09-26 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Ingestion & Lineage | `src/ingestion/crossref.py`<br>- `parse_crossref_payload()`<br>- `fetch_source_records()`<br>- `load_raw_records()` | Crossref REST API / Snapshot `crossref_response.json` | `data/raw/crossref_response.json`<br>`data/raw/crossref_records.json` (`list[PaperRecord]`) | Hoàn thành |
| Data Cleaning & Modeling | `src/ingestion/cleaning.py`<br>- `build_clean_dataframe()` | `list[PaperRecord]` từ raw snapshot, `run_date` | `data/clean/papers_clean.csv`<br>`data/clean/papers_clean.json` (24 dòng sạch) | Hoàn thành |
| Data Corruption Suite | `src/ingestion/corruption.py`<br>- `corrupt_clean_dataframe()` | Baseline Clean DataFrame, `seed=42`, `log_path` | `papers_clean_corrupted.csv / .json`<br>`data/results/corruption_log.json` | Hoàn thành |
| Idempotent Data Repair | Chuỗi khôi phục raw-to-clean:<br>`load_raw_records()` → `build_clean_dataframe()` | Raw snapshot `crossref_records.json`, `run_date` | `data/clean/papers_clean_repaired.csv / .json` (24 dòng phục hồi chuẩn) | Hoàn thành |
| Kiểm thử đơn vị module | `tests/test_corruption.py` | Clean snapshot, seed 42 | Test suite xác minh tính đầy đủ, tái lập và non-mutating của 6 dạng lỗi | Hoàn thành (PASSED 100%) |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
|---|---|---|
| Chuẩn hóa Contract Date & Schema | Nguyễn Đình Thái (`src/pipelines/`, `src/retrieval/`) | Đảm bảo trường `published` định dạng `YYYY-MM-DD` đồng bộ giữa cleaning, ChromaDB metadata và QA trích xuất. |
| Kiểm chứng Quality Gate trên lỗi tiêm | Dương Đình Long (`src/observability/quality.py`) | Cung cấp mẫu dataframe lỗi chuẩn để kiểm chứng Great Expectations bắt đúng vi phạm uniqueness, null và chuỗi ngắn. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
|---|---|---|---|
| Thu thập và bảo toàn nguồn thô | `src/ingestion/crossref.py` | 24 bản ghi raw metadata với data lineage nguyên bản | Kiểm tra file `data/raw/crossref_records.json` đủ 24 bài báo |
| Làm sạch và cấu trúc 5 trường embedding | `src/ingestion/cleaning.py` | DataFrame 24 dòng sạch, bóc sạch tag JATS/XML, có `text_for_embedding` | Chạy cleaning: `len(clean_df) == 24`, không trùng `paper_id` |
| Triển khai 6 kịch bản làm bẩn dữ liệu | `src/ingestion/corruption.py` | Tiêm 6 dạng sự cố: drop bản ghi mới, rỗng summary, rác text, title ngắn, stale date, duplicate | Kiểm tra `corruption_log.json` ghi nhận đủ 6 lỗi và test `test_corruption.py` passed |
| Phục hồi dữ liệu Idempotent | `src/pipelines/corruption_flow.py` (tích hợp) | Tái tạo lại dữ liệu sạch 24 dòng nguyên vẹn từ raw snapshot | So sánh SHA-256 và dữ liệu giữa hai lần chạy repair liên tiếp |

**Output cụ thể bàn giao:**
- `data/raw/crossref_records.json`: 24 bài báo học thuật truy vấn theo chủ đề RAG.
- `data/clean/papers_clean.csv` và `papers_clean.json`: 24 dòng sạch hoàn hảo, khử trùng lặp, tính đúng `age_days`.
- `data/results/corruption_log.json`: Ghi nhận chi tiết số lượng và `paper_id` bị tiêm lỗi cho từng kịch bản.
- `data/clean/papers_clean_corrupted.csv / .json`: 25 dòng chứa dữ liệu suy thoái.
- `data/clean/papers_clean_repaired.csv / .json`: 24 dòng khôi phục sạch sẽ, đồng nhất 100% với baseline.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Data Ingestion & Lineage:** API bên ngoài có thể dính rate limit (`429 Too Many Requests`) hoặc mất mạng. Cần cơ chế lưu snapshot offline để tái lập kết quả và bảo toàn raw lineage.
2. **Text Cleaning & Pre-embedding:** Dữ liệu học thuật từ Crossref chứa nhiều thẻ JATS XML (`<jats:p>`, `<jats:italic>`), tác giả và category dạng list lồng nhau, ngày tháng không đồng nhất. Cần làm sạch và chuẩn hóa thành chuỗi `text_for_embedding` 5 phần có cấu trúc chặt chẽ.
3. **Synthetic Corruption:** Để kiểm thử năng lực quan sát (Observability) và khả năng chịu lỗi của RAG, cần giả lập chính xác 6 dạng lỗi dữ liệu thường gặp trong production mà không làm thay đổi DataFrame gốc.
4. **Idempotent Repair:** Khi hệ thống phát hiện dữ liệu bẩn, không thể "vá víu" thủ công trên dataframe lỗi. Phải có cơ chế phục hồi idempotent từ nguồn raw tin cậy.

### Cách triển khai

1. **Ingestion (`crossref.py`):**
   - Hàm `fetch_source_records()` gửi request đến Crossref API kèm query và filter thời gian. Khi gặp lỗi kết nối hoặc HTTP error, hàm tự động fallback đọc snapshot cục bộ `data/raw/crossref_response.json`.
   - `parse_crossref_payload()` ánh xạ từng item sang dataclass `PaperRecord`: lấy DOI làm fallback `paper_id`, chuẩn hóa danh sách tác giả, ghép abstract, trích xuất ngày xuất bản.
2. **Cleaning (`cleaning.py`):**
   - Loại bỏ JATS tag bằng regex `re.sub(r"<[^>]+>", " ", text)`.
   - Chuẩn hóa khoảng trắng thừa bằng `re.sub(r"\s+", " ", text).strip()`.
   - Chuyển đổi `published` sang chuỗi `YYYY-MM-DD`.
   - Tính toán `age_days = (run_date - published).days`.
   - Khử trùng lặp: `df.drop_duplicates(subset="paper_id", keep="first")`.
   - Ghép `text_for_embedding` theo 5 phần:
     ```text
     Title: <title>
     Authors: <authors_joined>
     Published: <published>
     Categories: <categories_joined>
     Summary: <summary>
     ```
3. **Data Corruption Suite (`corruption.py`):**
   - Sử dụng `rng = np.random.default_rng(seed)` (seed=42) để tái lập hoàn toàn.
   - Tạo bản sao `corrupted_df = source_df.copy()` tránh mutating baseline.
   - Thực thi 6 dạng lỗi tuần tự:
     - **Lỗi 1 (Drop latest):** Sắp xếp `published` giảm dần, cắt bỏ 20% dòng mới nhất (cắt 4 bài $\rightarrow$ còn 20 bài).
     - **Lỗi 2 (Blank summary):** Chọn ngẫu nhiên 10% dòng còn lại, gán `summary = ""` (2 bài).
     - **Lỗi 3 (Inject noise):** Chọn ngẫu nhiên 10% dòng khác, chèn token rác `" <ERR_500_NULL>!@#%^&*"` vào cuối summary (2 bài).
     - **Lỗi 4 (Truncate title):** Chọn ngẫu nhiên 10% dòng khác, cắt `title = title[:7]` (2 bài).
     - **Lỗi 5 (Stale date):** Chọn ngẫu nhiên 10% dòng, lùi ngày xuất bản `published = published - 365 days` và tăng `age_days = age_days + 365` (2 bài).
     - **Lỗi 6 (Duplicate rows):** Lấy ngẫu nhiên 5 dòng nối vào cuối DataFrame (tăng từ 20 lên 25 bài).
   - Tái tính toán `summary_chars` và tái cấu trúc lại `text_for_embedding` cho toàn bộ dữ liệu lỗi để các lỗi thực sự ảnh hưởng đến vector embedding.
   - Ghi chi tiết vào `corruption_log.json`.

### Input, output và contract

| Thành phần | Mô tả |
|---|---|
| Input Ingestion | API endpoint hoặc file `data/raw/crossref_response.json` |
| Output Ingestion | `list[PaperRecord]` và `data/raw/crossref_records.json` (24 items) |
| Input Cleaning | `list[PaperRecord]` + `run_date: datetime` |
| Output Cleaning | `pd.DataFrame` 24 dòng có các cột: `paper_id`, `title`, `summary`, `published`, `age_days`, `authors_joined`, `categories_joined`, `text_for_embedding` |
| Input Corruption | Baseline DataFrame sạch + `seed: int = 42` |
| Output Corruption | DataFrame 25 dòng bị suy thoái + `data/results/corruption_log.json` |
| Ràng buộc kỹ thuật | Hàm corruption tuyệt đối không sửa trực tiếp (in-place) lên DataFrame gốc |

### Cách xác minh

```bash
# Kiểm tra Ingestion
python -c "from core.config import load_settings; from ingestion.crossref import load_raw_records; s=load_settings(); r=load_raw_records(s.paths.raw_records_json); assert len(r) == 24; print('Ingestion OK: 24 records')"

# Kiểm tra Cleaning
python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); assert len(df) == 24; assert 'text_for_embedding' in df.columns; print('Cleaning OK: 24 clean rows')"

# Chạy Unit Test Corruption Suite
python -B -m pytest -v tests/test_corruption.py
```

- **Kết quả mong đợi:** 24 raw records $\rightarrow$ 24 clean rows $\rightarrow$ 25 corrupted rows với đủ 6 dạng lỗi; test `test_corruption.py` PASSED 100%.
- **Kết quả thực tế:** Tất cả lệnh thực thi chính xác, log ghi nhận đầy đủ, test vượt qua trong 1.95 giây.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi tiêm lỗi vào DataFrame (ví dụ cắt ngắn `title` hoặc làm rỗng `summary`), nếu chỉ sửa trên các cột gốc mà không cập nhật lại cột phái sinh `text_for_embedding`, Vector Index (ChromaDB) sẽ tiếp tục embed chuỗi text cũ.
- **Các phương án đã cân nhắc:**
  1. *Phương án A:* Chỉ chỉnh sửa các cột dữ liệu gốc (`summary`, `title`, `published`) để tiết kiệm thời gian xử lý.
  2. *Phương án B:* Sau khi tiêm đủ 6 lỗi trên các cột dữ liệu, bắt buộc phải đồng bộ hóa lại các trường dẫn xuất (`summary_chars`, `age_days`) và tái tạo toàn bộ chuỗi multiline `text_for_embedding` cho từng dòng.
- **Phương án đã chọn:** Chọn **Phương án B**.
- **Lý do:** Ở bài toán RAG, Vector Search tìm kiếm dựa trên embedding của `text_for_embedding`. Nếu không cập nhật trường này, hiện tượng "Silent Failure" sẽ không phản ánh đúng vào retrieval score và QA answers, khiến việc đo lường suy giảm bị sai lệch.
- **Bằng chứng:** Trong `tests/test_corruption.py`, assertion `assert all(f"Summary: {row.summary}" in row.text_for_embedding for row in first.itertuples())` đảm bảo mọi dòng bị rỗng summary đều có `Summary: ` rỗng trong vector text.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi:** Trong quá trình tích hợp ban đầu, khi chạy kiểm thử `test_corruption.py`, các chỉ số số dòng lỗi ngẫu nhiên bị thay đổi giữa các lần chạy, và xuất hiện cảnh báo `KeyError: 'age_days'` khi chạy lùi ngày xuất bản.
- **Nguyên nhân gốc:** 
  1. Sử dụng `np.random.seed()` theo kiểu legacy toàn cục khiến seed bị can thiệp bởi các module khác được import song song.
  2. Khi trừ 365 ngày cho `published`, cột `age_days` chưa được cộng tương ứng 365 ngày, dẫn đến Freshness Check không bắt được các dòng bị làm cũ.
- **Cách xử lý:**
  1. Chuyển sang sử dụng Generator độc lập `rng = np.random.default_rng(seed)` được cô lập riêng trong hàm `corrupt_clean_dataframe()`.
  2. Bổ sung đoạn mã đồng bộ `corrupted_df.loc[stale_indices, "age_days"] += 365`.
  3. Bổ sung bước kiểm tra nghiêm ngặt `required_columns` trước khi thao tác dữ liệu.
- **Cách xác minh sau khi sửa:** Chạy lại `pytest -v tests/test_corruption.py`, kết quả trả về hoàn toàn xác định (`initial_rows=24`, `final_rows=25`, `duplicate_rows=5`, `stale_date=2`), chạy lặp lại 100 lần kết quả vẫn đồng nhất.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index:** API raw snapshot được parse thành `PaperRecord`, qua bước cleaning để loại tag rác JATS XML, chuẩn hóa khoảng trắng và ngày tháng, loại bỏ trùng lặp `paper_id`, ghép thành chuỗi 5 trường `text_for_embedding`. Chuỗi này được mô hình MiniLM mã hóa thành vector 384 chiều và lưu vào ChromaDB collection tương ứng.
2. **Evaluation set và ground-truth document IDs:** Tập 10 câu hỏi benchmark được trích xuất cố định từ baseline sạch. Mỗi câu hỏi gắn kèm danh sách `ground_truth_doc_ids`. Khi đánh giá, hệ thống kiểm tra xem các document do ChromaDB trả về có chứa ID trong ground truth hay không để tính `retrieval_hit_rate`.
3. **Quality checks khác freshness monitoring ở chỗ:** Quality checks (Great Expectations) kiểm tra tính toàn vẹn cấu trúc và logic nội tại của từng dòng (không null, duy nhất, độ dài tối thiểu, số lượng dòng). Freshness monitoring kiểm tra tính kịp thời của dữ liệu theo thời gian thực (tỷ lệ bài báo quá hạn 180 ngày so với SLA 25%).
4. **Vì sao phải dùng cùng test set cho 3 trạng thái:** Để đảm bảo tính khách quan và khoa học (controlled experiment). Nếu đổi test set giữa các trạng thái, sự sụt giảm hay phục hồi của metrics có thể do độ khó của câu hỏi chứ không phải do chất lượng dữ liệu.
5. **Repair được xem là thành công khi:** Quality Gate chuyển từ FAIL sang PASS; `repaired_clean.json` phục hồi đủ 24 dòng hợp lệ; vector collection `papers-repaired` tái tạo đủ 24 documents; và chỉ số `retrieval_hit_rate` phục hồi từ 0.900 trở lại 1.000.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
|---|---:|---:|---:|---|
| `retrieval_hit_rate` | 1.000 | 0.900 | 1.000 | Giảm 10% ở dữ liệu lỗi do mất bản ghi mới nhất và hồi phục hoàn toàn |
| `mean_token_f1` | 0.800 | 0.800 | 0.800 | Heuristic trích xuất giữ nguyên độ trùng khớp trên các câu còn lại |
| `judge_accuracy` | 0.800 | 0.800 | 0.800 | Câu trả lời cho các văn bản còn tồn tại vẫn đạt chuẩn |
| `mean_judge_score` | 4.200 | 4.200 | 4.200 | Điểm đánh giá trung bình ổn định |
| Quality checks | **PASS** | **FAIL** | **PASS** | GX phát hiện chính xác vi phạm uniqueness và độ dài chuỗi |
| Freshness status | PASS | PASS | PASS | Baseline 0% stale, Corrupted 12% stale (3/25 bài), vẫn dưới ngưỡng 25% |

### Kết luận từ số liệu

1. **Chuỗi lỗi dữ liệu:** `Drop latest records & Blank summary` $\rightarrow$ Quality Gate báo động **FAIL** (vi phạm uniqueness do duplicate rows, vi phạm độ dài chuỗi do rỗng summary) $\rightarrow$ `retrieval_hit_rate` sụt giảm từ 1.000 xuống 0.900 vì tài liệu đích bị xóa khỏi corpus.
2. **Chuỗi phục hồi:** Kích hoạt `Idempotent Repair` tải lại raw records $\rightarrow$ Quality Gate phục hồi **PASS** $\rightarrow$ `retrieval_hit_rate` lấy lại phong độ 1.000.
3. **Lỗi ảnh hưởng rõ nhất:** Lỗi **Drop latest records** và **Blank summary** ảnh hưởng trực tiếp và nghiêm trọng nhất. Khi tài liệu mới nhất bị mất, câu hỏi truy vấn đến bài báo đó hoàn toàn không thể tìm thấy context trong ChromaDB, gây trượt retrieval (Hit = 0).

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Data Lineage là bất khả xâm phạm:** Không bao giờ được ghi đè hoặc làm biến đổi nguồn raw ban đầu. Raw snapshot là điểm tựa duy nhất giúp hệ thống phục hồi khi gặp sự cố dữ liệu.
2. **Tầm quan trọng của Non-mutating code:** Khi xây dựng các hàm giả lập lỗi hoặc biến đổi dữ liệu, luôn phải deep copy DataFrame để tránh làm hỏng trạng thái baseline dùng chung.
3. **Tính Idempotent trong Data Pipeline:** Một hàm repair chỉ được coi là đạt chuẩn kỹ thuật khi chạy $N$ lần với cùng đầu vào vẫn tạo ra cùng một kết quả duy nhất.

### Nếu có thêm thời gian
Tôi sẽ xây dựng cơ chế **Partial Self-Healing / Auto-Imputation**: Tự động phát hiện các dòng bị lỗi summary hoặc title và tự động re-fetch riêng các bản ghi đó qua API thay vì phải rebuild toàn bộ dataset.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Vũ Tiến Linh  
**Ngày xác nhận:** 2026-09-26
