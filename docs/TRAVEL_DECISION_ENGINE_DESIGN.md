# Tài Liệu Thiết Kế Tiêu Chí Travel & Tích Hợp Decision Engine Pipeline

Tài liệu đặc tả chi tiết kiến trúc, các tiêu chí đánh giá, hướng tối ưu (direction), trọng số (weight), quy trình lọc và chấm điểm Weighted Sum Model (WSM) cho phân hệ **Travel (WhereShouldITravel)** dùng chung Decision Engine với phân hệ **Food**.

---

## 1. Mục Tiêu & Nguyên Tắc Thiết Kế

1. **Tái sử dụng tối đa pipeline Decision Engine:**
   - Decision Engine hoạt động độc lập với cơ sở dữ liệu (`backend/app/modules/decision/engine/`).
   - Nhận danh sách ứng viên đã chuẩn hóa (`candidates: list[dict]`) và danh sách tiêu chí (`criteria: list[Criterion]`).
   - Module Travel (`app/modules/travel/service.py`) chịu trách nhiệm truy vấn database, áp dụng Hard Constraints và map trường thành định dạng chuẩn trước khi chuyển cho Engine.
2. **Tuân thủ quy trình 6 bước chuẩn của DecisionHub:**
   - **Bước 1: Candidate Retrieval:** Truy vấn các địa điểm đang mở/hoạt động (`is_active = True`).
   - **Bước 2: Constraint Filtering:** Lọc cứng các điều kiện bắt buộc (ngân sách, thời lượng, khu vực).
   - **Bước 3: Criteria Scoring:** Chuẩn hóa giá trị từng tiêu chí về thang điểm $[0, 100]$ theo hướng `min` hoặc `max`.
   - **Bước 4: Weighted Sum Model (WSM):** Nhân điểm tiêu chí với trọng số $\sum (w_i \times s_i)$, tổng trọng số bằng 1.0.
   - **Bước 5: Ranking:** Sắp xếp giảm dần theo điểm tổng; xử lý hòa điểm (tie-breaker).
   - **Bước 6: Explanation:** Tự động sinh $1 - 3$ lý do minh bạch dựa trên dữ liệu thực tế.

---

## 2. Bảng Tiêu Chí Travel (Rubric WSM)

Phân hệ Travel áp dụng Rubric 3 tiêu chí cốt lõi tương tự như phân hệ Food:

| STT | Tiêu chí | Cột nguồn DB (`travel_places`) | Key Candidate | Direction | Trọng số ($w_i$) | Ý nghĩa nghiệp vụ |
|:---:|---|---|---|:---:|:---:|---|
| **1** | **Chi phí** | `estimated_cost` | `cost` | **`min`** | **0.40** (40%) | Chi phí càng thấp, tiết kiệm ngân sách càng được ưu tiên |
| **2** | **Thời lượng** | `estimated_duration` | `duration` | **`min`** | **0.30** (30%) | Thời lượng ngắn gọn, tối ưu quỹ thời gian trong ngưỡng cho phép (linh hoạt min/max trong DB) |
| **3** | **Hoạt động** | `rating` + `activity_type` + `highlights` | `activities` | **`max`** | **0.30** (30%) | Mức độ phù hợp với loại hình/hoạt động và chất lượng trải nghiệm |

$$\sum_{i=1}^{3} w_i = 0.40 + 0.30 + 0.30 = 1.00$$

---

## 3. Chi Tiết Thuật Toán & Công Thức

### 3.1. Chuẩn Hóa Điểm Tiêu Chí (Criteria Scoring)

Với một tập ứng viên hợp lệ sau bước lọc, mỗi tiêu chí được chuẩn hóa về thang $[0, 100]$:

- **Hướng cực tiểu (`min` - chi phí, thời lượng):**
  $$s_{\min}(A) = \left(1 - \frac{\text{value}(A) - \min(\text{values})}{\max(\text{values}) - \min(\text{values})}\right) \times 100$$
  *(Nếu $\max = \min$, tất cả ứng viên nhận 100 điểm).*

- **Hướng cực đại (`max` - mức độ phù hợp/chất lượng):**
  $$s_{\max}(A) = \left(\frac{\text{value}(A) - \min(\text{values})}{\max(\text{values}) - \min(\text{values})}\right) \times 100$$

### 3.2. Cách Tính Tiêu Chí "Mức Phù Hợp Sở Thích" (`preference`)

Giá trị thô (`preference`) được tính toán kết hợp trước khi đưa vào normalization:
- Quy đổi điểm đánh giá: $\text{rating\_score} = \text{rating} \times 20$ (thang 1.0 - 5.0 quy đổi về 20 - 100).
- Hệ số tương thích loại hình hoạt động:
  - Nếu người dùng **không chọn** `preferred_activity`:
    $$\text{preference}(A) = \text{rating\_score}$$
  - Nếu người dùng **có chọn** `preferred_activity`:
    $$\text{preference}(A) = 0.5 \times \text{rating\_score} + 0.5 \times \text{activity\_match}$$
    Trong đó $\text{activity\_match} = 100$ nếu trùng khớp `activity_type`, ngược lại $= 0$.

### 3.3. Thuật Toán Xếp Hạng & Giải Quyết Hòa Điểm (Tie-Breaker)

Sắp xếp ứng viên theo thứ tự ưu tiên nhiều tầng:
1. **Điểm tổng WSM (`score`):** Giảm dần.
2. **Chi phí (`cost`):** Tăng dần (ưu tiên phương án tiết kiệm hơn khi cùng điểm).
3. **Tên địa điểm (`name`):** Thứ tự alphabet (đảm bảo tính ổn định của kết quả).

---

## 4. Đặc Tả Bộ Lọc Điều Kiện Bắt Buộc (Hard Constraints)

Lọc trước khi tính điểm nhằm loại bỏ hoàn toàn các phương án không khả thi:

| Tên Ràng Buộc | Field DB | Toán tử | Nguồn Dữ Liệu Input | Bắt buộc / Tùy chọn |
|---|---|:---:|---|:---:|
| **Ngân sách tối đa** | `estimated_cost` | `<=` | `request.budget_max` | **Bắt buộc** |
| **Thời lượng tối đa** | `estimated_duration` | `<=` | `request.max_duration` | **Bắt buộc** |
| **Khu vực ưu tiên** | `region` | `IN` | `request.regions` | Tùy chọn |
| **Loại hình bắt buộc** | `activity_type` | `=` | `request.required_activity` | Tùy chọn |

---

## 5. Kiến Trúc & Cấu Trúc Mã Nguồn

```
backend/
├── app/
│   ├── main.py                               # Đăng ký travel_router
│   └── modules/
│       ├── decision/
│       │   ├── models.py                     # DecisionCriterion, HardConstraint
│       │   └── engine/
│       │       ├── calculator.py             # Score candidates (WSM) & sinh lý do giải thích
│       │       └── ranking.py                # Sắp xếp và xử lý tie-breaker
│       └── travel/
│           ├── models.py                     # TravelPlace SQLAlchemy Model
│           ├── schemas.py                    # TravelRecommendRequest, TravelDecisionResponse...
│           ├── repository.py                 # Query SQL (Candidate Retrieval & Search)
│           ├── service.py                    # Pipeline Recommendation & Logic Travel
│           └── router.py                     # API Endpoints (/quick-search, /{id}, /recommend)
├── sql/seeds/
│   ├── decision_criteria.sql                 # Seed tiêu chí WSM Travel
│   └── hard_constraints.sql                  # Seed hard constraints Travel
└── tests/
    └── test_decision_engine_travel.py        # Unit test kiểm thử pipeline WSM
```

---

## 6. Đặc Tả API Contract

### `POST /api/v1/travel/recommend`

#### Request Body
```json
{
  "budget_max": 2000000,
  "max_duration": 24.0,
  "regions": ["Bắc", "Trung"],
  "preferred_activity": "Khám phá thiên nhiên",
  "top_n": 5
}
```

#### Response (200 OK)
```json
{
  "items": [
    {
      "place_id": 2,
      "name": "Quần thể danh thắng Tràng An",
      "province_city": "Ninh Bình",
      "region": "Bắc",
      "estimated_cost": 450000,
      "estimated_duration": 6.0,
      "activity_type": "Khám phá thiên nhiên",
      "rating": 4.9,
      "image_url": "https://images.unsplash.com/photo-1528127269322-539801943592",
      "score": 93.42,
      "criteria_scores": {
        "cost": 95.2,
        "preference": 99.0,
        "duration": 82.5
      },
      "reasons": [
        "Phù hợp loại hình 'Khám phá thiên nhiên' bạn ưa thích (điểm: 99/100)",
        "Chi phí 450.000 VND nằm trong ngân sách 2.000.000 VND (điểm: 95/100)",
        "Thời lượng 6.0 giờ phù hợp với quỹ thời gian 24.0 giờ (điểm: 83/100)"
      ]
    }
  ],
  "total": 1,
  "limit": 5,
  "applied_filters": {
    "budget_max": 2000000,
    "max_duration": 24.0,
    "regions": ["Bắc", "Trung"],
    "preferred_activity": "Khám phá thiên nhiên"
  },
  "scoring": {
    "method": "WSM",
    "weights": {
      "cost": 0.4,
      "duration": 0.3,
      "activities": 0.3
    }
  }
}
```
