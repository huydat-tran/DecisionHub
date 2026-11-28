# BÁO CÁO KẾT QUẢ CHẠY LẠI BỘ TEST CONSTRAINT FILTERING VÀ NORMALIZATION SAU KHI GHÉP TRAVEL ADAPTER – DECISIONHUB

---

## A. Thông tin kiểm thử

| Hạng mục | Chi tiết |
|---|---|
| **Tên dự án** | DecisionHub – Hệ thống hỗ trợ ra quyết định (Modular Monolith) |
| **Nhánh kiểm thử** | `test/rerun-filtering-normalization-travel` (tạo từ `develop` @ `23a5a88`) |
| **Ngày kiểm thử** | 26/11/2026 |
| **Môi trường kiểm thử** | Python 3.14.5 (`backend/.venv/bin/python`), FastAPI, SQLAlchemy 2.x, Pydantic v2, SQLite In-Memory |
| **Công cụ kiểm thử** | `unittest` (`backend/.venv/bin/python -m unittest`), kiểm tra cú pháp `py_compile`, kiểm thử web trực tiếp qua trình duyệt |
| **File test liên quan** | `backend/tests/test_filters.py`, `backend/tests/test_scoring.py`, `backend/tests/test_hard_constraints.py`, `backend/tests/test_travel_adapter.py` |

### Lệnh đã chạy
```bash
# Kiểm tra cú pháp các file test vừa cập nhật
backend/.venv/bin/python -m py_compile backend/tests/test_filters.py backend/tests/test_scoring.py

# Chạy bộ test mục tiêu sau khi ghép Travel Adapter
backend/.venv/bin/python -m unittest -v backend/tests/test_filters.py backend/tests/test_scoring.py backend/tests/test_hard_constraints.py backend/tests/test_travel_adapter.py

# Chạy hồi quy toàn bộ suite trong backend/tests/
backend/.venv/bin/python -m unittest discover -s backend/tests -p "test_*.py"
```

---

## B. Kết quả chạy lại các bộ test tự động

### 1. Kết quả từng bộ test mục tiêu & Decision Engine liên quan

| STT | File kiểm thử | Phạm vi | Số test | Kết quả | Thời gian |
|---|---|---|---:|---|---|
| 1 | `backend/tests/test_filters.py` | Hard Constraint Filtering & tích hợp Travel Adapter (`TestTravelAdapterConstraintFiltering`: +3 test) | 31 | **OK (31/31)** | 0.008s |
| 2 | `backend/tests/test_scoring.py` | Criteria Scoring, Min-Max Normalization & tích hợp Travel Adapter (`TestTravelAdapterNormalization`: +5 test) | 21 | **OK (21/21)** | 0.007s |
| 3 | `backend/tests/test_hard_constraints.py` | HardConstraint fields config, Repository, Service & DB SQL filtering parity | 52 | **OK (52/52)** | 0.339s |
| 4 | `backend/tests/test_travel_adapter.py` | `adapt_travel_candidate`, `adapt_travel_candidates`, `adapt_travel_criteria`, pipeline Travel | 9 | **OK (9/9)** | 0.007s |
| **Tổng** | **4 bộ test mục tiêu (chạy gộp)** | **Constraint Filtering + Normalization + Hard Constraints + Travel Adapter** | **113** | **OK (113/113)** | **0.333s** |
| 5 | `backend/tests/test_pipeline.py` | Pipeline 3 bước & thống kê `total_valid`/`returned_count` | 8 | **OK (8/8)** | 0.001s |
| 6 | `backend/tests/test_scoring_and_exclusions.py` | WSM scoring, tie-break & giải thích phương án bị loại | 8 | **OK (8/8)** | 0.001s |
| 7 | `backend/tests/test_decision_engine_unit.py` | Bộ unit test tổng hợp Decision Engine (7 nhóm mục tiêu) | 41 | **OK (41/41)** | 0.003s |

### 2. Kết quả chạy hồi quy toàn bộ `backend/tests/` (`unittest discover`)

- **Trước khi thêm test mới (baseline trên `develop` `23a5a88`):** `346` tests (`325` pass, `21` error).
- **Sau khi thêm 8 test mới tích hợp Travel Adapter:** `354` tests trong `18.362s` (`333` pass, `21` error).
- **Giải thích 21 lỗi có sẵn trong môi trường `.venv`:** Toàn bộ `21` lỗi đều xảy ra ở các test tạo/giải mã JWT (`test_decision_history.py`, `test_decision_history_api.py`, `test_recommend_api.py`) do trong `backend/.venv` đang cài package `jwt==1.4.0` thay vì `PyJWT`, dẫn đến `AttributeError: module 'jwt' has no attribute 'encode'` / `'decode'` / `'PyJWTError'` tại `app/core/security.py` và `app/modules/auth/dependencies.py`. Không có lỗi hay thất bại nào ở Decision Engine, Travel Adapter, Constraint Filtering hoặc Normalization.

---

## C. Ma trận đối chiếu với `docs/TRAVEL_DECISION_TEST_CASES.md`

| Mã TC / Nhóm | Nội dung kiểm thử | Nơi kiểm chứng | Trạng thái |
|---|---|---|---|
| **Nhóm 2** (`TC-MAP-01`, `TC-MAP-02`, `TC-MAP-03`) | Ánh xạ `TravelPlace` ORM / dict / missing `highlights` sang candidate struct, idempotent `field_name` | `test_travel_adapter.py`, `test_scoring.py` | **Pass** |
| **Nhóm 3** (`Hard Constraints Filtering`) | Ứng viên Travel qua adapter đi qua `filter_candidates` / `filter_and_explain_candidates` / `evaluate_decision` khi `constraints=None`; kiểm chứng domain `"travel"` chưa đăng ký trong `DOMAIN_CONSTRAINT_CONFIG` sẽ báo `ValueError` rõ ràng; kiểm tra hồi quy Food constraints | `test_filters.py` (`TestTravelAdapterConstraintFiltering`), `test_hard_constraints.py` | **Pass (theo contract hiện tại trên `develop`)** |
| **Nhóm 4** (`TC-SCR-01`..`TC-SCR-06`) | Chuẩn hóa `estimated_cost` (`min`), `estimated_duration` (`min`), `activities` (`max`), `min == max -> 100.0`, giữ `None` khi thiếu dữ liệu trong dict, không tính `score` và không mutate input | `test_scoring.py` (`TestTravelAdapterNormalization`) | **Pass** |
| **Nhóm 8** (`TC-EDG-03`, `TC-EDG-04`, `TC-EDG-05`) | 1 ứng viên hợp lệ (`min == max`), chi phí miễn phí (`estimated_cost = 0`), thời lượng `Decimal` thập phân (`1.5`, `4.5`) | `test_scoring.py` (`TestTravelAdapterNormalization`) | **Pass** |
| **Pipeline & Custom Weights** | `DecisionCriterion(domain="travel")` từ DB + `custom_weights` qua `adapt_travel_criteria` chạy end-to-end qua `evaluate_decision(..., domain="travel")` | `test_travel_adapter.py`, `test_scoring.py` | **Pass** |

---

## D. Phát hiện & Lưu ý tương thích sau khi ghép Travel Adapter

1. **Đăng ký cấu hình Hard Constraints cho domain `"travel"`:**
   - Trong `backend/app/modules/decision/hard_constraint_fields.py`, `DOMAIN_CONSTRAINT_CONFIG` hiện mới khai báo domain `"food"` (chưa khai báo `"travel"`), và `backend/tests/test_hard_constraints.py` đang kiểm tra khẳng định `get_domain_constraint_config("travel")` / `validate_constraint("travel", ...)` / `filter_candidates(..., domain="travel")` với constraint chủ động phải raise `ValueError`.
   - Khi gọi `evaluate_decision(adapted_candidates, adapted_criteria, domain="travel")` với `constraints=None`, pipeline chạy bình thường. Khi nhóm tích hợp endpoint `POST /api/v1/travel/recommend` dùng chung `filters.py` với `domain="travel"`, cần bổ sung cấu hình `"travel"` vào `DOMAIN_CONSTRAINT_CONFIG` và cập nhật test tương ứng.
2. **Xử lý dữ liệu thiếu giữa Travel Adapter và Scoring:**
   - `adapt_travel_candidate()` chuẩn hóa `estimated_cost` thiếu thành `0`, `estimated_duration` thiếu thành `0.0`, và `highlights` thiếu/`None` thành `activities = 0.0` (an toàn, không lỗi `AttributeError`/`TypeError`).
   - Nếu ứng viên dict đưa vào `score_candidates()` có giá trị `None` (ví dụ `activities=None`), `score_candidates()` giữ nguyên `criteria_scores["activities"] = None` và không tự suy diễn điểm.

---

## E. Kết quả kiểm thử trực tiếp trên Web (Browser)

Khởi động server cục bộ trực tiếp từ nhánh `test/rerun-filtering-normalization-travel`:
- Backend FastAPI: `uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Frontend tĩnh: `python3 -m http.server 5500 --directory frontend --bind 127.0.0.1`

Kết quả kiểm tra trực tiếp trên trình duyệt (`0` lỗi console, `0` lỗi page, `0` request mạng thất bại):

1. **Swagger UI (`http://127.0.0.1:8000/docs`)**
   - Trạng thái: `200 OK` (`DecisionHub - Swagger UI`), hiển thị 15 endpoint (`/health`, `/api/v1/decisions/food/recommend`, `/decisions/food/recommend`, `/api/v1/food`, `/auth/register`, `/auth/login`, `/users/me`, `/decisions/recommend`, `/decisions/history`, ...).
2. **Đề xuất món ăn (`http://127.0.0.1:5500/pages/food-results.html`)**
   - Gửi form `#food-recommend-form` với bộ lọc Hard Constraints: `budget_max=50000`, `meal_type=lunch`, `max_prep_time=30`, `excluded_ingredients=tôm`.
   - Request `POST http://127.0.0.1:8000/decisions/food/recommend` trả về **`200 OK`** (không rơi vào fallback lỗi).
   - Summary cards hiển thị: Tổng phương án hợp lệ = `2`, Phương án điểm cao nhất = `Cơm chiên đậu hũ nấm` (`82.5/100 điểm (WSM)`), Phương án bị loại = `6`.
   - Bảng xếp hạng hiển thị `1. Cơm chiên đậu hũ nấm (82,5/100)` và `2. Bún chả Hà Nội (17,5/100)`. Chọn mục #2 cập nhật khung giải thích (`#results-explanation-body`) và biểu đồ SVG tiêu chí sang Hạng 2 (`17,5` WSM) cùng lý do chi tiết.
   - Khu vực phương án bị loại (`#results-excluded-body`) hiển thị đầy đủ `6 phương án` kèm lý do vi phạm chính xác (sai `meal_type`, vượt `budget_max`, chứa `tôm sú`).
3. **Đề xuất du lịch (`http://127.0.0.1:5500/pages/travel-results.html`)**
   - Tải trang `200 OK`, hiển thị 7 địa điểm du lịch xếp hạng WSM (`#1 Phố cổ Hội An (Quảng Nam)` `88,5/100`, `#2 Vịnh Hạ Long (Quảng Ninh)` `86,8/100`, ...).
   - Chọn mục #2 (`Vịnh Hạ Long (Quảng Ninh)`) cập nhật tương tác khung giải thích sang Hạng 2 (`86,8` WSM), cập nhật biểu đồ SVG tiêu chí và ưu/nhược điểm.
4. **Khám phá du lịch (`http://127.0.0.1:5500/pages/travel.html`)**
   - Tải trang `200 OK`, ban đầu hiển thị `26` địa điểm toàn quốc.
   - Chọn chip lọc vùng miền `"Miền Bắc"` trong `#chip-travel-regions`: danh sách lọc còn `8` địa điểm Miền Bắc (`#1 Làng cổ Đường Lâm` `97.0 WSM` ... `#8 Du thuyền Vịnh Lan Hạ 5 sao` `29.4 WSM`).
