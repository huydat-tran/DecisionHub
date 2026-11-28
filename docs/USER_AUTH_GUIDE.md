# DecisionHub - Hướng dẫn Module User/Auth

Tài liệu cài đặt môi trường, cấu hình `.env`, chạy và kiểm thử module **User/Auth**
(đăng ký, đăng nhập, xem/cập nhật hồ sơ cá nhân, xác thực JWT).

## 1. Giới thiệu module

Module **User/Auth** xử lý toàn bộ vòng đời xác thực và quản lý hồ sơ cá nhân của người dùng trong DecisionHub.

| Endpoint | Method | Mục đích | Xác thực |
|---|---|---|---|
| `/auth/register` | POST | Tạo tài khoản mới | Không |
| `/auth/login` | POST | Đăng nhập, nhận access token JWT | Không |
| `/users/me` | GET | Lấy thông tin hồ sơ tài khoản hiện tại | Bearer token |
| `/users/me` | PATCH | Cập nhật hồ sơ tài khoản hiện tại | Bearer token |

### 1.1. Định dạng response

Mọi response (thành công và lỗi) đều dùng cùng một cấu trúc chung do `app/common/exceptions.py` chuẩn hóa:

```json
{
  "success": true,
  "message": "...",
  "data": {}
}
```

Response lỗi bổ sung thêm `error_code`, `errors` và `path`:

```json
{
  "success": false,
  "message": "Email hoặc mật khẩu không đúng.",
  "data": null,
  "error_code": "UNAUTHORIZED",
  "errors": null,
  "path": "/auth/login"
}
```

Mã lỗi thường gặp: `BAD_REQUEST` (400), `UNAUTHORIZED` (401), `FORBIDDEN` (403),
`NOT_FOUND` (404), `CONFLICT` (409), `VALIDATION_ERROR` (422), `INTERNAL_SERVER_ERROR` (500).

### 1.2. Các file quan trọng của module

| File | Vai trò |
|---|---|
| `backend/app/modules/auth/router.py` | Khai báo API `/auth/register`, `/auth/login` |
| `backend/app/modules/auth/schemas.py` | Pydantic schema: `RegisterRequest`, `LoginRequest`, `TokenData` |
| `backend/app/modules/auth/service.py` | Nghiệp vụ đăng ký / đăng nhập |
| `backend/app/modules/auth/dependencies.py` | Dependency `get_current_user` xác thực Bearer token |
| `backend/app/modules/users/router.py` | Khai báo API `/users/me` (GET, PATCH) |
| `backend/app/modules/users/schemas.py` | `UserProfile`, `UpdateProfileRequest`, `ProfileResponse` |
| `backend/app/modules/users/service.py` | Nghiệp vụ đọc / cập nhật hồ sơ |
| `backend/app/modules/users/repository.py` | Truy vấn bảng `users` và `roles` |
| `backend/app/modules/users/models.py` | SQLAlchemy models `Role`, `User` |
| `backend/app/core/security.py` | Hash bcrypt + tạo/kiểm tra JWT access token |
| `backend/app/core/config.py` | Đọc cấu hình từ `.env` |
| `backend/app/common/exceptions.py` | Chuẩn hóa response lỗi |

### 1.3. Luồng xử lý

```
Client → router.py (validate bằng schemas.py) → service.py → repository.py → MySQL
```

## 2. Yêu cầu môi trường

| Thành phần | Yêu cầu | Cách kiểm tra |
|---|---|---|
| Python | 3.10 trở lên (khuyến nghị 3.11+) | `python --version` |
| MySQL Server | 8.0 trở lên | `mysql --version` |
| pip | đi kèm Python | `pip --version` |
| MySQL client (không bắt buộc) | để chạy `sql/init.sql` và các file seed | `mysql --version` |

Mã nguồn module User/Auth chỉ cần FastAPI, SQLAlchemy 2.x, PyMySQL, bcrypt, PyJWT,
pydantic v2 và pydantic-settings — tất cả đều nằm trong `backend/requirements.txt`.

> Môi trường đã dùng để kiểm tra tài liệu này: **Python 3.14.8**, **MySQL 8.0.46**,
> uvicorn chạy trên `127.0.0.1:8000`.

## 3. Hướng dẫn cài đặt

Tất cả lệnh dưới đây chạy trong thư mục `backend/`.

### Bước 1 — Tạo và kích hoạt virtual environment

```bash
cd backend

python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate       # Mac/Linux
```

> PowerShell có thể chặn `Activate.ps1`. Sửa bằng:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Bước 2 — Cài dependencies

```bash
pip install -r requirements.txt
```

### Bước 3 — Tạo file `.env`

```bash
copy .env.example .env              # Windows
# cp .env.example .env              # Mac/Linux
```

Sửa `DB_USER` / `DB_PASSWORD` cho khớp MySQL của máy (chi tiết ở mục 4).

### Bước 4 — Tạo database

`sql/init.sql` chỉ tạo database, không tạo bảng:

```bash
mysql -u root -p < sql/init.sql
```

### Bước 5 — Tạo cấu trúc bảng bằng Alembic

Alembic đọc `DB_*` từ `.env` (xem `backend/alembic/env.py`):

```bash
alembic upgrade head
```

### Bước 6 — Nạp dữ liệu mẫu (bắt buộc cho module Auth)

Module Auth **cần** bảng `roles` và dữ liệu seed vai trò. Nếu thiếu role `USER`
thì đăng ký sẽ trả về 500.

```bash
mysql -u root -p decision_hub < sql/seeds/users.sql
```

File seed dùng `INSERT IGNORE` / `WHERE NOT EXISTS` nên chạy lại nhiều lần không sinh bản ghi trùng.

## 4. Cấu hình `.env`

File `.env` nằm ở `backend/.env`, được đọc bởi `app/core/config.py` (pydantic-settings).
File này đã có trong `.gitignore` — **không commit**.

### 4.1. Biến môi trường thực tế

| Biến | Ý nghĩa | Mặc định | Ví dụ mẫu |
|---|---|---|---|
| `APP_NAME` | Tên ứng dụng, dùng cho tiêu đề Swagger | `DecisionHub` | `DecisionHub` |
| `DB_HOST` | Host MySQL | `127.0.0.1` | `127.0.0.1` |
| `DB_PORT` | Cổng MySQL | `3306` | `3306` |
| `DB_USER` | Tài khoản MySQL | `root` | `root` |
| `DB_PASSWORD` | Mật khẩu MySQL | (rỗng) | `<mat-khau-cua-ban>` |
| `DB_NAME` | Tên database | `decision_hub` | `decision_hub` |
| `CORS_ORIGINS` | Danh sách origin được phép gọi API, cách nhau bằng dấu phẩy | `*` | `http://127.0.0.1:5500,http://localhost:5500` |
| `JWT_SECRET_KEY` | Key ký/kiểm tra access token | *(sinh tự động)* | `<chuoi-ngau-nhien-32-bytes>` |
| `JWT_ALGORITHM` | Thuật toán ký JWT | `HS256` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Thời gian hết hạn access token (phút) | `60` | `60` |

### 4.2. Giải thích từng biến

- `DB_*`: `Settings.database_url` ghép thành chuỗi `mysql+pymysql://...` kèm `charset=utf8mb4`.
  Mật khẩu có ký tự đặc biệt sẽ được `quote_plus` hóa đúng cách.
- `CORS_ORIGINS`: dùng cho `CORSMiddleware` trong `app/main.py`. `*` là cho phép tất cả
  (tiện khi dev). Khi deploy thật chỉ ghi domain frontend thực tế.
- `JWT_SECRET_KEY`: **nên đặt khi dev** nếu muốn token còn hiệu lực sau khi restart server.
  Nếu để trống, `Settings` tự sinh key tạm cho tiến trình hiện tại, nên token cũ mất
  hiệu lực sau mỗi lần restart.
- `JWT_ALGORITHM`: thuật toán dùng cho cả `jwt.encode` và `jwt.decode`.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: `create_access_token` dùng giá trị này để tính `exp` của JWT.

### 4.3. Ví dụ file `.env` hoàn chỉnh (không chứa thông tin nhạy cảm thật)

```dotenv
APP_NAME=DecisionHub

# ---- MySQL ----
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=<mat-khau-cua-ban>
DB_NAME=decision_hub

# ---- CORS ----
CORS_ORIGINS=*

# ---- JWT ----
# Sinh key ngẫu nhiên:
#   python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=<32-bytes-ngau-nhien>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Sau khi sửa `.env`, phải tắt uvicorn (`Ctrl + C`) và chạy lại, vì `settings` được đọc
một lần lúc import.

## 5. Hướng dẫn chạy module

### 5.1. Khởi động backend

```bash
cd backend
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # Mac/Linux

uvicorn app.main:app --reload
```

Các biến thể:

| Lệnh | Dùng khi |
|---|---|
| `uvicorn app.main:app --reload` | Dev, tự động reload khi sửa code |
| `uvicorn app.main:app --reload --port 8001` | Cổng 8000 đã bị dùng |
| `uvicorn app.main:app` | Production / kiểm tra nhanh |

> Phải `cd` vào `backend/` trước khi chạy, nếu không uvicorn sẽ báo
> `Error loading ASGI app. Could not import module "app.main"`.

Kiểm tra server đã lên:

```bash
curl http://127.0.0.1:8000/health
```

Kết quả mong đợi:

```json
{"success": true, "message": "OK", "data": {"app": "DecisionHub", "status": "ok"}}
```

### 5.2. Truy cập Swagger

| Đường dẫn | Nội dung |
|---|---|
| http://127.0.0.1:8000/docs | Swagger UI |
| http://127.0.0.1:8000/redoc | ReDoc |
| http://127.0.0.1:8000/openapi.json | OpenAPI schema |

Trong Swagger UI, các endpoint của module nằm ở tag **Auth** và **Users**.

### 5.3. Dùng chung token trên Swagger UI

Scheme `HTTPBearer` đã được cấu hình sẵn nên chỉ cần:

1. Bấm nút **Authorize** ở góc trên bên phải.
2. Dán `access_token` (không cần chèn `Bearer `) vào ô `value`.
3. Bấm **Authorize** rồi **Close**.

Token lấy từ `data.access_token` của response `POST /auth/login`.

## 6. Hướng dẫn kiểm thử API

Các ví dụ dưới đây dùng `curl` (Windows PowerShell: dùng `curl.exe` để tránh bị alias
của PowerShell).

### 6.1. Đăng ký tài khoản

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"nguyenvanan\", \"email\": \"nguyenvanan@example.com\", \"password\": \"Abcd@1234\"}"
```

Quy tắc dữ liệu (`app/modules/auth/schemas.py`):

| Trường | Quy tắc |
|---|---|
| `username` | Bắt buộc, duy nhất, 5–50 ký tự |
| `email` | Bắt buộc, định dạng email hợp lệ, duy nhất |
| `password` | Bắt buộc, tối thiểu 8 ký tự, có ít nhất 1 chữ in hoa và 1 ký tự đặc biệt, tối đa 72 byte UTF-8 (giới hạn của bcrypt) |

Không có trường `role` trong request — client không được tự chọn vai trò, mọi tài khoản
mới luôn nhận `USER`.

Kết quả mong đợi: HTTP 201.

```json
{
  "success": true,
  "message": "Đăng ký thành công.",
  "data": {
    "id": 44,
    "username": "nguyenvanan",
    "email": "nguyenvanan@example.com",
    "role": "USER",
    "created_at": "2026-11-27T20:56:29"
  }
}
```

### 6.2. Đăng nhập

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"nguyenvanan@example.com\", \"password\": \"Abcd@1234\"}"
```

Kết quả mong đợi: HTTP 200, `data.access_token` là JWT, `data.token_type` là `bearer`.

```json
{
  "success": true,
  "message": "Đăng nhập thành công.",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 44,
      "username": "nguyenvanan",
      "email": "nguyenvanan@example.com",
      "role": "USER",
      "created_at": "2026-11-27T20:56:29"
    }
  }
}
```

### 6.3. Xem hồ sơ (GET /users/me)

```bash
curl http://127.0.0.1:8000/users/me \
  -H "Authorization: Bearer <access_token>"
```

Kết quả mong đợi: HTTP 200, `data` có đúng 5 trường `id`, `username`, `email`, `role`,
`created_at` — không có `password` / `password_hash`.

### 6.4. Cập nhật hồ sơ (PATCH /users/me)

```bash
curl -X PATCH http://127.0.0.1:8000/users/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d "{\"username\": \"nguyenvanan_moi\"}"
```

Hiện tại chỉ hỗ trợ đổi `username`. Body rõng sẽ trả 400; body chứa field lạ sẽ trả 422
(schema dùng `extra="forbid"`).

### 6.5. Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| 401 `Không có quyền truy cập. Vui lòng đăng nhập.` | Thiếu `Authorization` header | Đăng nhập lại và dán token |
| 401 `Access token không hợp lệ hoặc đã hết hạn.` | Token sai / hết hạn / user không còn tồn tại | Đăng nhập lại |
| 409 `Email đã được đăng ký.` | Email trùng | Đổi email |
| 409 `Username đã được sử dụng.` | Username trùng | Đổi username |
| 422 `Dữ liệu đầu vào không hợp lệ` | Sai quy tắc validation | Xem `errors[].field` |
| 400 `Không có trường nào được cập nhật.` | PATCH body rỗng | Gửi `{"username": "..."}` |
| 500 `Không tìm thấy vai trò 'USER'` | Chưa nạp seed `sql/seeds/users.sql` | Nạp lại seed |

## 7. Bảng tổng hợp kết quả kiểm thử

### 7.1. Điều kiện kiểm thử

| Hạng mục | Giá trị |
|---|---|
| Ngày kiểm thử | 27/11/2026 |
| Backend | `uvicorn app.main:app` trên `http://127.0.0.1:8000` |
| Database | MySQL 8.0.46, schema `decision_hub` (đã `alembic upgrade head` + nạp seed `users.sql`) |
| Cách kiểm thử | Gọi HTTP trực tiếp bằng `httpx` vào server đang chạy, đối chiếu status code và body thực tế |
| Tài khoản thử nghiệm | `e2e_auth_tester` / `e2e.auth.tester@example.com`, mật khẩu `Abcd@1234` |

> **Lưu ý**: môi trường kiểm thử có chạy MySQL thật với dữ liệu mẫu sẵn có.
> Các tài khoản thử nghiệm đã được xoá sạch sau khi kiểm thử.

### 7.2. Kết quả chi tiết

| # | Trường hợp | Mục đích kiểm thử | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|---|
| 1 | Đăng ký thành công | Tạo được tài khoản mới, gán role `USER` | HTTP 201, `success=true`, `data` có id/username/email/role/created_at | HTTP 201. `data`: `{"id":44,"username":"e2e_auth_tester","email":"e2e.auth.tester@example.com","role":"USER","created_at":"2026-11-27T20:56:29"}` | **PASS** |
| 2 | Đăng ký với email đã tồn tại | Chặn trùng email, tránh tạo tài khoản trùng | HTTP 409, `error_code=CONFLICT` | HTTP 409. `{"success":false,"message":"Email đã được đăng ký.","error_code":"CONFLICT","path":"/auth/register"}` | **PASS** |
| 3 | Đăng ký với username đã tồn tại | Chặn trùng username | HTTP 409 | HTTP 409. `{"message":"Username đã được sử dụng.","error_code":"CONFLICT"}` | **PASS** |
| 4 | Đăng ký với dữ liệu không hợp lệ | Validate input: sai định dạng email, mật khẩu yếu, username ngắn, thiếu trường | HTTP 422, `error_code=VALIDATION_ERROR`, có `errors[]` chỉ rõ field | HTTP 422 ở cả 5 biến thể: email `not-an-email` → `body.email` / "value is not a valid email address"; password `abc12345` → `body.password` / "Mật khẩu phải có ít nhất 1 chữ cái in hoa."; password `Ab1@` → `body.password` / "String should have at least 8 characters"; username `abc` → `body.username` / "String should have at least 5 characters"; thiếu `password` → `body.password` / "Field required" | **PASS** |
| 5 | Đăng nhập thành công | Xác thực thông tin đúng và cấp access token | HTTP 200, `data.access_token` là JWT, `token_type=bearer` | HTTP 200. Token decode được: `{"sub":"44","type":"access","iat":1795787883,"exp":1795791483}` (exp − iat = 3600s = 60 phút) | **PASS** |
| 6 | Đăng nhập sai thông tin | Từ chối sai mật khẩu và email không tồn tại, không lộ email nào đã được đăng ký | HTTP 401, `error_code=UNAUTHORIZED`, cùng một thông điệp | HTTP 401 ở cả hai trường hợp, cùng thông điệp `"Email hoặc mật khẩu không đúng."`: sai mật khẩu → 401; email không tồn tại → 401 | **PASS** |
| 7 | Truy cập hồ sơ khi chưa đăng nhập | Bảo vệ endpoint, trả 401 khi thiếu token | HTTP 401, `error_code=UNAUTHORIZED` | HTTP 401. Không header → `"Không có quyền truy cập. Vui lòng đăng nhập."`; token tạm giả → 401 `"Access token không hợp lệ hoặc đã hết hạn."`; sai scheme (`Basic`) → 401; token hợp lệ nhưng user không tồn tại → 401 | **PASS** |
| 8 | Xem hồ sơ khi đã đăng nhập | Trả đúng thông tin tài khoản đang đăng nhập | HTTP 200, `data` đúng 5 trường | HTTP 200. `{"id":44,"username":"e2e_auth_tester","email":"e2e.auth.tester@example.com","role":"USER","created_at":"2026-11-27T20:56:29"}` | **PASS** |
| 9 | Cập nhật hồ sơ thành công | Đổi `username` và lưu xuống DB | HTTP 200, `data.username` đã đổi | HTTP 200. `username` đổi từ `e2e_auth_tester` → `e2e_auth_tester_new`; đọc lại `GET /users/me` vẫn là giá trị mới | **PASS** |
| 10 | Cập nhật với dữ liệu không hợp lệ | Validate payload cập nhật | HTTP 422 / 400 / 409 | HTTP 422 `username` ngắn ("String should have at least 5 characters"); HTTP 422 gửi field `email` → "Extra inputs are not permitted" (schema `extra="forbid"`); HTTP 400 body rỗng → `"Không có trường nào được cập nhật."`; HTTP 409 `username` trùng với tài khoản khác → `"Username đã được sử dụng."` | **PASS** |
| 11 | Response hồ sơ không trả về `password_hash` | Không lộ thông tin nhạy cảm | Response không chứa `password` / `password_hash` | PASS. Khóa của `data` = `['id','username','email','role','created_at']`. Kiểm tra chuỗi thô trên raw body: không xuất hiện `password`. Cả hai endpoint `/auth/register` và `/auth/login` cũng không trả về hash | **PASS** |

### 7.3. Kiểm thử bổ sung (ngoài danh sách yêu cầu)

| # | Trường hợp | Kết quả | Trạng thái |
|---|---|---|---|
| 12 | Client tự gửi `role` trong body đăng ký | HTTP 201 nhưng `data.role` vẫn là `USER` — client không thể tự nâng quyền | **PASS** |
| 13 | PATCH `/users/me` không có token | HTTP 401 | **PASS** |
| 14 | PATCH `/users/me` đổi `username` bằng chính username hiện tại | HTTP 200, không lỗi trùng | **PASS** |
| 15 | `GET /health` | HTTP 200, `{"app":"DecisionHub","status":"ok"}` | **PASS** |
| 16 | `/docs` và `/redoc` | HTTP 200 | **PASS** |
| 17 | `password_hash` được lưu bằng bcrypt | Hash trong DB có tiền tố `$2b$12$` (cost 12), `verify_password` khớp với `Password@123` và không khớp với mật khẩu sai | **PASS** |

## 8. Lỗi và hạn chế còn tồn tại

### 8.1. Hạn chế của module (theo phạm vi hiện tại)

| Hạn chế | Mô tả | Hướng giải quyết |
|---|---|---|
| Không đổi mật khẩu | `PATCH /users/me` chỉ nhận `username` | Bổ sung trường `password` vào `UpdateProfileRequest` và xử lý hash trong `update_profile` |
| Không đổi email | `UpdateProfileRequest` chỉ cho phép đổi `username` | Tương tự, cần kiểm tra trùng email |
| Không có khôi phục / quên mật khẩu | Chưa có endpoint `forgot-password` | Cần thêm service và gửi email |
| Không có phân quyền theo vai trò | Chỉ có `ForbiddenException` trong `common/exceptions.py` nhưng chưa endpoint nào dùng; mọi endpoint dùng chung `get_current_user` | Thêm dependency `require_role(...)` khi cần khu vực ADMIN |
| Không có refresh token / logout | Chỉ cấp access token, hết hạn sau 60 phút | Thêm `refresh_token` và lưu blacklist hoặc lưu token trong DB |
| Không có xác thực 2 yếu tố (2FA) | Chưa triển khai | — |
| Không giới hạn số lần đăng ký / đăng nhập | Chưa có rate limit | Thêm middleware đếm request theo IP / email |

### 8.2. Điểm cần lưu ý khi vận hành

| Vấn đề | Ghi chú |
|---|---|
| `JWT_SECRET_KEY` để trống | Token mất hiệu lực sau mỗi lần restart server. Nên đặt giá trị cố định khi dev |
| Token hết hạn sau 60 phút | Client cần xử lý 401 để đăng nhập lại |
| Thiếu seed `roles` | Đăng ký trả 500. Chạy `sql/seeds/users.sql` trước |
| Mật khẩu tối đa 72 byte UTF-8 | Chuỗi có dấu nhiều byte có thể bị cắt ngắn; validator đã chặn giá trị vượt quá |
| `bcrypt` giới hạn 72 byte | Giới hạn của thư viện, không phải lỗi của module |

### 8.3. Phần việc mã nguồn chưa kiểm thử tự động

Không có file test Pytest nào cho module User/Auth trong `backend/tests/`. Toàn bộ kết quả ở
mục 7 được lấy bằng cách gọi HTTP trực tiếp vào server thật. Các file trong `tests/`
hiện tại thuộc về module Decision.

> Lưu ý: `pytest` và `ruff` có trong `requirements.txt` nhưng **chưa được cài** trong môi
> trường đã kiểm thử (chạy `pip install -r requirements.txt` sẽ cài thêm). Các lệnh
> `pytest` / `ruff` nên chạy sau khi cài đầy đủ requirements.

### 8.4. Phạm vi đã loại trừ khi viết tài liệu này

| Ngoài phạm vi | Lý do |
|---|---|
| Module Food / Travel / Decision | Không thuộc phần công việc |
| Frontend (`frontend/`) | Không thuộc phần công việc |
| Quản trị admin (`frontend/admin/`) | Không thuộc phần công việc |

