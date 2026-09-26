# Member Role Report — Nguyễn Đình Thái

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
|---|---|
| Họ và tên | Nguyễn Đình Thái |
| MSSV | 2A202602718 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | Buddy |
| Vai trò chính | Trưởng nhóm · Pipeline & RAG |
| Repository | `K4-L3B-DAY10-Buddy-DataPipelineDataObservability` |
| Ngày thực hiện | 2026-09-26 |

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm phụ trách | Input | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| Cấu hình và môi trường | `src/core/config.py`, `.env.example`, `README.md` | Biến môi trường và cấu trúc repo | `Settings`, đường dẫn artifacts, hướng dẫn cài/chạy | Hoàn thành |
| Embedding và vector index | `src/retrieval/embeddings.py`, `src/retrieval/index.py` | Clean dataframe | 3 collection độc lập và embedding manifests | Hoàn thành code và contract test |
| QA và Agent | `src/retrieval/qa.py`, `llm.py`, `agent.py` | Câu hỏi và index | QA có cấu trúc, provider router, Agent online/offline | Hoàn thành code; mock đã chạy thực tế |
| Baseline orchestration | `src/pipelines/phase1.py`, `script/run_phase1.py` | Raw/clean, quality, benchmark | Baseline metrics, answers và phase-1 report | Hoàn thành orchestration; chờ module Long để chạy cuối |
| Corruption/repair orchestration | `src/pipelines/corruption_flow.py`, `script/run_corruption_flow.py` | Baseline artifacts, corruption, raw snapshot | Corrupted/repaired metrics và comparison report | Hoàn thành orchestration; chờ module Linh/Long để chạy cuối |
| Tài liệu và điều phối | `README.md`, `docs/TEAM.md`, `docs/PHAN_CONG_NHOM.md` | Rubric và checkpoint | Phân công, contract, mốc bàn giao, hướng dẫn tái hiện | Hoàn thành |

## 3. Kết quả theo vai trò

- Sửa entrypoint để hai script tự thêm `src/` vào import path và chạy được trực tiếp từ thư mục repository.
- Hỗ trợ các provider `gemini`/`google`, `openai`, `anthropic`, `openrouter`, `ollama`, `custom`, `mock`; embedding model cấu hình được qua môi trường.
- Bổ sung validation schema trước khi index, collection rebuild không tích lũy bản ghi cũ, giới hạn `top_k` theo số document và manifest dùng đường dẫn tương đối.
- Chuẩn hóa `published` thành `YYYY-MM-DD` giữa cleaning, JSON artifact, Chroma metadata và QA.
- Hoàn thiện baseline flow: raw → clean → quality/freshness → index → benchmark → evaluation → demo answers → report.
- Hoàn thiện corruption flow: baseline → corruption → quality/evaluation → repair từ raw → kiểm tra idempotent → quality/evaluation → comparison report.
- Cho phép dữ liệu corrupted tiếp tục được đo khi Quality Gate fail; repaired phải pass Quality Gate trước khi index.
- Tạo mock Agent local dùng retrieval thật để demo không cần API key.

## 4. Input, output và contract

| Thành phần | Contract |
|---|---|
| Raw input | `list[PaperRecord]` từ `data/raw/crossref_records.json` |
| Clean input | DataFrame có `paper_id`, `title`, `summary`, `published`, `age_days`, `text_for_embedding` và metadata retrieval |
| Evaluation set | Một JSON benchmark duy nhất, dùng lại cho baseline, corrupted và repaired |
| Vector collections | `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| Metrics | `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy`, `mean_judge_score` |
| Repair | Xây dựng lại clean dataframe từ raw snapshot với cùng `run_date`; chạy hai lần phải cho dataframe giống nhau |

## 5. Cách xác minh đã thực hiện

```bash
.venv/Scripts/python.exe -m compileall -q src script
git diff --check
```

Các contract test đã chạy:

- Raw 24 records → clean 24 rows → index documents 24.
- Build/load Chroma collection giữ đúng 24 documents bằng embedding xác định trong bài kiểm tra cô lập.
- QA ngày trả đúng chuỗi `YYYY-MM-DD` từ exact-title lookup.
- Baseline orchestration gọi đúng thứ tự load → clean → quality/freshness → index → testset → evaluate → report.
- Corruption orchestration dùng cùng baseline benchmark, chạy hai trạng thái corrupted/repaired, kiểm tra repair idempotent và gọi comparison report.
- Mock Agent trả kết quả retrieval có title, `paper_id` và similarity score mà không cần API key.

Hai lệnh nghiệm thu cuối cùng:

```bash
.venv/Scripts/python.exe script/run_phase1.py
.venv/Scripts/python.exe script/run_corruption_flow.py
```

Hiện `run_phase1.py` đã đi qua ingestion/cleaning và dừng tại `run_data_quality_checks()` vì module của Long chưa hoàn thành. `run_corruption_flow.py` chủ động báo thiếu baseline artifacts cho tới khi phase 1 chạy xong.

## 6. Quyết định kỹ thuật quan trọng

- **Cô lập collection:** mỗi trạng thái dùng collection riêng để không ghi đè hoặc trộn vector giữa baseline, corrupted và repaired.
- **Rebuild idempotent:** collection cùng tên được xóa và tạo lại; repair được chạy hai lần với cùng raw và `run_date` để kiểm tra kết quả ổn định.
- **Quality Gate:** baseline và repaired phải pass trước khi index; corrupted vẫn tiếp tục để thu được bằng chứng về tác động của dữ liệu lỗi.
- **Artifact portable:** manifest lưu `data/chroma` tương đối với project thay vì đường dẫn tuyệt đối của máy cá nhân.
- **Offline demo:** provider `mock` dùng retrieval local trực tiếp vì fake chat model mặc định không hỗ trợ tool binding.

## 7. Lỗi và blocker đã xử lý

### Entrypoint không import được package

- **Triệu chứng:** `ModuleNotFoundError: No module named 'pipelines'` khi chạy `python script/run_phase1.py`.
- **Nguyên nhân:** Python chỉ thêm thư mục `script/` vào import path khi chạy file trực tiếp.
- **Cách xử lý:** hai entrypoint thêm `<project>/src` vào `sys.path` trước khi import pipeline.

### Mock Agent crash khi invoke

- **Triệu chứng:** `NotImplementedError` từ `FakeListChatModel.bind_tools()`.
- **Nguyên nhân:** fake chat model không hỗ trợ tool binding mà `create_agent()` yêu cầu.
- **Cách xử lý:** triển khai `MockPaperAgent` local, gọi index trực tiếp và trả `AIMessage` có kết quả retrieval.

### Blocker liên-module còn lại

- `src/ingestion/corruption.py` chưa triển khai 6 lỗi dữ liệu.
- `src/observability/quality.py`, `reporting.py` và `src/evaluation/testset.py` chưa triển khai.
- Vì vậy chưa sinh metrics và báo cáo cuối; không ghi số liệu giả vào báo cáo này.

## 8. Hiểu biết luồng end-to-end

Dữ liệu Crossref được lưu nguyên bản để bảo toàn lineage, parse thành `PaperRecord`, làm sạch và ghép `text_for_embedding`. MiniLM biến văn bản thành vector rồi ChromaDB lưu riêng theo từng trạng thái. Evaluation set giữ nguyên document IDs để so sánh công bằng. Quality checks phát hiện schema/completeness/uniqueness, còn freshness đo tuổi dữ liệu theo SLA. Corruption tạo dữ liệu lỗi nhưng vẫn được index và đánh giá để đo silent failure. Repair không vá dataframe lỗi mà dựng lại từ raw snapshot đáng tin cậy, sau đó chạy lại Quality Gate và cùng benchmark để đo mức phục hồi.

## 9. Kết quả và giới hạn hiện tại

| Metric/signal | Baseline | Corrupted | Repaired |
|---|---:|---:|---:|
| `retrieval_hit_rate` | Chờ chạy E2E | Chờ chạy E2E | Chờ chạy E2E |
| `mean_token_f1` | Chờ chạy E2E | Chờ chạy E2E | Chờ chạy E2E |
| `judge_accuracy` | Chờ chạy E2E | Chờ chạy E2E | Chờ chạy E2E |
| `mean_judge_score` | Chờ chạy E2E | Chờ chạy E2E | Chờ chạy E2E |
| Quality/freshness | Chờ module Long | Chờ module Long | Chờ module Long |

Tôi chỉ cập nhật bảng này sau khi hai pipeline chạy thành công và các số liệu khớp artifacts trong `data/results/` và `data/quality/`.

## 10. Cam kết

- [x] Nội dung phản ánh đúng phần việc và kết quả đã kiểm chứng.
- [x] Có thể giải thích luồng end-to-end và contract giữa các module.
- [x] Không ghi thành công hoặc metrics cho phần chưa chạy được.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.

**Họ và tên:** Nguyễn Đình Thái  
**Ngày xác nhận:** 2026-09-26
