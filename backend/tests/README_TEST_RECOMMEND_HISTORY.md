# Hướng dẫn chạy lại kiểm thử API Recommend & Lịch sử quyết định

Tài liệu hướng dẫn ngắn gọn để thiết lập môi trường và chạy lại bộ kiểm thử tự động cho **Recommend API** và **Decision History API** của dự án **DecisionHub**.

---

## 1. Cấu trúc các file kiểm thử & minh chứng

| File | Vị trí | Mô tả |
|---|---|---|
| `test_recommend_api.py` | `backend/tests/test_recommend_api.py` | Kiểm thử tự động Nhóm A – API Recommend (`TC01`–`TC04`, `TC11`, `TC12`) |
| `test_decision_history_api.py` | `backend/tests/test_decision_history_api.py` | Kiểm thử tự động Nhóm B – API Lịch sử & Phân quyền bảo mật IDOR (`TC05`–`TC10`, `TC13`, `TC14`) |
| `test_cases_recommend_history.xlsx` | `backend/tests/test_cases_recommend_history.xlsx` | Bảng Test Case đầy đủ định dạng Excel (`.xlsx`) |
| `test_report_recommend_history.md` | `backend/tests/test_report_recommend_history.md` | Báo cáo kết quả kiểm thử chi tiết kèm Request/Response thực tế & sơ đồ luồng |

---

## 2. Chạy bộ kiểm thử tự động (Pytest / Unittest)

Bộ test tự động sử dụng cơ sở dữ liệu **SQLite In-Memory** độc lập cho từng test case, tự động khởi tạo 2 tài khoản test (`User A`, `User B`) và dữ liệu món ăn mẫu, tự động dọn sạch sau khi chạy xong (không cần bật MySQL và không ảnh hưởng dữ liệu thật).

Mở terminal tại thư mục gốc dự án `DecisionHub_neww`:

### Cách 1: Chạy bằng `pytest` (Khuyến nghị)
```powershell
backend\.venv\Scripts\pytest.exe -v backend\tests\test_recommend_api.py backend\tests\test_decision_history_api.py
```

### Cách 2: Chạy bằng `unittest`
```powershell
backend\.venv\Scripts\python.exe -m unittest -v backend\tests\test_recommend_api.py backend\tests\test_decision_history_api.py
```

**Kết quả mong đợi:** `14 passed` (100% Pass).

---

## 3. Chạy kiểm thử trực tiếp trên Server FastAPI + MySQL (Swagger UI / Postman)

Nếu muốn kiểm thử thủ công qua giao diện Swagger UI hoặc Postman:

1. **Đảm bảo MySQL đang chạy và đã cập nhật migration Alembic:**
   ```powershell
   cd backend
   .venv\Scripts\alembic.exe upgrade head
   ```
2. **Khởi động Backend Server:**
   ```powershell
   cd backend
   .venv\Scripts\uvicorn.exe app.main:app --reload
   ```
3. **Mở Swagger UI:** Truy cập `http://127.0.0.1:8000/docs` và thực hiện theo hướng dẫn tại mục **E** trong file `test_report_recommend_history.md`.

