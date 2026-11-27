# HƯỚNG DẪN CÀI ĐẶT MÔI TRƯỜNG, CẤU HÌNH `.env`, CHẠY MODULE DECISION & TỔNG HỢP KẾT QUẢ KIỂM THỬ

> **Nhánh tài liệu:** `docs/decision-module-setup-and-test-report` (tạo từ `develop` @ `4a832c5`)  
> **Ngày cập nhật:** 27/11/2026  
> **Kiến trúc dự án:** Modular Monolith (`FastAPI` + `SQLAlchemy 2.x` + `MySQL 8` + `Alembic` + `Vanilla HTML/CSS/JS` + `Bootstrap 5.0.2` + `Axios`)

---

## 1. Tổng quan module phụ trách

Phạm vi phụ trách tập trung vào **Module Decision (`backend/app/modules/decision/`)** và **Giao diện Đề xuất món ăn (`frontend/pages/food-results.html`, `frontend/js/pages/food-recommend.js`)**:

| Thành phần | Vị trí trong mã nguồn | Chức năng chính |
|---|---|---|
| **Database Models & Migrations** | `backend/app/modules/decision/models.py`<br>`backend/alembic/versions/b3f74c8eecf8_*.py`<br>`backend/alembic/versions/f92a86007329_*.py`<br>`backend/sql/seeds/decision_criteria.sql`<br>`backend/sql/seeds/hard_constraints.sql` | Định nghĩa và seed dữ liệu chuẩn cho bảng `decision_criteria` (Food rubric mặc định: `Giá` 40%, `Mức phù hợp nhu cầu/khẩu vị` 35%, `Thời gian chuẩn bị` 25%; Travel: `cost` 40%, `duration` 30%, `activities` 30%) và `hard_constraints` (4 quy tắc lọc bắt buộc cho Food). |
| **Decision Engine (DB-independent)** | `backend/app/modules/decision/engine/filters.py`<br>`backend/app/modules/decision/engine/scoring.py`<br>`backend/app/modules/decision/engine/pipeline.py`<br>`backend/app/modules/decision/engine/ranking.py`<br>`backend/app/modules/decision/engine/calculator.py` | Pipeline xử lý thuần Python (không truy vấn DB): lọc điều kiện bắt buộc (`<=`, `>=`, `=`, `!=`, `in`, `not_in`), chuẩn hóa Min-Max thang `0–100` cho tiêu chí `min`/`max` (xử lý `min == max -> 100.0`, giữ `None` khi thiếu dữ liệu), tính điểm tổng WSM, xếp hạng Top N và sinh giải thích. |
| **Validation đầu vào & trọng số** | `backend/app/modules/decision/schema.py`<br>`backend/app/modules/decision/hard_constraint_fields.py`<br>`backend/app/modules/decision/mock_data.py` | Kiểm tra `DecisionRecommendRequest` (`extra="forbid"`): `budget_max > 0`, `meal_type` thuộc `("breakfast", "lunch", "dinner", "snack")`, `max_prep_time > 0`, `limit` trong `[1, 20]`, và `WeightsInput` (không âm, hữu hạn, trong `[0, 1]`, tổng bằng `1.0 ± 1e-6`), trả HTTP `422` chi tiết khi sai. |
| **Tối ưu lọc SQL Pushdown & Service** | `backend/app/modules/decision/repository.py`<br>`backend/app/modules/decision/service.py`<br>`backend/app/modules/decision/router.py` | Đẩy các Hard Constraints đủ điều kiện (`price`, `prep_time`, `meal_type`, `ingredients`) xuống truy vấn SQL (`filter_food_candidates_in_db`) mà vẫn giữ tương đương 100% hành vi với `filters.py` trong bộ nhớ; điều phối `recommend_food_decisions`, `recommend_travel` và API lịch sử quyết định. |
| **Frontend Form Đề xuất món ăn** | `frontend/pages/food-results.html`<br>`frontend/js/pages/food-recommend.js` | Form nhập tiêu chí Food Recommendation (`budget_max`, `meal_type`, `max_prep_time`, `excluded_ingredients`, `preferred_tags`, `limit`), validate phía client, hiển thị lỗi API `422` ngay dưới từng ô nhập liệu, cùng các trạng thái Loading / Empty / Error / Success. |

---

## 2. Hướng dẫn cài đặt môi trường

### 2.1. Yêu cầu hệ thống

| Công cụ | Phiên bản tối thiểu | Phiên bản đã kiểm chứng thực tế | Ghi chú |
|---|---|---|---|
| **Python** | `3.10+` | `3.14.5` | Dùng cho Backend FastAPI, Alembic và `unittest`/`pytest` |
| **MySQL Server** | `8.0+` | `8.0.45` | Bắt buộc charset `utf8mb4` (`utf8mb4_unicode_ci`) |
| **Trình duyệt / HTTP tĩnh** | Chrome/Edge/Firefox bất kỳ | VS Code Live Server hoặc `python3 -m http.server` | Frontend không cần build tool hay `npm install` (tải Bootstrap 5.0.2 & Axios 1.7.9 từ CDN) |
| **Node.js (tùy chọn)** | `18+` | Đã cài tại `/usr/local/bin/node` | Chỉ cần nếu muốn chạy bộ test JS trong `frontend/tests/*.test.js` |

### 2.2. Cài đặt môi trường ảo Python & thư viện Backend

Mở terminal tại thư mục gốc dự án `DecisionHub/`:

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> [!WARNING]
> **Lưu ý quan trọng về thư viện `PyJWT` vs `jwt`:**  
> `backend/requirements.txt` yêu cầu `PyJWT>=2.8.0` (import dưới tên `import jwt` trong `app/core/security.py`). Tuyệt đối **không** cài gói `jwt` (`pip install jwt`) vì gói `jwt` sẽ ghi đè namespace `jwt` và gây lỗi `AttributeError: module 'jwt' has no attribute 'encode'` ở các chức năng/test tạo và giải mã JWT. Nếu gặp lỗi này, chạy:
> ```bash
> pip uninstall -y jwt PyJWT && pip install "PyJWT>=2.8.0"
> ```

### 2.3. Khởi tạo Database, Migration Alembic và Dữ liệu mẫu (Seed)

Thực hiện **đúng 3 bước độc lập theo thứ tự** dưới đây (từ thư mục `backend/`):

1. **Bước 1 — Tạo Database `decision_hub` (`utf8mb4`):**
   ```bash
   mysql -u root -p < sql/init.sql
   ```
   *(Hoặc mở `backend/sql/init.sql` trong MySQL Workbench và nhấn Execute.)*

2. **Bước 2 — Tạo toàn bộ cấu trúc bảng bằng Alembic:**
   *(Đảm bảo đã cấu hình xong file `backend/.env` ở Mục 3 trước khi chạy lệnh này.)*
   ```bash
   .venv/bin/alembic upgrade head   # Windows: .venv\Scripts\alembic.exe upgrade head
   ```
   Kiểm tra lại phiên bản migration hiện tại:
   ```bash
   .venv/bin/alembic current
   ```
   Kết quả chuẩn ở trạng thái mới nhất là: `d4e8a9c12b34 (head) (mergepoint)`.

3. **Bước 3 — Nạp dữ liệu mẫu (`sql/seeds/`):**
   Chạy lần lượt các script seed (đều viết theo chuẩn idempotent `INSERT IGNORE` / `WHERE NOT EXISTS`, chạy lại nhiều lần không bị trùng):
   ```bash
   mysql -u root -p decision_hub < sql/seeds/users.sql
   mysql -u root -p decision_hub < sql/seeds/foods.sql
   mysql -u root -p decision_hub < sql/seeds/travel_places.sql
   mysql -u root -p decision_hub < sql/seeds/decision_criteria.sql
   mysql -u root -p decision_hub < sql/seeds/hard_constraints.sql
   mysql -u root -p decision_hub < sql/seeds/decisions.sql
   ```

---

## 3. Hướng dẫn cấu hình `.env` & Frontend `config.js`

### 3.1. Tạo file `backend/.env`

Tạo bản sao từ file mẫu (tại thư mục `backend/`):

```bash
# macOS / Linux
cp .env.example .env

# Windows (PowerShell / CMD)
copy .env.example .env
```

> [!CAUTION]
> Tuyệt đối **không commit** file `backend/.env`, mật khẩu database hoặc `JWT_SECRET_KEY` lên Git. File `.gitignore` trong `backend/` đã loại trừ `.env`.

### 3.2. Danh sách đầy đủ các biến môi trường trong `backend/.env`

Dựa theo `backend/.env.example` và `backend/app/core/config.py`:

| Biến môi trường | Bắt buộc | Mặc định trong `config.py` | Ý nghĩa & Cách cấu hình |
|---|---|---|---|
| `APP_NAME` | Không | `DecisionHub` | Tên ứng dụng hiển thị trên Swagger UI và endpoint `/health`. |
| `DB_HOST` | Có | `127.0.0.1` | Địa chỉ máy chủ MySQL (`127.0.0.1` hoặc `localhost`). |
| `DB_PORT` | Không | `3306` | Cổng kết nối MySQL. |
| `DB_USER` | Có | `root` | Tên tài khoản MySQL dùng để chạy Alembic và FastAPI. |
| `DB_PASSWORD` | Có (nếu MySQL có pass) | `""` (rỗng) | Mật khẩu tài khoản MySQL (`config.py` tự động `quote_plus` nên hỗ trợ ký tự đặc biệt). |
| `DB_NAME` | Có | `decision_hub` | Tên database đã tạo ở `sql/init.sql`. |
| `CORS_ORIGINS` | Không | `*` | Danh sách origin được phép gọi API từ trình duyệt, phân tách bởi dấu phẩy (ví dụ: `http://127.0.0.1:5500,http://localhost:5500` hoặc `*` khi dev). |
| `JWT_SECRET_KEY` | Khuyến nghị đặt cố định | Tự sinh ngẫu nhiên mỗi lần khởi động | Khóa bí mật ký/kiểm tra JWT (`HS256`). Nếu để trống, token sẽ mất hiệu lực sau mỗi lần restart server. Sinh key mới bằng lệnh:<br>`python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_ALGORITHM` | Không | `HS256` | Thuật toán ký JWT. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Không | `60` | Thời gian sống của access token (tính bằng phút). |

**Ví dụ nội dung `backend/.env` chuẩn cho môi trường local:**
```env
APP_NAME=DecisionHub

# ---- MySQL ----
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=decision_hub

# ---- CORS ----
CORS_ORIGINS=*

# ---- JWT ----
JWT_SECRET_KEY=replace-with-generated-random-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

> [!NOTE]
> Sau khi chỉnh sửa `backend/.env`, phải dừng (`Ctrl + C`) và khởi động lại `uvicorn` để `Settings()` nạp lại cấu hình mới.

### 3.3. Kiểm tra cấu hình Frontend (`frontend/js/config.js`)

Kiểm tra file `frontend/js/config.js` đảm bảo địa chỉ `API_BASE_URL` khớp với cổng của Backend (mặc định không có tiền tố `/api`):
```js
const CONFIG = {
  API_BASE_URL: "http://127.0.0.1:8000",
  APP_NAME: "DecisionHub",
};
```

---

## 4. Hướng dẫn chạy module phụ trách

### 4.1. Khởi động Backend (FastAPI)

Mở terminal thứ nhất tại thư mục **`backend/`** (bắt buộc đứng trong `backend/` để Python tìm đúng package `app`):

```bash
cd backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# Windows: .venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

Kiểm tra nhanh sau khi server chạy:
- **Health Check:** `http://127.0.0.1:8000/health` → trả về `{"success": true, "message": "OK", "data": {"app": "DecisionHub", "status": "ok"}}`.
- **Swagger UI:** `http://127.0.0.1:8000/docs`.

### 4.2. Khởi động Frontend (Static HTTP / Live Server)

Mở terminal thứ hai tại thư mục gốc **`DecisionHub/`**:

- **Cách 1 (VS Code Live Server):** Chuột phải vào `frontend/pages/food-results.html` (hoặc `frontend/index.html`) → chọn **Open with Live Server**.
- **Cách 2 (Python HTTP Server):**
  ```bash
  python3 -m http.server 5500 --directory frontend --bind 127.0.0.1
  ```
- Truy cập giao diện module phụ trách tại:
  - **Đề xuất món ăn (Food Recommendation):** `http://127.0.0.1:5500/pages/food-results.html`
  - **Đề xuất du lịch (Travel Recommendation):** `http://127.0.0.1:5500/pages/travel-results.html`

### 4.3. Danh sách API của module Decision

| Method | Endpoint chính (& Alias tương thích) | Xác thực | Mô tả |
|---|---|---|---|
| `POST` | `/decisions/food/recommend`<br>`/api/v1/decisions/food/recommend`<br>`/decisions/recommend`<br>`/api/v1/decisions/recommend` | Optional (`Bearer`) | Lọc Hard Constraints (SQL pushdown + Engine), chấm điểm WSM (`0–100`), xếp hạng Top N, trả phương án bị loại kèm lý do. Có token hợp lệ sẽ lưu lịch sử vào bảng `decisions`. |
| `POST` | `/decisions/travel/recommend`<br>`/api/v1/decisions/travel/recommend`<br>`/api/v1/travel/recommend` | Không | Đánh giá và gợi ý địa điểm du lịch theo mô hình WSM qua `recommend_travel`. |
| `GET` | `/decisions/history`<br>`/api/v1/decisions/history` | Required (`Bearer`) | Lấy danh sách lịch sử quyết định của chính người dùng đang đăng nhập (`limit` 1–100, `offset` >= 0). |
| `GET` | `/decisions/history/{decision_id}`<br>`/api/v1/decisions/history/{decision_id}` | Required (`Bearer`) | Xem chi tiết một bản ghi lịch sử quyết định thuộc quyền sở hữu của người dùng hiện tại (trả `404` nếu không tồn tại hoặc thuộc user khác). |

### 4.4. Ví dụ gọi API nhanh bằng `curl`

**1. Gọi `POST /decisions/food/recommend` hợp lệ (`200 OK`):**
```bash
curl -s -X POST "http://127.0.0.1:8000/decisions/food/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "budget_max": 50000,
    "meal_type": "lunch",
    "max_prep_time": 30,
    "excluded_ingredients": ["tôm"],
    "preferred_tags": ["thanh đạm"],
    "limit": 5
  }'
```

**2. Gọi `POST /decisions/food/recommend` sai dữ liệu để kiểm tra Validation (`422 Unprocessable Entity`):**
```bash
curl -i -X POST "http://127.0.0.1:8000/decisions/food/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "budget_max": -10000,
    "weights": {"price": 0.5, "preference": 0.5, "prep_time": 0.5}
  }'
```

### 4.5. Các lỗi thường gặp khi chạy module

| Triệu chứng / Lỗi | Nguyên nhân | Cách khắc phục |
|---|---|---|
| `Error loading ASGI app. Could not import module "app.main"` | Chạy `uvicorn` từ thư mục gốc thay vì `backend/` | `cd backend` rồi mới chạy `uvicorn app.main:app --reload` |
| `Access denied for user 'root'@'localhost'` | Sai `DB_USER` hoặc `DB_PASSWORD` trong `backend/.env` | Cập nhật đúng thông tin MySQL trong `backend/.env` và khởi động lại server |
| `Can't connect to MySQL server on '127.0.0.1'` | MySQL Server chưa khởi động hoặc sai `DB_PORT` | Bật dịch vụ MySQL (`brew services start mysql` / MySQL Windows Service) |
| `AttributeError: module 'jwt' has no attribute 'encode'` | Trong `.venv` cài nhầm package `jwt` thay vì `PyJWT` | Chạy `pip uninstall -y jwt PyJWT && pip install "PyJWT>=2.8.0"` |
| Frontend báo `"Không kết nối được backend..."` hoặc lỗi CORS | Backend chưa chạy, sai `CONFIG.API_BASE_URL` trong `frontend/js/config.js`, hoặc sai `CORS_ORIGINS` trong `.env` | Bật backend ở cổng `8000`, giữ `API_BASE_URL: "http://127.0.0.1:8000"`, đặt `CORS_ORIGINS=*` rồi restart backend |
| Kết quả Food trả về dữ liệu mẫu thay vì DB | DB chưa chạy migration hoặc chưa nạp `foods.sql` / `decision_criteria.sql` | Chạy `alembic upgrade head` và các script trong `backend/sql/seeds/` |

---

## 5. Tổng hợp kết quả kiểm thử của module

### 5.1. Thông tin môi trường kiểm thử thực tế

| Hạng mục | Giá trị đo thực tế |
|---|---|
| **Nhánh kiểm thử** | `docs/decision-module-setup-and-test-report` (tạo từ `develop` @ `4a832c5`) |
| **Ngày kiểm thử** | `27/11/2026` |
| **Python / Backend** | Python `3.14.5` (`backend/.venv/bin/python`), FastAPI `0.115.5`, SQLAlchemy `2.1.8`, Pydantic `2.14.3`, Alembic `1.20.1` (`head: d4e8a9c12b34`) |
| **Database** | MySQL `8.0.45` (`decision_hub`, `utf8mb4` — đã seed `foods`: 8 rows, `decision_criteria`: 3 rows, `hard_constraints`: 4 rows) và SQLite In-Memory cho unit test |
| **Frontend Runtime** | Static HTTP Server (`127.0.0.1:5500`) + Node.js (`/usr/local/bin/node`) |

### 5.2. Lệnh tái lập toàn bộ kiểm thử

```bash
# 1. Chạy 5 bộ test trực tiếp thuộc phạm vi phụ trách (gộp)
backend/.venv/bin/python -m unittest \
  backend/tests/test_filters.py \
  backend/tests/test_scoring.py \
  backend/tests/test_recommend_validation.py \
  backend/tests/test_seed_food_criteria.py \
  backend/tests/test_hard_constraints.py

# 2. Chạy toàn bộ bộ test hồi quy Backend
backend/.venv/bin/python -m unittest discover -s backend/tests -p "test_*.py"

# 3. Chạy bộ test tự động Frontend (Node.js)
node --test frontend/tests/*.test.js
```

### 5.3. Kết quả kiểm thử tự động Backend (`unittest`)

#### A. Nhóm test trực tiếp phụ trách (5/5 file Pass — `121/121` test)

| STT | File kiểm thử | Phạm vi kiểm thử | Số test | Kết quả | Thời gian |
|---|---|---|---:|---|---|
| 1 | `backend/tests/test_filters.py` | Lọc Hard Constraints (`<=`, `>=`, `=`, `!=`, `in`, `not_in`), thiếu dữ liệu, tích hợp Travel Adapter (`TestTravelAdapterConstraintFiltering`) | 31 | **OK (31/31)** | 0.009s |
| 2 | `backend/tests/test_scoring.py` | Chuẩn hóa Min-Max (`min`/`max`), xử lý `min == max -> 100.0`, giữ `None` khi thiếu dữ liệu, tích hợp Travel Adapter (`TestTravelAdapterNormalization`) | 21 | **OK (21/21)** | 0.007s |
| 3 | `backend/tests/test_recommend_validation.py` | Validate `WeightsInput` (âm, NaN/Inf, tổng `!= 1.0`, boolean), `budget_max`, `meal_type`, trả HTTP `422` rõ ràng | 11 | **OK (11/11)** | 0.211s |
| 4 | `backend/tests/test_seed_food_criteria.py` | Kiểm tra seed mặc định Food `decision_criteria` (`Giá` 0.40, `Khẩu vị` 0.35, `Thời gian` 0.25) và tính idempotent | 6 | **OK (6/6)** | 0.050s |
| 5 | `backend/tests/test_hard_constraints.py` | Cấu hình `hard_constraint_fields.py`, Repository SQL pushdown filtering parity (MySQL/SQLite vs in-memory), Service | 52 | **OK (52/52)** | 0.285s |
| **Tổng** | **Chạy gộp 5 bộ test phụ trách** | **Filtering + Scoring + Validation + Seed + DB SQL Pushdown** | **121** | **OK (121/121)** | **0.474s** |

#### B. Các bộ test khác của Decision Engine, Travel Integration & API Hệ thống (`17/17` file Pass — `218/218` test)

| STT | File kiểm thử | Phạm vi kiểm thử | Số test | Kết quả | Thời gian |
|---|---|---|---:|---|---|
| 1 | `backend/tests/test_calculator.py` | Tính toán WSM & công thức chấm điểm lõi | 19 | **OK (19/19)** | 0.001s |
| 2 | `backend/tests/test_candidate.py` | Chuẩn hóa cấu trúc ứng viên | 9 | **OK (9/9)** | 0.002s |
| 3 | `backend/tests/test_decision_api.py` | Endpoint API Decision tổng quát | 4 | **OK (4/4)** | 0.018s |
| 4 | `backend/tests/test_decision_engine_unit.py` | Bộ unit test tổng hợp Decision Engine (7 nhóm mục tiêu) | 41 | **OK (41/41)** | 0.003s |
| 5 | `backend/tests/test_decision_service.py` | Service layer của module Decision | 11 | **OK (11/11)** | 0.111s |
| 6 | `backend/tests/test_engine_quality.py` | Kiểm tra chất lượng, tính nhất quán và edge cases của Engine | 20 | **OK (20/20)** | 0.001s |
| 7 | `backend/tests/test_pipeline.py` | Pipeline 3 bước (`filtering -> scoring -> ranking`) | 8 | **OK (8/8)** | 0.001s |
| 8 | `backend/tests/test_preference.py` | Chấm điểm tiêu chí khẩu vị / nhãn ưu tiên (`preferred_tags`) | 25 | **OK (25/25)** | 0.001s |
| 9 | `backend/tests/test_ranking.py` | Xếp hạng giảm dần, tie-breaker (chi phí thấp hơn, tên/ID) & Top N | 8 | **OK (8/8)** | 0.000s |
| 10 | `backend/tests/test_scoring_and_exclusions.py` | WSM scoring kết hợp giải thích phương án bị loại | 8 | **OK (8/8)** | 0.001s |
| 11 | `backend/tests/test_travel_adapter.py` | Ánh xạ `TravelPlace` & `DecisionCriterion(domain="travel")` | 9 | **OK (9/9)** | 0.006s |
| 12 | `backend/tests/test_travel_recommend.py` | Endpoint & Service gợi ý Travel (`POST /api/v1/travel/recommend`, `/decisions/travel/recommend`) | 8 | **OK (8/8)** | 0.083s |
| 13 | `backend/tests/test_weights.py` | Xử lý trọng số từ DB và trọng số tùy chỉnh | 20 | **OK (20/20)** | 0.041s |
| 14 | `backend/tests/test_wsm_verification.py` | Đối chiếu kết quả WSM với dữ liệu tính tay (`wsm_sample_verification.json`) | 6 | **OK (6/6)** | 0.002s |
| 15 | `backend/tests/test_app_error_format.py` | Chuẩn hóa format JSON khi trả lỗi | 2 | **OK (2/2)** | 0.020s |
| 16 | `backend/tests/test_exception_handlers.py` | Exception handlers toàn cục của FastAPI | 12 | **OK (12/12)** | 0.059s |
| 17 | `backend/tests/test_openapi_documentation.py` | Kiểm tra schema OpenAPI / Swagger UI | 8 | **OK (8/8)** | 0.032s |

#### C. Nhóm test liên quan JWT & Lịch sử (`3` file chịu ảnh hưởng bởi môi trường `.venv` hiện tại)

| STT | File kiểm thử | Số test | Pass | Error | Thời gian | Nguyên nhân ghi nhận trên máy local |
|---|---|---:|---:|---:|---|---|
| 1 | `backend/tests/test_decision_history.py` | 9 | 1 | 8 | 5.532s | `AttributeError: module 'jwt' has no attribute 'encode'` |
| 2 | `backend/tests/test_decision_history_api.py` | 8 | 0 | 8 | 7.218s | `AttributeError: module 'jwt' has no attribute 'encode'` |
| 3 | `backend/tests/test_recommend_api.py` | 6 | 1 | 5 | 3.661s | `AttributeError: module 'jwt' has no attribute 'encode'` |

#### D. Tổng hợp bộ hồi quy toàn dự án (`unittest discover`)

- **Tổng số test phát hiện:** `362` tests trong `17.207s` (`25` file test).
- **Đạt (Pass):** `341` tests (`0` Failure).
- **Lỗi môi trường (Error):** `21` tests — toàn bộ 21 lỗi xảy ra tại `app/core/security.py:39` (`jwt.encode(...)`) do trong `backend/.venv` hiện tại đang cài package `jwt==1.4.0` thay vì `PyJWT>=2.8.0` theo `requirements.txt`. Không phát hiện bất kỳ lỗi logic hay hồi quy nào trong Decision Engine, Filtering, Normalization, Validation, Seed hoặc SQL Pushdown.

### 5.4. Kết quả kiểm thử tự động Frontend (`node --test`)

Chạy `node --test frontend/tests/*.test.js` trên nhánh `develop` (`4a832c5`): **4/4 file test Pass** (tổng `57` kiểm tra con, thời gian `344.16ms`, `0` lỗi):

| STT | File test Frontend | Phạm vi kiểm thử | Số kiểm tra con | Kết quả | Thời gian |
|---|---|---|---:|---|---|
| 1 | `frontend/tests/api-path.test.js` | Giải quyết đường dẫn tương đối (`appUrl`), kiểm tra token hết hạn và `session.clear()` | 11 | **PASS (11/11)** | 223.45ms |
| 2 | `frontend/tests/criteria-chart.test.js` | Khởi tạo `CriteriaChart`, render cột/legend/tooltip, null-safe, empty/error state, khớp đóng góp điểm từ Backend | 17 | **PASS (17/17)** | 257.12ms |
| 3 | `frontend/tests/food-states.test.js` | Validation nhập ngân sách, trạng thái Loading/Success/Empty/Error, chống double-submit, nút Thử lại, responsive & không inline `onclick` | 14 | **PASS (14/14)** | 306.78ms |
| 4 | `frontend/tests/history.test.js` | Thứ tự import CSS, namespace `.history-page`, gọi API `GET /decisions/history`, phân trang, lọc Food/Travel, chi tiết, 404/error/401 state | 15 | **PASS (15/15)** | 255.99ms |

### 5.5. Kết quả kiểm thử trực tiếp trên Web (Browser Verification)

Khởi động thực tế Backend (`uvicorn app.main:app --host 127.0.0.1 --port 8000`) và Frontend (`python3 -m http.server 5500 --directory frontend --bind 127.0.0.1`) kết nối MySQL `8.0.45`:

- **Tổng lỗi Console:** `0`
- **Tổng lỗi Page (Uncaught Exception):** `0`
- **Tổng request mạng thất bại (`status >= 400` / network failure):** `0`

| STT | Màn hình / Endpoint | Kịch bản kiểm thử | Kết quả thực tế quan sát được | Trạng thái |
|---|---|---|---|---|
| 1 | `http://127.0.0.1:8000/health` | Kiểm tra trạng thái Backend | HTTP `200 OK`, trả về `{"success":true,"message":"OK","data":{"app":"DecisionHub","status":"ok"}}`. | **PASS** |
| 2 | `http://127.0.0.1:8000/docs` | Kiểm tra Swagger UI & các endpoint module | HTTP `200 OK` (`DecisionHub - Swagger UI`, `OAS 3.1`), hiển thị đầy đủ 18 endpoints, bao gồm `/decisions/food/recommend`, `/api/v1/decisions/food/recommend`, `/decisions/travel/recommend`, `/api/v1/travel/recommend`, `/decisions/history`, `/decisions/history/{decision_id}`. | **PASS** |
| 3 | `http://127.0.0.1:5500/pages/food-results.html` | **Case 1 — Đề xuất hợp lệ:** `budget_max=50000`, `meal_type=lunch`, `max_prep_time=30`, `excluded_ingredients=tôm` | `POST /decisions/food/recommend` trả `200 OK`. Summary cards: `2` phương án hợp lệ, Top 1 `Cơm chiên đậu hũ nấm` (`82.5/100 điểm (WSM)`), Top 2 `Bún chả Hà Nội` (`17,5/100`), `6` món bị loại hiển thị trong `#results-excluded-body`, render biểu đồ SVG tiêu chí. Nhấn vào Hạng 2 cập nhật `#results-explanation-body` sang `Hạng 2` / `Bún chả Hà Nội` (`Giá: 50.000 ₫`, `Thời gian: 20 phút`, `Bữa: Trưa`, `17,5 Điểm tổng (WSM)`). | **PASS** |
| 4 | `http://127.0.0.1:5500/pages/food-results.html` | **Case 2 — Kiểm tra Validate Form:** nhập `budget_max=-10000` và để trống `budget_max` | Không crash trang; hiển thị lỗi ngay dưới ô nhập (`#food-max-budget-error`): `"Ngân sách tối đa phải lớn hơn 0."` (khi âm) và `"Vui lòng nhập ngân sách tối đa để bắt đầu tìm món ăn."` (khi để trống). | **PASS** |
| 5 | `http://127.0.0.1:5500/pages/food-results.html` | **Case 3 — Trạng thái rỗng (Empty State):** `budget_max=5000`, `meal_type=lunch`, bỏ trống thời gian chuẩn bị và nguyên liệu tránh | `POST /decisions/food/recommend` trả `200 OK`. `#results-ranking-list` có `0` món; `#results-empty-state` hiển thị thông báo hướng dẫn nới điều kiện (*"Không tìm thấy món ăn phù hợp với tiêu chí hiện tại. Tất cả 8 món ăn đều không đạt điều kiện lọc bắt buộc (ngân sách ≤ 5.000 ₫, Bữa trưa)..."*); `#results-excluded-body` liệt kê đủ `8` món bị loại kèm lý do. | **PASS** |
| 6 | `http://127.0.0.1:5500/pages/travel-results.html` | Kiểm tra tải trang và tương tác bảng xếp hạng Travel | HTTP `200 OK`, hiển thị `7` phương án du lịch (`#1 Phố cổ Hội An (Quảng Nam)` `88,5/100`, `#2 Vịnh Hạ Long (Quảng Ninh)` `86,8/100`, ...). Chọn mục #2 cập nhật `#results-explanation-body` sang `Hạng 2` / `Vịnh Hạ Long (Quảng Ninh)` (`86,8 Điểm tổng (WSM)`). | **PASS** |

---

## 6. Ghi chú đối chiếu chuẩn `DecisionHub.md` (Mục 14)

- **Hard Constraints & Decision Engine:** Đã đáp ứng đầy đủ các tiêu chí kiểm thử tại Mục 14.1 (`Food Filtering`, `Scoring`, `Ranking`, `Explanation`, `Data`) và Mục 14.2 (`Definition of Done cho Food`), giữ nguyên tắc Decision Engine độc lập database và Frontend không tự tính điểm cuối cùng.
- **Lưu ý tích hợp Travel Hard Constraints:** Trong `backend/app/modules/decision/hard_constraint_fields.py`, `DOMAIN_CONSTRAINT_CONFIG` hiện mới khai báo cấu hình Hard Constraints cho domain `"food"`; luồng Travel sử dụng `evaluate_travel_recommendation` / `recommend_travel` với bước lọc riêng của `travel` trước khi gọi `evaluate_decision(..., domain="travel", constraints=None)`.
- **Lưu ý môi trường `.venv`:** Nếu cần chạy 3 bộ test liên quan JWT (`test_decision_history.py`, `test_decision_history_api.py`, `test_recommend_api.py`) trên máy hiện tại, cần thay thế gói `jwt==1.4.0` bằng `PyJWT>=2.8.0` đúng như `backend/requirements.txt`.
