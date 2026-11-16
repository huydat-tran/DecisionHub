# Backend DecisionHub

Backend của DecisionHub, kiến trúc **Modular Monolith** (FastAPI + MySQL).

## 1. Yêu cầu môi trường

| Thành phần | Ghi chú |
|---|---|
| Python 3.10+ | Kiểm tra: `python --version` |
| MySQL Server 8 | Chưa cần cài ngay nếu chỉ chạy skeleton |

## 2. Cấu trúc thư mục

```
backend/
├── app/
│   ├── main.py                  # Khởi động FastAPI, CORS, endpoint /health
│   ├── core/
│   │   ├── config.py            # Đọc cấu hình từ .env (pydantic-settings)
│   │   ├── database.py          # engine, SessionLocal, Base, get_db
│   │   └── security.py          # Chỗ dành cho JWT / password hashing (chưa dùng)
│   ├── common/
│   │   ├── exceptions.py        # Exception gốc + handler chuẩn hóa
│   │   └── responses.py         # Định dạng response thống nhất
│   └── modules/
│       ├── auth/                # Module nghiệp vụ (chưa triển khai)
│       ├── users/               # Module Users (models.py: Role, User)
│       ├── food/
│       ├── travel/
│       ├── decision/            # Chứa Decision Engine nội bộ
│
├── alembic/                     # Alembic migrations (tạo/thay đổi cấu trúc bảng)
│   ├── env.py
│   └── versions/                # Các file migration
├── alembic.ini
├── sql/
│   ├── init.sql                 # Tạo database decision_hub
│   └── seeds/                   # Dữ liệu mẫu
│       └── users.sql            # Seed roles + users
├── .env                         # Cấu hình máy phát triển (KHÔNG commit)
├── .env.example                 # Mẫu cấu hình
└── requirements.txt
```

Luồng xử lý một request:

```
Frontend --HTTP--> modules/<module>/router.py --> service.py --> repository.py --> MySQL
                     (validate bằng schemas.py, model trong models.py)
```

## 3. Cài đặt và chạy

```bash
cd backend

# Tạo môi trường ảo (1 lần)
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # Mac/Linux

# Cài thư viện
pip install -r requirements.txt

# Tạo file .env
copy .env.example .env            # Windows
# cp .env.example .env            # Mac/Linux
# Sửa DB_USER / DB_PASSWORD / DB_NAME cho đúng máy

# Chạy server (từ thư mục backend)
uvicorn app.main:app --reload
```

Tài liệu API: http://127.0.0.1:8000/docs

## 4. Kiểm tra

| Kiểm tra | Kết quả mong đợi |
|---|---|
| `GET /health` | `{"success": true, "message": "OK", "data": {"app": "DecisionHub", "status": "ok"}}` |
| `GET /docs` | Trang Swagger UI |

## 5. Cấu hình `.env`

| Biến | Ý nghĩa | Mặc định |
|---|---|---|
| `APP_NAME` | Tên ứng dụng | `DecisionHub` |
| `DB_HOST` | Host MySQL | `127.0.0.1` |
| `DB_PORT` | Cổng MySQL | `3306` |
| `DB_USER` | Tài khoản MySQL | `root` |
| `DB_PASSWORD` | Mật khẩu MySQL | (rỗng) |
| `DB_NAME` | Tên database | `decision_hub` |
| `CORS_ORIGINS` | Origin được phép gọi API, cách nhau bằng dấu phẩy | `*` |

Sửa `.env` xong phải tắt (`Ctrl + C`) và chạy lại uvicorn.

## 6. Database: tạo cấu trúc bảng và dữ liệu mẫu

Ba bước độc lập, theo đúng thứ tự:

```bash
cd backend
```

**Bước 1 — Tạo database** (`sql/init.sql` chỉ tạo database, không tạo bảng):

```bash
mysql -u root -p < sql/init.sql
```

**Bước 2 — Tạo cấu trúc bảng** bằng Alembic (đọc `DB_*` từ `.env`):

```bash
alembic upgrade head
```

Sinh migration mới sau khi đổi `models.py`:

```bash
alembic revision --autogenerate -m "mô tả thay đổi"
```

**Bước 3 — Nạp dữ liệu mẫu** (`sql/seeds/`):

```bash
mysql -u root -p decision_hub < sql/seeds/users.sql
mysql -u root -p decision_hub < sql/seeds/foods.sql
mysql -u root -p decision_hub < sql/seeds/travel_places.sql
mysql -u root -p decision_hub < sql/seeds/decision_criteria.sql
mysql -u root -p decision_hub < sql/seeds/hard_constraints.sql
```

Các file seed đều dùng `INSERT IGNORE` hoặc `WHERE NOT EXISTS` nên
**chạy lại nhiều lần không tạo bản ghi trùng**.

| Nội dung | Ở đâu |
|---|---|
| Cấu trúc bảng | Alembic — `alembic/versions/` |
| Dữ liệu mẫu | `sql/seeds/` |
| Tạo database | `sql/init.sql` |

Tài khoản mẫu (mật khẩu dev `Password@123`, hash bcrypt):

| Email | Role |
|---|---|
| user1@example.com | USER |
| user2@example.com | USER |
| admin@example.com | ADMIN |
| admin2@example.com | ADMIN |

## 7. Lỗi hay gặp

| Lỗi | Cách sửa |
|---|---|
| `Error loading ASGI app. Could not import module "app.main"` | Đang đứng sai thư mục. Phải `cd` vào `backend/` rồi mới chạy uvicorn |
| `ModuleNotFoundError: No module named 'fastapi'` | Chưa kích hoạt `.venv` hoặc chưa `pip install -r requirements.txt` |
| `Access denied for user 'root'@'localhost'` | Sai `DB_PASSWORD` trong `.env` |
| `Can't connect to MySQL server on '127.0.0.1'` | MySQL chưa bật. Kiểm tra lại `DB_PORT` |
| Cổng 8000 đã bị dùng | `uvicorn app.main:app --reload --port 8001` |
| Tiếng Việt bị lỗi font trong DB | Database/bảng phải dùng `utf8mb4` (xem `sql/init.sql`) |
