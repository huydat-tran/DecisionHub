# Module Food – DecisionHub Backend

Phân hệ **Food (WhatShouldIEat)** quản lý danh mục món ăn, nguyên liệu và cung cấp API CRUD phục vụ cả giao diện người dùng (`frontend/pages/food.html`) lẫn trang quản trị (`frontend/admin/pages/foods.html`).

---

## 1. Cấu trúc thư mục

```text
backend/app/modules/food/
├── models_food.py       # SQLAlchemy 2.x models: Food, Ingredient, FoodIngredient
├── schemas_food.py      # Pydantic v2 schemas & validators (FoodOut, FoodCreate, FoodUpdate, ...)
├── repository_food.py   # Tầng truy vấn MySQL (foods & ingredients)
├── services.py          # Nghiệp vụ CRUD, kiểm tra dữ liệu và quản lý transaction
├── router_food.py       # FastAPI APIRouter (/api/v1/food)
├── README.md            # Tài liệu module
└── TEST_REPORT.md       # Báo cáo kết quả kiểm thử API Food
```

**Luồng xử lý chuẩn:**

```text
Frontend / Admin --HTTP--> router_food.py --> services.py --> repository_food.py --> MySQL
```

---

## 2. Mô hình dữ liệu (`models_food.py`)

| Bảng | Vai trò | Cột chính | Ràng buộc |
|---|---|---|---|
| `foods` | Lưu thông tin món ăn | `id`, `name`, `description`, `price` (VND), `meal_type`, `prep_time` (phút), `image_url`, `tags` (JSON), `is_active`, `created_at` | `price >= 0`, `prep_time >= 0` |
| `ingredients` | Danh mục nguyên liệu dùng chung | `id`, `name` | `name` là `UNIQUE` |
| `food_ingredients` | Bảng trung gian N–N giữa `foods` và `ingredients` | `food_id`, `ingredients_id` | `ON DELETE CASCADE` |

- `meal_type` hợp lệ: `breakfast`, `lunch`, `dinner`, `snack`.
- `tags` lưu mảng JSON (VD: `["nước", "truyền thống", "nóng"]`), tự loại khoảng trắng và phần tử trùng không phân biệt hoa thường.
- `ingredients` khi tạo/cập nhật chấp nhận cả dạng `["Thịt bò", "Hành lá"]` lẫn `[{"name": "Thịt bò"}]`; hệ thống tự tái sử dụng nguyên liệu có sẵn trong bảng `ingredients` hoặc tạo mới nếu chưa tồn tại.

---

## 3. Danh sách API (`router_food.py`)

Tiền tố chung: `/api/v1/food`

| Method | Endpoint | Query / Body | HTTP Status | Mô tả |
|---|---|---|---|---|
| `GET` | `/api/v1/food` | `?include_inactive=false\|true` | `200 OK` | Lấy danh sách món ăn. Mặc định `false` (chỉ món `is_active = true` cho người dùng); truyền `true` để lấy toàn bộ cho Admin. |
| `GET` | `/api/v1/food/{food_id}` | `?include_inactive=false\|true` | `200 OK` / `404` / `422` | Xem chi tiết món ăn kèm `ingredients` và `tags`. |
| `POST` | `/api/v1/food` | JSON `FoodCreate` | `201 Created` / `422` | Thêm món ăn mới kèm nhãn và nguyên liệu. |
| `PUT` | `/api/v1/food/{food_id}` | JSON `FoodUpdate` | `200 OK` / `400` / `404` / `422` | Cập nhật thông tin món ăn (cho phép cập nhật toàn bộ hoặc một phần trường). |
| `DELETE` | `/api/v1/food/{food_id}` | — | `200 OK` / `404` | Xoá món ăn theo ID (tự xoá liên kết trong `food_ingredients`). |

### Ví dụ payload `POST /api/v1/food`

```json
{
  "name": "Phở bò tái",
  "price": 45000,
  "meal_type": "breakfast",
  "prep_time": 15,
  "description": "Nước dùng ninh xương ngọt thanh, thịt bò tái mềm.",
  "image_url": "https://example.com/pho.jpg",
  "tags": ["nước", "truyền thống", "nóng"],
  "ingredients": ["Bánh phở", "Thịt bò", "Hành lá"],
  "is_active": true
}
```

### Cấu trúc Response chuẩn

- **Thành công:** `{"success": true, "message": "...", "data": ...}`
- **Lỗi (chuẩn `app/common/exceptions.py`):** `{"success": false, "message": "...", "data": ..., "error_code": "...", "errors": ..., "path": "..."}`

---

## 4. Khởi chạy & Dữ liệu mẫu

Chạy từ thư mục `backend/`:

```bash
# 1. Tạo bảng theo migration Alembic
alembic upgrade head

# 2. Nạp dữ liệu mẫu món ăn & nguyên liệu (an toàn khi chạy lại nhiều lần)
mysql -u root -p decision_hub < sql/seeds/foods.sql

# 3. Khởi động API server
python -m uvicorn app.main:app --reload
```

Tài liệu tương tác Swagger UI: `http://127.0.0.1:8000/docs`

---

## 5. Giới hạn & Lưu ý hiện tại

- **Phân quyền Admin (`shortcut`):** Các endpoint ghi dữ liệu (`POST`, `PUT`, `DELETE /api/v1/food`) hiện chưa gắn dependency kiểm tra JWT role `ADMIN` vì `frontend/admin/` chưa tích hợp luồng đăng nhập. Cần bổ sung kiểm tra quyền `ADMIN` ngay khi Admin Console nối với `/auth/login`.
- **Gợi ý WSM (Recommendation):** Logic gợi ý món ăn theo tiêu chí thuộc module `app/modules/decision/` (`POST /api/v1/decisions/food/recommend`), tách biệt khỏi CRUD danh mục tại module `food`.
