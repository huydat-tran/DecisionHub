# DecisionHub Admin Console

Giao diện quản trị độc lập với giao diện người dùng (`frontend/pages`). Xây dựng bằng HTML5 + CSS3 + Vanilla JS, Bootstrap 5.0.2 (chỉ dùng grid / modal), SweetAlert2.

## 1. Cấu trúc thư mục

```
frontend/admin/
├── pages/
│   ├── dashboard.html     # Tổng quan
│   ├── foods.html         # Quản lý món ăn
│   └── places.html        # Quản lý địa điểm du lịch
├── css/
│   ├── admin-variables.css   # Design tokens (màu, bo góc, shadow, layout)
│   ├── admin-layout.css      # Sidebar, Header, Main, responsive
│   ├── admin-components.css  # Button, Card, Form, Table, Badge, Modal, Toast
│   └── admin-pages.css       # Riêng Dashboard (hero, stat, activity, quick access)
└── js/
    ├── layout.js          # Chèn Sidebar + Header dùng chung + xử lý menu mobile
    ├── common.js          # Toast, hộp thoại xác nhận, validate form
    ├── store.js           # Lớp dữ liệu tạm (thay bằng API ở giai đoạn sau)
    └── pages/
        ├── dashboard.js
        ├── foods.js
        └── places.js
```

## 2. Chạy thử

Mở bằng Live Server tại `frontend/admin/pages/dashboard.html`, hoặc serve thư mục `frontend/`:

```
cd frontend
python -m http.server 5501
# http://127.0.0.1:5501/admin/pages/dashboard.html
```

## 3. Trạng thái dữ liệu ở giai đoạn hiện tại

- **Chưa tích hợp API.** `js/store.js` giả lập nguồn dữ liệu bằng mảng in-memory, lưu trong `sessionStorage` nên dữ liệu tồn tại xuyên suốt phiên trình duyệt.
- Danh mục khởi tạo **rỗng** — giao diện hiển thị empty state thật, không dùng bản ghi giả.
- Mọi thông báo sau khi thêm / sửa / xoá đều ghi rõ "chưa ghi xuống máy chủ".

**Khi tích hợp API:** chỉ cần thay phần thân các hàm `admStore*` trong `js/store.js` (đổi `sessionStorage` sang request API). Phần UI không cần viết lại.

## 4. Cấu trúc dữ liệu dùng trong form

Field của form bám sát model hiện có, không thêm field mới.

**Food** (`backend/app/modules/food/models_food.py`):
`name`, `description`, `price`, `meal_type` (breakfast/lunch/dinner/snack), `prep_time`, `image_url`, `tags`, `ingredients`, `is_active`.

**TravelPlace** (`backend/app/modules/travel/models.py`):
`name`, `province_city`, `region` (Bắc/Trung/Nam/Tây Nguyên/Tây Nam Bộ), `activity_type`, `estimated_cost`, `estimated_duration`, `rating`, `description`, `highlights`, `image_url`, `is_active`.

## 5. Kiểm thử

```
node frontend/tests/admin-store.test.js
```

## 6. Quy tắc bắt buộc khi sửa

- Không dùng thuộc tính `onclick` hay JavaScript inline trong HTML.
- Mọi dữ liệu chèn bằng `innerHTML` phải bọc `escapeHtml(...)` (dùng lại `frontend/js/utils.js`).
- CSS dùng tiền tố class `adm-` để không xung đột với giao diện người dùng.
