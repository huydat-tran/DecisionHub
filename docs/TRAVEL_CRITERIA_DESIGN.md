# Thiết Kế Tiêu Chí Đánh Giá Travel (Decision Criteria)
## Dùng Chung Pipeline Decision Engine (WSM)

Tài liệu này đặc tả thiết kế bộ tiêu chí Travel (mã định danh, tên, hướng tối ưu - direction, trọng số - weight, chuẩn hóa thang điểm và mapping dữ liệu) để sử dụng chung pipeline Decision Engine với Food trong hệ thống DecisionHub.

---

## 1. Bảng Tiêu Chí Travel (Travel Decision Criteria)

Theo mô hình Weighted Sum Model (WSM), tập tiêu chí Travel gồm 3 tiêu chí cốt lõi: **Chi phí (`cost`)**, **Thời lượng (`duration`)**, và **Hoạt động (`activities`)**.

| STT | Mã định danh (`code`/`key`) | Tên Tiêu Chí (`name`) | Trường dữ liệu (`field`) | Hướng tối ưu (`direction`) | Trọng số (`weight`) | Diễn giải ý nghĩa |
|:---:|:---:|---|---|:---:|:---:|---|
| **1** | `cost` | **Chi phí** | `estimated_cost` | **`min`** | **0.40** (40%) | Chi phí càng thấp, càng tiết kiệm ngân sách thì điểm càng cao. |
| **2** | `duration` | **Thời lượng** | `estimated_duration` | **`min`** *(hoặc `max` theo cấu hình CSDL)* | **0.30** (30%) | Trong phạm vi quỹ thời gian tối đa cho phép, ưu tiên chuyến đi gọn gàng, tối ưu thời gian. |
| **3** | `activities` | **Hoạt động** | `activity_type` + `highlights` + `rating` | **`max`** | **0.30** (30%) | Mức độ phù hợp với hoạt động mong muốn và chất lượng trải nghiệm (rating). |

> **Ràng buộc toán học WSM:**  
> $$\sum_{i=1}^{n} w_i = 0.40 + 0.30 + 0.30 = 1.00$$

---

## 2. Đặc Tả Chi Tiết Từng Tiêu Chí

### 2.1. Tiêu chí 1: Chi phí chuyến đi (`cost`)
- **Mã định danh:** `cost`
- **Tên hiển thị:** Chi phí (hỗ trợ alias `Chi phí du lịch` để tương thích ngược)
- **Trường nguồn:** `estimated_cost` (đơn vị: VND, số nguyên).
- **Direction:** `min` (Càng nhỏ càng tốt).
- **Weight:** `0.40`
- **Công thức chuẩn hóa về thang điểm $[0, 100]$:**
  $$s_{\text{cost}}(A) = \left(1 - \frac{\text{cost}(A) - \text{cost}_{\min}}{\text{cost}_{\max} - \text{cost}_{\min}}\right) \times 100$$
  *(Nếu tất cả ứng viên có cùng chi phí: $s_{\text{cost}} = 100$)*.

---

### 2.2. Tiêu chí 2: Thời lượng chuyến đi (`duration`)
- **Mã định danh:** `duration`
- **Tên hiển thị:** Thời lượng (hỗ trợ alias `Thời lượng trải nghiệm`)
- **Trường nguồn:** `estimated_duration` (đơn vị: giờ, số thực).
- **Direction:** `min` theo cấu hình mặc định (hoặc `max` tùy cấu hình nghiệp vụ).
  - *Lý giải hướng tối ưu (`min` vs `max`):*
    - Người dùng đặt ra một quỹ thời gian tối đa (`max_duration`) thông qua Hard Constraint. Các địa điểm vượt quá thời gian này đã bị loại bỏ từ Bước 2.
    - Với các địa điểm còn lại thỏa mãn điều kiện, cấu hình mặc định là `min` nhằm ưu tiên tối ưu hóa quỹ thời gian (chuyến đi tốn ít thời gian di chuyển/tham quan hơn giúp người dùng không bị kiệt sức, dễ thu xếp thời gian).
    - Hệ thống hỗ trợ đọc động trường `direction` từ bảng `decision_criteria` trong database. Nếu nghiệp vụ yêu cầu ưu tiên chuyến đi dài ngày hơn (du lịch trải nghiệm sâu, nghỉ dưỡng dài hạn), chỉ cần cập nhật `direction = 'max'` trong database mà không cần thay đổi Decision Engine Pipeline.
- **Weight:** `0.30`
- **Công thức chuẩn hóa về thang điểm $[0, 100]$:**
  - Khi `direction = 'min'`:
    $$s_{\text{duration}}(A) = \left(1 - \frac{\text{duration}(A) - \text{duration}_{\min}}{\text{duration}_{\max} - \text{duration}_{\min}}\right) \times 100$$
  - Khi `direction = 'max'`:
    $$s_{\text{duration}}(A) = \left(\frac{\text{duration}(A) - \text{duration}_{\min}}{\text{duration}_{\max} - \text{duration}_{\min}}\right) \times 100$$

---

### 2.3. Tiêu chí 3: Mức độ phù hợp hoạt động (`activities`)
- **Mã định danh:** `activities` (hỗ trợ alias `preference`)
- **Tên hiển thị:** Hoạt động (hỗ trợ alias `Mức phù hợp sở thích`)
- **Trường nguồn:** Kết hợp giữa `activity_type` (loại hình chính), `highlights` (danh sách hoạt động nổi bật) và `rating` (1.0 - 5.0).
- **Direction:** `max` (Mức độ phù hợp càng cao càng tốt).
- **Weight:** `0.30`
- **Quy tắc tính giá trị thô trước khi chuẩn hóa:**
  1. Điểm đánh giá quy đổi: $\text{rating\_score} = \text{rating} \times 20$ (thang điểm $20 - 100$).
  2. Điểm khớp hoạt động (`activity_match`):
     - Kiểm tra nếu `preferred_activity` trùng khớp hoặc xuất hiện trong `activity_type` hoặc danh sách hoạt động nổi bật `highlights_list`:  
       $\text{activity_match} = 100.0$.
     - Nếu không khớp: $\text{activity_match} = 0.0$.
  3. Tổng hợp giá trị thô:
     - Nếu người dùng **không chọn** hoạt động ưu tiên:  
       $$\text{activities}(A) = \text{rating\_score}$$
     - Nếu người dùng **có chọn** hoạt động ưu tiên (`preferred_activity`):  
       $$\text{activities}(A) = 0.5 \times \text{rating\_score} + 0.5 \times \text{activity\_match}$$
- **Công thức chuẩn hóa về thang điểm $[0, 100]$:**
  $$s_{\text{activities}}(A) = \left(\frac{\text{activities}(A) - \text{activities}_{\min}}{\text{activities}_{\max} - \text{activities}_{\min}}\right) \times 100$$

---

## 3. Tổng Điểm Quyết Định (Weighted Sum Model)

Điểm tổng thể của phương án $A$ được tính theo công thức WSM dùng chung toàn hệ thống:

$$\text{Score}(A) = 0.40 \times s_{\text{cost}}(A) + 0.30 \times s_{\text{duration}}(A) + 0.30 \times s_{\text{activities}}(A)$$

$$\text{Score}(A) \in [0, 100]$$

- **Quy tắc giải quyết hòa điểm (Tie-breaker):**
  1. Điểm WSM cao hơn xếp trước.
  2. Nếu bằng điểm: Ưu tiên địa điểm có `estimated_cost` thấp hơn.
  3. Nếu vẫn bằng điểm: Sắp xếp theo tên địa điểm (A-Z).

---

## 4. Dữ Liệu Khởi Tạo (Seed SQL cho bảng `decision_criteria`)

Cơ chế Seed cập nhật bảng `decision_criteria` đảm bảo idempotent, không trùng lặp và không ảnh hưởng đến Criteria Food:

```sql
-- Thêm cấu hình tiêu chí Travel vào bảng decision_criteria (Tổng = 1.0)
INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Chi phí', 'min', 0.4000
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.name IN ('Chi phí', 'Chi phí du lịch')
);

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Thời lượng', 'min', 0.3000
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.name IN ('Thời lượng', 'Thời lượng trải nghiệm')
);

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Hoạt động', 'max', 0.3000
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.name IN ('Hoạt động', 'Mức phù hợp sở thích', 'Hoạt động trải nghiệm')
);

-- Đồng bộ cập nhật nếu bản ghi cũ đã tồn tại
UPDATE decision_criteria SET direction = 'min', weight = 0.4000 WHERE name IN ('Chi phí', 'Chi phí du lịch');
UPDATE decision_criteria SET direction = 'min', weight = 0.3000 WHERE name IN ('Thời lượng', 'Thời lượng trải nghiệm');
UPDATE decision_criteria SET direction = 'max', weight = 0.3000 WHERE name IN ('Hoạt động', 'Mức phù hợp sở thích', 'Hoạt động trải nghiệm');
```
