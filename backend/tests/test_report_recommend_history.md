# BÁO CÁO KẾT QUẢ KIỂM THỬ API RECOMMEND VÀ LỊCH SỬ QUYẾT ĐỊNH – DECISIONHUB

---

## A. Thông tin kiểm thử

| Hạng mục | Chi tiết |
|---|---|
| **Tên dự án** | DecisionHub – Hệ thống hỗ trợ ra quyết định (Modular Monolith) |
| **Module kiểm thử** | Recommend API (`app/modules/decision/`) & Decision History API (`app/modules/decision/`) |
| **Ngày kiểm thử** | 25/11/2026 |
| **Môi trường kiểm thử** | Python 3.10+ (`backend/.venv`), FastAPI, SQLAlchemy 2.x, Pydantic v2, PyJWT, Bcrypt, SQLite In-Memory / MySQL 8 (`utf8mb4`) |
| **Công cụ kiểm thử** | `pytest`, `unittest`, Swagger UI (`/docs`), Postman / cURL |
| **File test tự động** | `backend/tests/test_recommend_api.py`, `backend/tests/test_decision_history_api.py` |

### Danh sách API thực tế được kiểm thử

| STT | Nhóm | HTTP Method | Endpoint thực tế (và Alias tương thích) | Xác thực JWT | Mô tả chức năng |
|---|---|---|---|---|---|
| 1 | Recommend | `POST` | `/decisions/food/recommend`<br>`/api/v1/decisions/food/recommend`<br>`/decisions/recommend`<br>`/api/v1/decisions/recommend` | Optional (`Bearer <token>`) – Có token sẽ xác thực và lưu lịch sử vào bảng `decisions`; không có token chạy chế độ Guest (không lưu lịch sử); token sai/hết hạn trả `401`. | Lọc ứng viên theo Hard Constraints, chuẩn hóa điểm (0–100), tính tổng điểm WSM, xếp hạng Top N, sinh giải thích và lưu snapshot quyết định. |
| 2 | History | `GET` | `/decisions/history`<br>`/api/v1/decisions/history` | Required (`Bearer <token>`) – Bắt buộc đăng nhập (`get_current_user`). | Lấy danh sách lịch sử quyết định của chính người dùng đang đăng nhập, sắp xếp `created_at DESC`, hỗ trợ phân trang `limit` (1–100, mặc định 20) và `offset` (>= 0). |
| 3 | History | `GET` | `/decisions/history/{decision_id}`<br>`/api/v1/decisions/history/{decision_id}` | Required (`Bearer <token>`) – Bắt buộc đăng nhập (`get_current_user`). | Xem chi tiết một quyết định đã lưu theo `decision_id`. Kiểm tra quyền sở hữu `user_id == current_user.id`; trả `404` nếu không tồn tại hoặc thuộc về người dùng khác. |

### Sơ đồ luồng kiểm thử API Recommend & Lịch sử quyết định

```mermaid
sequenceDiagram
    autonumber
    actor UA as User A (JWT Token A)
    actor UB as User B (JWT Token B)
    actor G as Guest (Không Token)
    participant API as FastAPI Decision Router
    participant Auth as JWT Auth Dependency
    participant Svc as Decision Service & WSM Engine
    participant DB as Database (decisions)

    Note over UA,DB: 1. Luồng Recommend & Lưu lịch sử (TC01, TC02)
    UA->>API: POST /decisions/food/recommend (Bearer Token A + Valid JSON)
    API->>Auth: get_optional_current_user(Token A)
    Auth-->>API: User A (id=101)
    API->>Svc: recommend_food_decisions(payload, user_id=101)
    Svc->>DB: Truy vấn foods, decision_criteria, hard_constraints
    Svc->>Svc: Lọc Hard Constraints + Chấm điểm WSM + Xếp hạng
    Svc->>DB: INSERT INTO decisions (user_id=101, domain='food', input_snapshot, result_snapshot)
    Svc-->>UA: 200 OK (DecisionResponse: items, excluded_items, scoring)

    Note over G,DB: 2. Luồng Recommend thiếu Token / Token sai (TC03, TC04)
    G->>API: POST /decisions/food/recommend (No Authorization Header)
    API->>Svc: recommend_food_decisions(payload, user_id=None)
    Svc-->>G: 200 OK (Trả kết quả gợi ý, KHÔNG ghi bảng decisions)

    Note over UA,DB: 3. Luồng Xem lịch sử & Bảo mật phân quyền IDOR (TC05 -> TC10)
    UA->>API: GET /decisions/history (Bearer Token A)
    API->>Auth: get_current_user(Token A)
    API->>DB: SELECT * FROM decisions WHERE user_id=101 ORDER BY created_at DESC
    DB-->>UA: 200 OK (Chỉ trả danh sách quyết định của User A)

    UA->>API: GET /decisions/history/{decision_id_của_User_B} (Bearer Token A)
    API->>Auth: get_current_user(Token A)
    API->>DB: SELECT * FROM decisions WHERE id={id_B} AND user_id=101
    DB-->>API: None (Không khớp chủ sở hữu)
    API-->>UA: 404 Not Found (RESOURCE_NOT_FOUND - Chặn truy cập chéo IDOR)
```

---

## B. Kết quả tổng hợp

| Chỉ số | Số lượng | Tỷ lệ |
|---|---|---|
| **Tổng số Test Case** | **14** | 100% |
| **Số Test Case Passed** | **14** | **100%** |
| **Số Test Case Failed** | **0** | 0% |
| **Số Test Case Blocked / Not Run** | **0** | 0% |
| **Số lỗi (Bug) phát hiện trên Backend** | **0** | Không có lỗi |

### Đánh giá tổng thể
- **Tính đúng đắn nghiệp vụ (Recommend WSM):** API `POST /decisions/food/recommend` lọc chính xác các điều kiện bắt buộc (`budget_max`, `meal_type`, `max_prep_time`, `excluded_ingredients`), tính điểm WSM chính xác theo trọng số mặc định (`0.40 / 0.35 / 0.25`) cũng như trọng số tùy chỉnh, trả về đầy đủ phương án hợp lệ (`items`) và phương án bị loại kèm lý do (`excluded_items`). Khi không còn ứng viên nào phù hợp, API trả về `200 OK` với `has_valid_candidates: false`, `items: []` và thông báo hướng dẫn người dùng nới lỏng điều kiện, không gây lỗi `500`.
- **Tính toàn vẹn lưu lịch sử:** Khi người dùng đã đăng nhập bằng JWT hợp lệ, mỗi lần gọi Recommend thành công đều tạo đúng 1 bản ghi trong bảng `decisions` với `user_id` trích xuất từ JWT (chặn hoàn toàn việc giả mạo `user_id` trong body nhờ `extra="forbid"`), lưu đầy đủ `input_snapshot` và `result_snapshot`.
- **Bảo mật & Phân quyền (JWT + Chống IDOR):**
  - Các API lịch sử (`GET /decisions/history`, `GET /decisions/history/{decision_id}`) bắt buộc JWT hợp lệ; mọi request thiếu token, token sai chữ ký hoặc hết hạn đều bị chặn với `401 UNAUTHORIZED`.
  - Truy vấn lịch sử luôn ràng buộc `Decision.user_id == current_user.id`. Khi User A cố tình thay đổi `decision_id` trên URL sang ID lịch sử của User B, hệ thống trả về `404 RESOURCE_NOT_FOUND` (đồng nhất với ID không tồn tại), đảm bảo không rò rỉ dữ liệu và không tiết lộ sự tồn tại bản ghi của người dùng khác.

---

## C. Bảng Test Case tổng hợp (TC01 – TC14)

| TC ID | Nhóm | Mô tả test | Input / Điều kiện | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|---|
| **TC01** | Recommend | Recommend với input hợp lệ và có kết quả (User A đăng nhập) | `POST /decisions/food/recommend`<br>Header: `Authorization: Bearer <token_user_a>`<br>Body: `{"budget_max": 50000, "meal_type": "lunch", "max_prep_time": 25, "excluded_ingredients": ["đậu phộng"], "preferred_tags": ["truyền thống"], "limit": 5}` | HTTP `200 OK`. `success=true`, `has_valid_candidates=true`, `total=2`, `items` xếp hạng WSM giảm dần (`rank` 1, 2), `excluded_items` có 1 món vượt ngân sách/chứa đậu phộng. Bảng `decisions` lưu 1 bản ghi mới của User A. | HTTP `200 OK`. Trả về 2 món hợp lệ (`Bún chả Hà Nội` hạng 1, `Cơm chiên đậu hũ nấm` hạng 2), 1 món bị loại (`Cơm tấm sườn bì chả`). Bảng `decisions` có 1 bản ghi `user_id=101`, `domain="food"`. | **PASSED** |
| **TC02** | Recommend | Recommend khi không còn ứng viên phù hợp | `POST /decisions/food/recommend`<br>Header: `Authorization: Bearer <token_user_a>`<br>Body: `{"budget_max": 10000, "meal_type": "lunch", "limit": 5}` (Ngân sách thấp hơn mọi món ăn) | HTTP `200 OK`. `success=true`, `has_valid_candidates=false`, `total=0`, `items=[]`, `total_excluded=3`, `message` báo không có phương án hợp lệ. Không lỗi 500. | HTTP `200 OK`. `has_valid_candidates=false`, `items=[]`, `total=0`, `total_excluded=3`, `message`: *"Không có phương án hợp lệ sau khi lọc theo điều kiện bắt buộc..."*. | **PASSED** |
| **TC03** | Recommend | Recommend khi thiếu Authorization Token (Guest) | `POST /decisions/food/recommend`<br>Header: Không có `Authorization`<br>Body: `{"budget_max": 50000, "meal_type": "lunch", "limit": 5}` | HTTP `200 OK`. Trả về kết quả gợi ý WSM bình thường cho khách (Guest), nhưng **không** lưu bản ghi vào bảng `decisions`. | HTTP `200 OK`. `success=true`, `total=2`. Số bản ghi trong bảng `decisions` = `0`. | **PASSED** |
| **TC04** | Recommend | Recommend khi token không hợp lệ hoặc hết hạn | `POST /decisions/food/recommend`<br>Header: `Authorization: Bearer <invalid_or_expired_token>`<br>Body: `{"budget_max": 50000, "meal_type": "lunch", "limit": 5}` | HTTP `401 Unauthorized`. `success=false`, `error_code="UNAUTHORIZED"`, `message="Access token không hợp lệ hoặc đã hết hạn."`. Không lưu lịch sử. | HTTP `401 Unauthorized`. `success=false`, `error_code="UNAUTHORIZED"`, bảng `decisions` không phát sinh bản ghi. | **PASSED** |
| **TC05** | History | User A lấy danh sách lịch sử của chính mình | `GET /decisions/history?limit=20&offset=0`<br>Header: `Authorization: Bearer <token_user_a>`<br>(DB có 2 quyết định của User A, 1 quyết định của User B) | HTTP `200 OK`. `success=true`, `total=2`, `data` chỉ gồm 2 bản ghi `user_id=101` (User A), sắp xếp `created_at DESC` (mới nhất đứng đầu). | HTTP `200 OK`. `total=2`, trả về đúng 2 bản ghi của User A theo thứ tự `10:30` trước, `09:00` sau; không chứa bản ghi của User B. | **PASSED** |
| **TC06** | History | User A xem chi tiết lịch sử của chính mình | `GET /decisions/history/{decision_id_user_a}`<br>Header: `Authorization: Bearer <token_user_a>` | HTTP `200 OK`. `success=true`, trả về đầy đủ `id`, `user_id=101`, `domain="food"`, `input_snapshot`, `result_snapshot`, `created_at` khớp dữ liệu đã lưu. | HTTP `200 OK`. Trả về đúng chi tiết quyết định của User A với `input_snapshot.budget_max=40000` và `result_snapshot.items[0].name="Bún chả Hà Nội"`. | **PASSED** |
| **TC07** | History (Security) | User A không thể xem lịch sử của User B (Chống IDOR) | `GET /decisions/history/{decision_id_user_b}`<br>Header: `Authorization: Bearer <token_user_a>` | HTTP `404 Not Found`. `success=false`, `error_code="RESOURCE_NOT_FOUND"`. Tuyệt đối không trả dữ liệu `input_snapshot` / `result_snapshot` của User B. | HTTP `404 Not Found`. `success=false`, `error_code="RESOURCE_NOT_FOUND"`, `message="Lịch sử quyết định với mã 3 không tồn tại."`. Không rò rỉ dữ liệu của User B. | **PASSED** |
| **TC08** | History | User B chỉ nhận được lịch sử của User B | `GET /decisions/history`<br>Header: `Authorization: Bearer <token_user_b>` | HTTP `200 OK`. `total=1`, `data` chỉ chứa duy nhất bản ghi của User B (`user_id=202`), không có dữ liệu của User A. | HTTP `200 OK`. `total=1`, `data[0].user_id=202`, `data[0].input_snapshot.budget_max=50000`. | **PASSED** |
| **TC09** | History | Lấy danh sách / chi tiết lịch sử khi thiếu token | `GET /decisions/history` và `GET /decisions/history/1`<br>Header: Không có `Authorization` | HTTP `401 Unauthorized`. `success=false`, `error_code="UNAUTHORIZED"`, `message="Không có quyền truy cập. Vui lòng đăng nhập."`. | HTTP `401 Unauthorized` trên cả 2 endpoint. `error_code="UNAUTHORIZED"`. | **PASSED** |
| **TC10** | History | Truy cập `decision_id` không tồn tại | `GET /decisions/history/999999`<br>Header: `Authorization: Bearer <token_user_a>` | HTTP `404 Not Found`. `success=false`, `error_code="RESOURCE_NOT_FOUND"`, `data={"resource": "Lịch sử quyết định", "id": 999999}`. | HTTP `404 Not Found`. `success=false`, `error_code="RESOURCE_NOT_FOUND"`, `message="Lịch sử quyết định với mã 999999 không tồn tại."`. | **PASSED** |
| **TC11** | Recommend (Bổ sung) | Recommend với trọng số WSM tùy chỉnh hợp lệ (`Σw = 1.0`) | `POST /decisions/food/recommend`<br>Header: `Authorization: Bearer <token_user_a>`<br>Body: `{"budget_max": 50000, "meal_type": "lunch", "weights": {"price": 0.6, "preference": 0.25, "prep_time": 0.15}}` | HTTP `200 OK`. `scoring.weights` phản ánh đúng trọng số tùy chỉnh `0.6 / 0.25 / 0.15` và xếp hạng ưu tiên món giá rẻ nhất. | HTTP `200 OK`. `scoring.weights` khớp `{"price": 0.6, "preference": 0.25, "prep_time": 0.15}`, `Cơm chiên đậu hũ nấm` (30.000đ) đứng hạng 1. | **PASSED** |
| **TC12** | Recommend (Bổ sung) | Recommend với dữ liệu không hợp lệ hoặc chèn `user_id` giả mạo trong body | `POST /decisions/food/recommend`<br>Body 1: `{"budget_max": -20000}`<br>Body 2: `{"budget_max": 50000, "weights": {"price": 0.5, "preference": 0.5, "prep_time": 0.5}}`<br>Body 3: `{"budget_max": 50000, "user_id": 999}` | HTTP `422 Unprocessable Entity`. `success=false`, `error_code="VALIDATION_ERROR"`, `errors` chỉ rõ trường lỗi. Không lưu bản ghi lịch sử. | HTTP `422 Unprocessable Entity` cho cả 3 trường hợp. Bảng `decisions` có `0` bản ghi. | **PASSED** |
| **TC13** | History (Bổ sung) | Truy cập API lịch sử với token sai hoặc đã hết hạn | `GET /decisions/history`<br>Header: `Authorization: Bearer <invalid_or_expired_token>` | HTTP `401 Unauthorized`. `success=false`, `error_code="UNAUTHORIZED"`, `message="Access token không hợp lệ hoặc đã hết hạn."`. | HTTP `401 Unauthorized`. `error_code="UNAUTHORIZED"`. | **PASSED** |
| **TC14** | History (Bổ sung) | User mới chưa từng recommend lấy danh sách lịch sử | `GET /decisions/history`<br>Header: `Authorization: Bearer <token_user_c>` | HTTP `200 OK`. `success=true`, `total=0`, `data=[]`, `items=[]`, không phát sinh lỗi. | HTTP `200 OK`. `success=true`, `total=0`, `data=[]`, `items=[]`. | **PASSED** |

---

## D. Chi tiết từng Test Case (Request & Response thực tế)

### TC01 – Recommend với input hợp lệ và có kết quả (Lưu lịch sử thành công)
- **Endpoint:** `POST /decisions/food/recommend`
- **Headers:** `Authorization: Bearer <JWT_TOKEN_USER_A>`
- **Request Body:**
```json
{
  "budget_max": 50000,
  "meal_type": "lunch",
  "max_prep_time": 25,
  "excluded_ingredients": ["đậu phộng"],
  "preferred_tags": ["truyền thống"],
  "limit": 5
}
```
- **HTTP Status Code:** `200 OK`
- **Response JSON thực tế:**
```json
{
  "success": true,
  "message": "Đánh giá thành công 2 phương án hợp lệ.",
  "has_valid_candidates": true,
  "items": [
    {
      "food_id": 2,
      "id": 2,
      "name": "Cơm chiên đậu hũ nấm",
      "price": 30000,
      "meal_type": "lunch",
      "prep_time": 12,
      "image_url": null,
      "tags": ["chay", "thanh đạm", "nhanh"],
      "score": 65.0,
      "total_score": 65.0,
      "rank": 1,
      "criteria_scores": {
        "price": 100.0,
        "preference": 0.0,
        "prep_time": 100.0
      },
      "criteria_details": {
        "price": { "normalized_score": 100.0, "weight": 0.4, "contribution": 40.0 },
        "preference": { "normalized_score": 0.0, "weight": 0.35, "contribution": 0.0 },
        "prep_time": { "normalized_score": 100.0, "weight": 0.25, "contribution": 25.0 }
      },
      "reasons": [
        "Giá 30.000đ nằm trong ngân sách tối đa 50.000đ",
        "Phù hợp cho bữa lunch",
        "Thời gian chuẩn bị 12 phút (đạt giới hạn ≤ 25 phút)"
      ]
    },
    {
      "food_id": 1,
      "id": 1,
      "name": "Bún chả Hà Nội",
      "price": 35000,
      "meal_type": "lunch",
      "prep_time": 20,
      "image_url": null,
      "tags": ["truyền thống", "đậm đà"],
      "score": 35.0,
      "total_score": 35.0,
      "rank": 2,
      "criteria_scores": {
        "price": 0.0,
        "preference": 100.0,
        "prep_time": 0.0
      },
      "criteria_details": {
        "price": { "normalized_score": 0.0, "weight": 0.4, "contribution": 0.0 },
        "preference": { "normalized_score": 100.0, "weight": 0.35, "contribution": 35.0 },
        "prep_time": { "normalized_score": 0.0, "weight": 0.25, "contribution": 0.0 }
      },
      "reasons": [
        "Giá 35.000đ nằm trong ngân sách tối đa 50.000đ",
        "Phù hợp khẩu vị ưu tiên: truyền thống",
        "Thời gian chuẩn bị 20 phút (đạt giới hạn ≤ 25 phút)"
      ]
    }
  ],
  "excluded_items": [
    {
      "id": 3,
      "name": "Cơm tấm sườn bì chả",
      "status": "excluded",
      "is_excluded": true,
      "exclusion_reason": "Giá (55,000đ) vượt quá ngân sách tối đa (50,000đ).; Chứa nguyên liệu cần tránh: Đậu phộng.",
      "exclusion_reasons": [
        "Giá (55,000đ) vượt quá ngân sách tối đa (50,000đ).",
        "Chứa nguyên liệu cần tránh: Đậu phộng."
      ]
    }
  ],
  "total": 2,
  "total_excluded": 1,
  "limit": 5,
  "applied_filters": {
    "budget_max": 50000,
    "meal_type": "lunch",
    "max_prep_time": 25,
    "excluded_ingredients": ["đậu phộng"],
    "preferred_tags": ["truyền thống"]
  },
  "scoring": {
    "method": "WSM",
    "weights": { "price": 0.4, "preference": 0.35, "prep_time": 0.25 }
  }
}
```
- **Kết quả:** **PASSED** (1 bản ghi lịch sử được tạo trong bảng `decisions` với `user_id = 101`).

---

### TC02 – Recommend khi không còn ứng viên phù hợp
- **Endpoint:** `POST /decisions/food/recommend`
- **Headers:** `Authorization: Bearer <JWT_TOKEN_USER_A>`
- **Request Body:**
```json
{
  "budget_max": 10000,
  "meal_type": "lunch",
  "limit": 5
}
```
- **HTTP Status Code:** `200 OK`
- **Response JSON thực tế:**
```json
{
  "success": true,
  "message": "Không có phương án hợp lệ sau khi lọc theo điều kiện bắt buộc. Hãy thử nới lỏng ngân sách, thời gian chuẩn bị hoặc danh sách nguyên liệu cần tránh.",
  "has_valid_candidates": false,
  "items": [],
  "excluded_items": [
    {
      "id": 1,
      "name": "Bún chả Hà Nội",
      "status": "excluded",
      "is_excluded": true,
      "exclusion_reason": "Giá (35,000đ) vượt quá ngân sách tối đa (10,000đ).",
      "exclusion_reasons": ["Giá (35,000đ) vượt quá ngân sách tối đa (10,000đ)."]
    },
    {
      "id": 2,
      "name": "Cơm chiên đậu hũ nấm",
      "status": "excluded",
      "is_excluded": true,
      "exclusion_reason": "Giá (30,000đ) vượt quá ngân sách tối đa (10,000đ).",
      "exclusion_reasons": ["Giá (30,000đ) vượt quá ngân sách tối đa (10,000đ)."]
    },
    {
      "id": 3,
      "name": "Cơm tấm sườn bì chả",
      "status": "excluded",
      "is_excluded": true,
      "exclusion_reason": "Giá (55,000đ) vượt quá ngân sách tối đa (10,000đ).",
      "exclusion_reasons": ["Giá (55,000đ) vượt quá ngân sách tối đa (10,000đ)."]
    }
  ],
  "total": 0,
  "total_excluded": 3,
  "limit": 5,
  "applied_filters": {
    "budget_max": 10000,
    "meal_type": "lunch",
    "max_prep_time": null,
    "excluded_ingredients": [],
    "preferred_tags": []
  },
  "scoring": {
    "method": "WSM",
    "weights": { "price": 0.4, "preference": 0.35, "prep_time": 0.25 }
  }
}
```
- **Kết quả:** **PASSED**.

---

### TC03 – Recommend khi thiếu Authorization Token
- **Endpoint:** `POST /decisions/food/recommend`
- **Headers:** *(Không truyền `Authorization`)*
- **Request Body:** `{"budget_max": 50000, "meal_type": "lunch", "limit": 5}`
- **HTTP Status Code:** `200 OK`
- **Actual Result:** Trả về kết quả gợi ý cho Guest (`total: 2`), bảng `decisions` có `0` bản ghi được tạo.
- **Kết quả:** **PASSED**.

---

### TC04 – Recommend khi token không hợp lệ hoặc hết hạn
- **Endpoint:** `POST /decisions/food/recommend`
- **Headers:** `Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.invalid_payload.invalid_signature`
- **Request Body:** `{"budget_max": 50000, "meal_type": "lunch", "limit": 5}`
- **HTTP Status Code:** `401 Unauthorized`
- **Response JSON thực tế:**
```json
{
  "success": false,
  "message": "Access token không hợp lệ hoặc đã hết hạn.",
  "data": null,
  "error_code": "UNAUTHORIZED",
  "errors": null,
  "path": "/decisions/food/recommend"
}
```
- **Kết quả:** **PASSED**.

---

### TC05 – User A lấy danh sách lịch sử của chính mình
- **Endpoint:** `GET /decisions/history?limit=20&offset=0`
- **Headers:** `Authorization: Bearer <JWT_TOKEN_USER_A>`
- **HTTP Status Code:** `200 OK`
- **Response JSON thực tế:**
```json
{
  "success": true,
  "message": "Lấy danh sách lịch sử quyết định thành công.",
  "data": [
    {
      "id": 2,
      "user_id": 201,
      "domain": "food",
      "input_snapshot": {
        "budget_max": 60000,
        "meal_type": "breakfast",
        "max_prep_time": null,
        "excluded_ingredients": [],
        "preferred_tags": ["nước"],
        "limit": 5,
        "weights": null
      },
      "result_snapshot": {
        "success": true,
        "has_valid_candidates": true,
        "total": 1,
        "total_excluded": 1,
        "items": [
          {
            "food_id": 1,
            "id": 1,
            "name": "Phở bò tái",
            "price": 45000,
            "meal_type": "breakfast",
            "prep_time": 15,
            "score": 100.0,
            "total_score": 100.0,
            "rank": 1
          }
        ]
      },
      "created_at": "2026-11-25T10:30:00"
    },
    {
      "id": 1,
      "user_id": 201,
      "domain": "food",
      "input_snapshot": {
        "budget_max": 40000,
        "meal_type": "lunch",
        "max_prep_time": null,
        "excluded_ingredients": [],
        "preferred_tags": ["truyền thống"],
        "limit": 5,
        "weights": null
      },
      "result_snapshot": {
        "success": true,
        "has_valid_candidates": true,
        "total": 1,
        "total_excluded": 1
      },
      "created_at": "2026-11-25T09:00:00"
    }
  ],
  "items": ["..."],
  "total": 2,
  "limit": 20,
  "offset": 0
}
```
- **Kết quả:** **PASSED**.

---

### TC06 – User A xem chi tiết lịch sử của chính mình
- **Endpoint:** `GET /decisions/history/1`
- **Headers:** `Authorization: Bearer <JWT_TOKEN_USER_A>`
- **HTTP Status Code:** `200 OK`
- **Response JSON thực tế:**
```json
{
  "success": true,
  "message": "Lấy chi tiết lịch sử quyết định thành công.",
  "data": {
    "id": 1,
    "user_id": 201,
    "domain": "food",
    "input_snapshot": {
      "budget_max": 40000,
      "meal_type": "lunch",
      "max_prep_time": null,
      "excluded_ingredients": [],
      "preferred_tags": ["truyền thống"],
      "limit": 5,
      "weights": null
    },
    "result_snapshot": {
      "success": true,
      "has_valid_candidates": true,
      "total": 1,
      "items": [
        {
          "food_id": 2,
          "id": 2,
          "name": "Bún chả Hà Nội",
          "price": 35000,
          "meal_type": "lunch",
          "prep_time": 20,
          "score": 100.0,
          "total_score": 100.0,
          "rank": 1
        }
      ]
    },
    "created_at": "2026-11-25T09:00:00"
  },
  "id": 1,
  "user_id": 201,
  "domain": "food",
  "input_snapshot": { "...": "..." },
  "result_snapshot": { "...": "..." },
  "created_at": "2026-11-25T09:00:00"
}
```
- **Kết quả:** **PASSED**.

---

### TC07 – User A không thể xem lịch sử của User B (Kiểm thử bảo mật IDOR)
- **Endpoint:** `GET /decisions/history/3` *(ID `3` là quyết định của User B)*
- **Headers:** `Authorization: Bearer <JWT_TOKEN_USER_A>`
- **HTTP Status Code:** `404 Not Found`
- **Response JSON thực tế:**
```json
{
  "success": false,
  "message": "Lịch sử quyết định với mã 3 không tồn tại.",
  "data": {
    "resource": "Lịch sử quyết định",
    "id": 3
  },
  "error_code": "RESOURCE_NOT_FOUND",
  "errors": null,
  "path": "/decisions/history/3"
}
```
- **Kết quả:** **PASSED** (Chặn hoàn toàn truy cập trái phép giữa User A và User B).

---

### TC08 – User B chỉ nhận được lịch sử của User B
- **Endpoint:** `GET /decisions/history`
- **Headers:** `Authorization: Bearer <JWT_TOKEN_USER_B>`
- **HTTP Status Code:** `200 OK`
- **Actual Result:** `total = 1`, chỉ chứa bản ghi `id = 3, user_id = 202` của User B.
- **Kết quả:** **PASSED**.

---

### TC09 – Lấy lịch sử khi thiếu token
- **Endpoint:** `GET /decisions/history`
- **Headers:** *(Không truyền `Authorization`)*
- **HTTP Status Code:** `401 Unauthorized`
- **Response JSON thực tế:**
```json
{
  "success": false,
  "message": "Không có quyền truy cập. Vui lòng đăng nhập.",
  "data": null,
  "error_code": "UNAUTHORIZED",
  "errors": null,
  "path": "/decisions/history"
}
```
- **Kết quả:** **PASSED**.

---

### TC10 – Truy cập `decision_id` không tồn tại
- **Endpoint:** `GET /decisions/history/999999`
- **Headers:** `Authorization: Bearer <JWT_TOKEN_USER_A>`
- **HTTP Status Code:** `404 Not Found`
- **Response JSON thực tế:**
```json
{
  "success": false,
  "message": "Lịch sử quyết định với mã 999999 không tồn tại.",
  "data": {
    "resource": "Lịch sử quyết định",
    "id": 999999
  },
  "error_code": "RESOURCE_NOT_FOUND",
  "errors": null,
  "path": "/decisions/history/999999"
}
```
- **Kết quả:** **PASSED**.

---

## E. Hướng dẫn chụp ảnh màn hình minh chứng (Swagger UI / Postman)

Nếu cần đính kèm ảnh chụp màn hình trực tiếp trên trình duyệt (Swagger UI tại `http://127.0.0.1:8000/docs`) hoặc Postman để nộp kèm báo cáo:

1. **Ảnh 1 – Recommend thành công với dữ liệu hợp lệ (TC01):**
   - Đăng nhập `POST /auth/login` với `user1@example.com` / `Password@123`, copy `access_token` dán vào nút **Authorize** trên `/docs`.
   - Gọi `POST /decisions/food/recommend` với body `{"budget_max": 50000, "meal_type": "lunch", "max_prep_time": 25, "preferred_tags": ["truyền thống"], "limit": 5}`.
   - Chụp màn hình HTTP `200` hiển thị `items` đã xếp hạng `rank: 1` kèm `total_score` và `reasons`.
2. **Ảnh 2 – Recommend không có ứng viên phù hợp (TC02):**
   - Gọi `POST /decisions/food/recommend` với body `{"budget_max": 5000, "meal_type": "lunch", "limit": 5}`.
   - Chụp màn hình HTTP `200` với `"has_valid_candidates": false`, `"items": []` và danh sách `"excluded_items"`.
3. **Ảnh 3 – Request thiếu token khi gọi API lịch sử (TC09):**
   - Nhấn **Authorize -> Logout** trên Swagger UI (hoặc bỏ tick Authorization trên Postman).
   - Gọi `GET /decisions/history`.
   - Chụp màn hình kết quả HTTP `401` với `"error_code": "UNAUTHORIZED"`, `"message": "Không có quyền truy cập. Vui lòng đăng nhập."`.
4. **Ảnh 4 – User A truy cập danh sách lịch sử của chính mình (TC05):**
   - Authorize bằng token của User A (`user1@example.com`).
   - Gọi `GET /decisions/history`.
   - Chụp màn hình HTTP `200` hiển thị danh sách quyết định có `"user_id"` của User A.
5. **Ảnh 5 – User A thử truy cập lịch sử của User B và bị từ chối (TC07):**
   - Giữ token của User A, gọi `GET /decisions/history/{id_của_user_b}`.
   - Chụp màn hình HTTP `404` với `"error_code": "RESOURCE_NOT_FOUND"`.
6. **Ảnh 6 – Kết quả tổng thể chạy Automated Test trên Terminal:**
   - Chạy lệnh:
     ```bash
     backend\.venv\Scripts\pytest.exe -v backend\tests\test_recommend_api.py backend\tests\test_decision_history_api.py
     ```
   - Chụp màn hình Terminal hiển thị `14 passed`.

