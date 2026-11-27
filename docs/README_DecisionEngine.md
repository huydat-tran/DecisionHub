# 📘 Hướng dẫn sử dụng **Decision Engine** (DecisionHub)

## 1. Giới thiệu

Decision Engine thực hiện các bước sau để đưa ra gợi ý quyết định:

1️⃣ **Hard‑Constraints** – Loại bỏ các phương án không thỏa các ràng buộc bắt buộc (giá, thời gian, loại bữa, nguyên liệu...).
2️⃣ **Scoring (Weighted Sum Model – WSM)** – Tính điểm cho mỗi tiêu chí, nhân với trọng số, tổng lại thành `total_score`.
3️⃣ **Ranking** – Sắp xếp giảm dần theo `total_score`, gán `rank`. Khi điểm bằng nhau, ưu tiên chi phí thấp hơn (hoặc `id`).

**Công thức WSM**

$$
\text{score}_i = \sum_{c=1}^{N} w_c \times s_{i,c}
$$

- `w_c` – trọng số tiêu chí `c` (được lấy từ bảng `decision_criteria`).
- `s_{i,c}` – điểm tiêu chí `c` của phương án `i` (được chuẩn hoá trong `scoring.py`).

Nếu một phương án vi phạm **Hard‑Constraint**, nó sẽ không đi vào bước scoring và được đưa vào `excluded_candidates` với lý do chi tiết.

## 2. Kiến trúc / Luồng dữ liệu

```mermaid
flowchart TD
    A[API Router] -->|request| B[Service]
    B --> C[Repository (DB queries)]
    C --> D[Engine.pipeline.evaluate_decision]
    D -->|filter_and_explain| E[engine.filters (Python)]
    E -->|valid / excluded| F[engine.scoring]
    F --> G[engine.calculator (WSM)]
    G --> H[engine.ranking]
    H --> I[Response] --> Frontend
```

- **Backend** (FastAPI) nhận request, gọi `service.build_*_constraints`, lấy candidates từ `repository`, sau đó đưa vào pipeline.
- **Frontend** hiển thị danh sách xếp hạng, biểu đồ đóng góp điểm (`criteria-chart.js`) và giải thích lý do loại.

## 3. Yêu cầu hệ thống

| Thành phần            | Yêu cầu                                                                                                     |
| --------------------- | ----------------------------------------------------------------------------------------------------------- |
| Python                | ≥ 3.10                                                                                                      |
| Node (đối với dev FE) | ≥ 20                                                                                                        |
| DB                    | MySQL 8 (hoặc SQLite cho test)                                                                              |
| Các gói Python        | `fastapi`, `sqlalchemy>2.0`, `pydantic>2.0`, `uvicorn`, `pytest`, `ruff` … (xem `backend/requirements.txt`) |
| Các gói Node          | `serve` (nếu dùng Live Server)                                                                              |

## 4. Cài đặt môi trường

```bash
# 1. Clone repository
git clone https://github.com/huydat-tran/DecisionHub
cd DecisionHub

# 2. Tạo và kích hoạt virtualenv (Windows)
python -m venv backend/.venv
backend\.venv\Scripts\activate

# 3. Cài dependencies
pip install -r backend/requirements.txt

# 4. Tạo .env từ mẫu
copy backend\.env.example backend\.env
#   → mở backend\.env và chỉnh sửa MYSQL_PASSWORD, SECRET_KEY, v.v.

# 5. Khởi tạo DB (MySQL)
#   Tạo database decisionhub
mysql -u root -p -e "CREATE DATABASE decisionhub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
#   Chạy migration alembic
alembic -c backend/alembic.ini upgrade head

# 6. Nạp dữ liệu mẫu (WSM criteria, hard‑constraints, food seed)
python <<PY
from backend.app.modules.decision.mock_data import seed_all
from backend.app.modules.decision.repository import get_db
db = get_db()
seed_all(db)
PY

# 7. Kiểm tra kết nối
uvicorn backend/app/main:app --reload
#   Truy cập http://localhost:8000/docs để xem OpenAPI
```

## 5. Cấu hình `.env` (bảng chi tiết)

| Variable                      | Mô tả                       | Giá trị mẫu                                                      |
| ----------------------------- | --------------------------- | ---------------------------------------------------------------- |
| `DATABASE_URL`                | DSN kết nối DB (SQLAlchemy) | `mysql://decision_user:your_password@localhost:3306/decisionhub` |
| `MYSQL_HOST`                  | Host MySQL                  | `localhost`                                                      |
| `MYSQL_PORT`                  | Cổng MySQL                  | `3306`                                                           |
| `MYSQL_USER`                  | Người dùng DB               | `decision_user`                                                  |
| `MYSQL_PASSWORD`              | Mật khẩu DB                 | `your_password`                                                  |
| `MYSQL_DB`                    | Tên DB                      | `decisionhub`                                                    |
| `SECRET_KEY`                  | Secret dùng cho JWT         | `change_this_to_a_secure_random_value`                           |
| `ALGORITHM`                   | Thuật toán JWT              | `HS256`                                                          |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Thời gian token (phút)      | `30`                                                             |
| `FRONTEND_URL`                | URL của frontend (để CORS)  | `http://localhost:3000`                                          |
| `LOG_LEVEL`                   | Mức độ log                  | `info`                                                           |

> **Không** lưu giá trị thực tế của `SECRET_KEY` và `MYSQL_PASSWORD` trong repo.

## 6. Chạy module

### 6.1 Backend (API)

```bash
uvicorn backend/app/main:app --reload
```

- **API recommend (Food)**

```bash
curl -X POST "http://localhost:8000/api/v1/food/recommend" \
-H "Content-Type: application/json" \
-d '{
  "budget_max": 100000,
  "meal_type": "lunch",
  "max_prep_time": 30,
  "excluded_ingredients": ["peanut"]
}'
```

- **API recommend (Travel)** – tương tự, gửi tới `/api/v1/travel/recommend`.

### 6.2 Frontend

Mở `frontend/index.html` (hoặc `frontend/pages/food-results.html`) trong trình duyệt, hoặc dùng:

```bash
cd frontend
npx serve -s .
```

Giao diện sẽ:

- Hiển thị bảng xếp hạng (`ranked`), `rank`, `total_score`.
- Vẽ **biểu đồ đóng góp** (thư viện Chart.js được gọi trong `criteria-chart.js`).
- Hiển thị danh sách `excluded_candidates` với lý do chi tiết.

## 7. Chạy test

```bash
cd backend
pytest -q
```

- Các test nằm trong `backend/app/modules/decision/tests/`.
- Test quan trọng:
  - `test_wsm_verification.py` – kiểm tra công thức WSM tính tay.
  - `test_scoring_and_exclusions.py` – trường hợp trọng số không cộng bằng 1, loại do constraints.
  - `test_ranking.py` – đồng điểm, tie‑break.
  - `test_pipeline.py` – luồng pipeline cho Food.
  - `test_travel_adapter.py` & `test_travel_pipeline_reuse.py` – tái sử dụng pipeline cho Travel.

## 8. Tái sử dụng pipeline cho Travel

- Domain `travel` có **các bảng** `travel_places`, `travel_criteria`, `travel_hard_constraints`.
- `service.build_travel_constraints()` tạo dict constraints tương tự `build_food_constraints`.
- Gọi **cùng** hàm `engine.pipeline.evaluate_decision` với `domain="travel"` – pipeline tự động lấy criteria, hard‑constraints từ DB, áp dụng WSM, ranking.
- Frontend `travel-result.js` nhận cùng cấu trúc JSON (`valid_candidates`, `excluded_candidates`, `total_score`, …) và hiển thị.

## 9. Các lỗi thường gặp & cách khắc phục

| Lỗi                                                              | Nguyên nhân                                                                  | Giải pháp                                                                                                           |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: No module named 'app.modules.decision'`    | Virtualenv chưa được kích hoạt hoặc `PYTHONPATH` không bao gồm `backend/app` | Kích hoạt virtualenv và chạy `export PYTHONPATH=$(pwd)/backend/app` (Windows: `set PYTHONPATH=%cd%\\backend\\app`). |
| `OperationalError: (1045, "Access denied for user …")`           | Thông tin DB trong `.env` không đúng                                         | Kiểm tra `MYSQL_USER`, `MYSQL_PASSWORD`, chắc chắn user có quyền trên DB.                                           |
| `ImportError: cannot import name 'filter_food_candidates_in_db'` | Repo đã được revert – hàm vẫn tồn tại trong `repository.py`                  | Đảm bảo bạn đang chạy mã hiện tại, không có thay đổi chưa commit.                                                   |
| `AttributeError: 'NoneType' object has no attribute 'price'`     | Không có dữ liệu mẫu (seed chưa chạy)                                        | Chạy script seed trong **Bước 4** hoặc tạo dữ liệu thủ công trong DB.                                               |
| Test **timeout** hoặc `ImportError` khi chạy `pytest`            | Thiếu migration hoặc DB chưa khởi tạo                                        | Thực hiện các lệnh `alembic upgrade head` và `seed_all` trước khi chạy test.                                        |
| `SyntaxError` trong file `.env.example`                          | Định dạng `.env` không đúng (có dấu ngoặc kép thừa)                          | Đảm bảo mỗi dòng có dạng `KEY=VALUE` không có dấu `'` hoặc `"` quanh giá trị.                                       |
