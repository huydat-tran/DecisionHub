# BÁO CÁO KẾT QUẢ KIỂM THỬ MODULE FOOD – DECISIONHUB

---

## A. Thông tin kiểm thử

| Hạng mục | Chi tiết |
|---|---|
| **Dự án** | DecisionHub – Modular Monolith (FastAPI + SQLAlchemy 2.x + MySQL 8) |
| **Module kiểm thử** | `backend/app/modules/food/` (`router_food.py`, `services.py`, `repository_food.py`, `schemas_food.py`, `models_food.py`) |
| **Ngày kiểm thử** | 28/11/2026 |
| **Môi trường** | Windows, Python 3.14, FastAPI `TestClient(app)`, MySQL 8 (`decision_hub`, `utf8mb4`) |
| **Phạm vi kiểm thử** | Toàn bộ 5 endpoint CRUD `/api/v1/food`, validation dữ liệu đầu vào, quản lý nguyên liệu `food_ingredients`, phân tách trạng thái `is_active` giữa trang người dùng và Admin |

### Danh sách API được kiểm thử

| STT | Method | Endpoint | Mục đích |
|---|---|---|---|
| 1 | `GET` | `/api/v1/food` | Lấy danh sách món ăn công khai (`include_inactive=false`) và quản trị (`include_inactive=true`) |
| 2 | `GET` | `/api/v1/food/{food_id}` | Xem chi tiết món ăn theo ID |
| 3 | `POST` | `/api/v1/food` | Tạo món ăn mới kèm `tags` và `ingredients` |
| 4 | `PUT` | `/api/v1/food/{food_id}` | Cập nhật thông tin, trạng thái và nguyên liệu món ăn |
| 5 | `DELETE` | `/api/v1/food/{food_id}` | Xoá món ăn theo ID |

---

## B. Kết quả tổng hợp

| Chỉ số | Số lượng | Tỷ lệ |
|---|---|---|
| **Tổng số Test Case** | **11** | 100% |
| **Passed** | **11** | **100%** |
| **Failed** | **0** | 0% |
| **Blocked / Not Run** | **0** | 0% |
| **Lỗi (Bug) còn tồn đọng** | **0** | Không có |

---

## C. Bảng Test Case chi tiết (TC01 – TC11)

| TC ID | Nhóm | Mô tả kiểm thử | Input / Điều kiện | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| **TC01** | Read List | Lấy danh sách món ăn công khai | `GET /api/v1/food` | HTTP `200 OK`, `success=true`, toàn bộ phần tử có `is_active=true`. | HTTP `200 OK`, trả về `10` món đang hoạt động (món đầu: `Phở bò tái`), 100% có `is_active=true`. | **PASSED** |
| **TC02** | Read Detail | Xem chi tiết món ăn đang hoạt động | `GET /api/v1/food/1` | HTTP `200 OK`, trả đủ thông tin món kèm mảng `ingredients` và `tags`. | HTTP `200 OK`, `id=1`, `name="Phở bò tái"`, `3` nguyên liệu, `tags=["nước", "truyền thống", "nóng"]`. | **PASSED** |
| **TC03** | Read Detail | Xem chi tiết ID không tồn tại | `GET /api/v1/food/999999` | HTTP `404 Not Found`, `success=false`, `error_code="RESOURCE_NOT_FOUND"`. | HTTP `404 Not Found`, `error_code="RESOURCE_NOT_FOUND"`, `message="Món ăn với mã 999999 không tồn tại."`. | **PASSED** |
| **TC04** | Validation | Xem chi tiết với `food_id <= 0` | `GET /api/v1/food/0` | HTTP `422 Unprocessable Entity`, `error_code="VALIDATION_ERROR"`. | HTTP `422`, `error_code="VALIDATION_ERROR"`. | **PASSED** |
| **TC05** | Create | Tạo món ăn mới hợp lệ (`is_active=false`, nguyên liệu mới + cũ, tag trùng hoa/thường) | `POST /api/v1/food` với `name="Bún bò Huế test"`, `price=52000`, `meal_type="lunch"`, `tags=["cay", "nước", "Cay"]`, `ingredients=[{"name": "Thịt bò"}, {"name": "Nguyên liệu kiểm thử tạm"}]`, `is_active=false` | HTTP `201 Created`, tự lọc trùng tag còn `["cay", "nước"]`, liên kết đủ 2 nguyên liệu (tái sử dụng `Thịt bò`, tạo mới `Nguyên liệu kiểm thử tạm`). | HTTP `201 Created`, `id=13`, `tags=["cay", "nước"]`, `ingredients=["Thịt bò", "Nguyên liệu kiểm thử tạm"]`, `is_active=false`. | **PASSED** |
| **TC06** | Visibility | Ẩn món tạm ngưng ở trang người dùng, hiện ở trang Admin | Gọi `GET /api/v1/food`, `GET /api/v1/food?include_inactive=true`, `GET /api/v1/food/13`, `GET /api/v1/food/13?include_inactive=true` | Public list không chứa ID `13` (`count=10`), public detail trả `404`; Admin list có ID `13`, Admin detail trả `200 OK`. | `public_count=10`, `admin_has_id=True`, `detail_pub=404`, `detail_adm=200`. | **PASSED** |
| **TC07** | Validation | Chặn dữ liệu không hợp lệ khi tạo mới | `POST /api/v1/food` lần lượt với: `price=-5000`; `meal_type="brunch"`; `image_url="ftp://x.jpg"`; thừa trường `unknown=1` | Cả 4 request trả HTTP `422` (`VALIDATION_ERROR`). | Cả 4 request đều trả `[422, 422, 422, 422]`. | **PASSED** |
| **TC08** | Update | Cập nhật thông tin, nguyên liệu và kích hoạt lại món ăn | `PUT /api/v1/food/13` đổi `name="Bún bò Huế đặc biệt"`, `price=58000`, `meal_type="dinner"`, `ingredients=[{"name": "Bánh phở"}]`, `is_active=true` | HTTP `200 OK`, dữ liệu cập nhật chính xác trong DB, `ingredients` chỉ còn `["Bánh phở"]`, `is_active=true`. | HTTP `200 OK`, `name="Bún bò Huế đặc biệt"`, `price=58000`, `is_active=true`, `ingredients=["Bánh phở"]`. | **PASSED** |
| **TC09** | Validation | Chặn cập nhật body rỗng hoặc ghi `null` vào trường bắt buộc | `PUT /api/v1/food/13` với `{}` và `{"price": null}` | Cả 2 request trả HTTP `400 Bad Request`. | `empty_body=400`, `null_price=400`. | **PASSED** |
| **TC10** | Delete | Xoá món ăn theo ID | `DELETE /api/v1/food/13`, sau đó gọi lại `GET /api/v1/food/13?include_inactive=true` | `DELETE` trả HTTP `200 OK` kèm `data.id=13`; `GET` lại trả `404`. | HTTP `200 OK`, `deleted_id=13`, `get_after_delete=404` (dữ liệu kiểm thử tạm đã được dọn sạch). | **PASSED** |
| **TC11** | Delete | Xoá ID không tồn tại | `DELETE /api/v1/food/999999` | HTTP `404 Not Found`, `error_code="RESOURCE_NOT_FOUND"`. | HTTP `404 Not Found`, `error_code="RESOURCE_NOT_FOUND"`. | **PASSED** |

---

## D. Phạm vi chưa kiểm thử & Rủi ro cần lưu ý

- **Phân quyền Admin:** Chưa kiểm thử trường hợp `401 Unauthorized` / `403 Forbidden` cho `POST`, `PUT`, `DELETE /api/v1/food` vì các endpoint này hiện chưa bật dependency kiểm tra JWT role `ADMIN` (đã đánh dấu `shortcut:` tại `router_food.py`).
- **Kiểm thử giao diện trực quan (Browser E2E):** Báo cáo này xác minh toàn bộ tầng Backend API + MySQL; chưa chạy kiểm thử bấm giao diện trực tiếp trên trình duyệt cho `frontend/pages/food.html` và `frontend/admin/pages/foods.html`.
- **Linter tĩnh:** Môi trường shell hiện chưa cài `ruff` / `pyright` CLI nên chưa chạy tự động từ dòng lệnh (đã kiểm tra cú pháp bằng `python -m py_compile`).
