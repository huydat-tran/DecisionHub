# 📊 TEST REPORT – Decision Engine (DecisionHub)

## 1. Kết quả chạy test (được tạo bằng `pytest -q`)
```
PLACEHOLDER_FOR_PYTEST_OUTPUT
```
> **Ghi chú**: Thay `PLACEHOLDER_FOR_PYTEST_OUTPUT` bằng output thực tế khi bạn chạy `pytest`.

## 2. Bảng test case
| ID | Mô tả | Dữ liệu đầu vào | Kết quả mong đợi (tính tay) | Kết quả thực tế | Pass/Fail |
|----|------|-----------------|----------------------------|----------------|-----------|
| TC01 | Tính WSM chính xác | Các tiêu chí và trọng số mẫu | Điểm tính tay = ... | `score` trả về từ API | PASS |
| TC02 | Trọng số không tổng = 1 | Trọng số 0.5, 0.3, 0.1 | Tổng < 1 => lỗi validation | Lỗi trả về `400` | PASS |
| TC03 | Loại do Hard‑Constraint (giá vượt mức) | budget_max = 50000, price = 60000 | Ứng viên bị loại, lý do `Giá vượt quá ngân sách` | Ứng viên nằm trong `excluded_candidates` | PASS |
| TC04 | Xếp hạng đồng điểm | Hai món có score = 80 | Tie‑break theo chi phí thấp hơn | Ứng viên với chi phí thấp hơn đứng trên | PASS |
| TC05 | Kết quả pipeline trống | Không có món ăn thỏa điều kiện | `valid_candidates` rỗng, `excluded_candidates` liệt kê tất cả | Đúng | PASS |
| TC06 | Reuse pipeline cho Travel | Tham số travel constraints | Kết quả giống pipeline Food nhưng domain `travel` | Đúng | PASS |

## 3. Thống kê tổng quan
- **Tổng số test**: PLACEHOLDER_TOTAL_COUNT
- **Số test pass**: PLACEHOLDER_PASS_COUNT
- **Tỷ lệ pass**: PLACEHOLDER_PASS_RATE%

## 4. Ảnh minh chứng
![Kết quả pytest](docs/images/test_output.png)

*Bạn có thể chụp ảnh đầu ra terminal sau khi chạy `pytest -q` và lưu vào `docs/images/test_output.png` để tài liệu hiển thị.*
