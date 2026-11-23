# Bảng Test Case Chi Tiết – Travel Decision Engine (Trước Khi Tích Hợp)

Tài liệu này đặc tả toàn bộ ma trận kiểm thử (Test Cases) cho logic xử lý quyết định phân hệ **Travel (WhereShouldITravel)** của hệ thống **DecisionHub**. Bảng kiểm thử được thiết kế để thẩm định độc lập chất lượng và độ ổn định của Decision Engine trước khi ghép nối vào API Service và Frontend.

---

## 1. Thông Tin Chung & Quy Chuẩn Kiểm Thử

- **Phân hệ:** Travel Decision (`backend/app/modules/travel` & `backend/app/modules/decision`).
- **Mô hình kiến trúc:** Modular Monolith, Decision Engine thuần Python (không phụ thuộc I/O / DB).
- **Quy trình kiểm thử 6 bước chuẩn:**
  1. *Candidate Retrieval & Data Adapter:* Ánh xạ dữ liệu `TravelPlace` sang candidate struct.
  2. *Constraint Filtering:* Lọc điều kiện bắt buộc (Hard Constraints) – ngân sách, thời lượng, khu vực, trạng thái hoạt động.
  3. *Criteria Scoring:* Chuẩn hóa giá trị tiêu chí về thang $[0, 100]$ (Min-Max normalization).
  4. *Weighted Sum Model (WSM):* Tính tổng điểm có trọng số $\text{Score}(A) = \sum (w_i \times s_i(A))$, $\sum w_i = 1.0$.
  5. *Ranking & Tie-breaking:* Sắp xếp giảm dần theo WSM Score; giải quyết hòa điểm theo thứ tự `estimated_cost` $\rightarrow$ Tên $\rightarrow$ ID; cắt Top N (`limit`).
  6. *Explanation & Exclusion Reasons:* Sinh lý do minh bạch từ dữ liệu thực tế và giải thích nguyên nhân loại trừ.

### Rubric Trọng Số Mặc Định (Travel Default Rubric)
| Tiêu chí | Field Name chuẩn | Chiều tối ưu (Direction) | Trọng số ($w_i$) | Ý nghĩa nghiệp vụ |
| :--- | :--- | :---: | :---: | :--- |
| **Chi phí** | `estimated_cost` | `min` | **0.40** (40%) | Tiết kiệm chi phí tham khảo cho người dùng |
| **Thời lượng** | `estimated_duration` | `min` | **0.30** (30%) | Tối ưu hóa quỹ thời gian trải nghiệm |
| **Hoạt động / Chất lượng** | `activities` | `max` | **0.30** (30%) | Điểm hoạt động nổi bật hoặc mức độ phù hợp sở thích |

---

## 2. Ma Trận Test Cases Chi Tiết

### Nhóm 1: Schema & Input Validation (Đầu vào Request)

| Mã TC | Hạng mục | Mục tiêu / Tình huống | Dữ liệu đầu vào (Input) | Các bước thực hiện | Kết quả mong đợi (Expected Output) | Mức độ |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-VAL-01** | Input Validation | `budget_max` hợp lệ | `budget_max: 2000000`, `region: "Bắc"` | Gửi request qua schema Pydantic | Pass validation, parse ra kiểu `int = 2000000`. | **P0** |
| **TC-VAL-02** | Input Validation | `budget_max` <= 0 hoặc số âm | `budget_max: 0` hoặc `-500000` | Validate payload đầu vào | Báo lỗi validation `422/400`: `budget_max` phải lớn hơn 0. | **P0** |
| **TC-VAL-03** | Input Validation | `budget_max` sai kiểu (float/chuỗi) | `budget_max: "hai_trieu"` hoặc `true` | Validate payload | Báo lỗi `422/400`: `budget_max` phải là số nguyên dương. | **P1** |
| **TC-VAL-04** | Input Validation | `region` không thuộc Enum cho phép | `region: "Đông Nam Bộ"` | Validate với Enum `TravelRegion` | Báo lỗi `422`: `region` phải thuộc `['Bắc', 'Trung', 'Nam', 'Tây Nguyên', 'Tây Nam Bộ']`. | **P0** |
| **TC-VAL-05** | Input Validation | `max_duration` không hợp lệ | `max_duration: -2.5` hoặc `0` | Validate `max_duration` | Báo lỗi `422`: Thời lượng phải là số dương (> 0). | **P1** |
| **TC-VAL-06** | Input Validation | Trọng số tùy chỉnh (`weights`) có tổng $\neq 1.0$ | `weights: {cost: 0.5, duration: 0.3, activities: 0.3}` (tổng = 1.1) | Kiểm tra `validate_weight_sum` | Báo lỗi `400/422`: `Tổng trọng số phải bằng 1.0 (hiện tại: 1.1000)`. | **P0** |
| **TC-VAL-07** | Input Validation | Trọng số có giá trị âm hoặc > 1.0 | `weights: {cost: -0.1, duration: 0.6, activities: 0.5}` | Kiểm tra `validate_weight_value` | Báo lỗi `400/422`: Trọng số phải nằm trong đoạn `[0.0, 1.0]`. | **P1** |
| **TC-VAL-08** | Input Validation | Tham số `limit` ngoài phạm vi cho phép | `limit: 0` hoặc `limit: 50` (chuẩn 1–20) | Validate `limit` | Báo lỗi `422`: `limit` phải trong khoảng `[1, 20]`. | **P1** |

---

### Nhóm 2: Data Adapter & Mapping (Entity ORM $\rightarrow$ Engine Candidate)

| Mã TC | Hạng mục | Mục tiêu / Tình huống | Dữ liệu đầu vào (Input) | Các bước thực hiện | Kết quả mong đợi (Expected Output) | Mức độ |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-MAP-01** | Data Adapter | Ánh xạ đầy đủ trường từ `TravelPlace` ORM | Đối tượng `TravelPlace(id=10, name="Vịnh Hạ Long", estimated_cost=1500000, estimated_duration=8.0, highlights="Du thuyền, Kayak")` | Chạy hàm adapter chuyển entity sang candidate dictionary | Candidate có đủ key: `id: 10`, `name: "Vịnh Hạ Long"`, `estimated_cost: 1500000`, `estimated_duration: 8.0`, `activities: 2`. | **P0** |
| **TC-MAP-02** | Data Adapter | Chuẩn hóa `highlights` dạng rỗng hoặc None | `highlights: None` hoặc `""` | Adapter trích xuất danh sách hoạt động | `activities` trả về `0` hoặc `[]`, không gây lỗi `AttributeError` hoặc `NoneType`. | **P1** |
| **TC-MAP-03** | Data Adapter | Tính Idempotent khi đã là canonical `field_name` | Dictionary đã có `estimated_cost`, `estimated_duration` | Gọi qua `resolve_field_name` | Trả về nguyên bản `field_name`, không bị biến đổi sai lệch. | **P1** |

---

### Nhóm 3: Hard Constraints Filtering (Lọc điều kiện tiên quyết)

| Mã TC | Hạng mục | Mục tiêu / Tình huống | Dữ liệu đầu vào (Input) | Các bước thực hiện | Kết quả mong đợi (Expected Output) | Mức độ |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-FLT-01** | Hard Constraint | Lọc ứng viên vượt ngân sách (`estimated_cost <= budget_max`) | `budget_max: 1000000`.<br>- Điểm A: 800.000đ<br>- Điểm B: 1.200.000đ | Chạy `filter_and_explain_candidates` | - Valid: Điểm A.<br>- Excluded: Điểm B kèm lý do `Chi phí 1.200.000đ vượt ngân sách 1.000.000đ`. | **P0** |
| **TC-FLT-02** | Hard Constraint | Lọc theo thời lượng tối đa (`estimated_duration <= max_duration`) | `max_duration: 4.0h`.<br>- Điểm A: 3.0h<br>- Điểm B: 6.0h | Chạy filter | - Valid: Điểm A.<br>- Excluded: Điểm B kèm lý do `Thời lượng 6.0h vượt quá 4.0h yêu cầu`. | **P0** |
| **TC-FLT-03** | Hard Constraint | Lọc theo khu vực địa lý (`region == requested_region`) | `region: "Bắc"`.<br>- Điểm A: Bắc<br>- Điểm B: Trung | Chạy filter | - Valid: Điểm A.<br>- Excluded: Điểm B kèm lý do không khớp khu vực. | **P0** |
| **TC-FLT-04** | Hard Constraint | Loại bỏ địa điểm ngưng hoạt động (`is_active == False`) | Điểm C: `is_active=False` (dù chi phí và thời lượng đạt) | Chạy filter | Điểm C bị loại với lý do `Địa điểm tạm ngưng hoạt động`. | **P0** |
| **TC-FLT-05** | Hard Constraint | Lọc theo loại hình trải nghiệm (`activity_type`) | `activity_type: "Nghỉ dưỡng biển"`.<br>- Điểm A: Nghỉ dưỡng biển<br>- Điểm B: Khám phá thiên nhiên | Chạy filter | - Valid: Điểm A.<br>- Excluded: Điểm B. | **P1** |
| **TC-FLT-06** | Hard Constraint | Nhiều điều kiện đồng thời (Multiple constraints) | `budget_max: 1M`, `region: "Nam"`, `max_duration: 5h` | Chạy filter trên 10 địa điểm hỗn hợp | Chỉ những địa điểm thỏa mãn **toàn bộ 3 điều kiện** mới vào `valid_candidates`. | **P0** |

---

### Nhóm 4: Criteria Scoring & Normalization (Chuẩn hóa Min-Max 0–100)

| Mã TC | Hạng mục | Mục tiêu / Tình huống | Dữ liệu đầu vào (Input) | Các bước thực hiện | Kết quả mong đợi (Expected Output) | Mức độ |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-SCR-01** | Scoring (Cost) | Chuẩn hóa chiều `min` cho chi phí (`estimated_cost`) | 3 địa điểm có chi phí:<br>- A: 200.000đ (thấp nhất)<br>- B: 600.000đ<br>- C: 1.000.000đ (cao nhất) | Gọi `score_candidates` với tiêu chí cost (`min`) | - Score Cost A = **100.0**<br>- Score Cost B = **50.0**<br>- Score Cost C = **0.0** | **P0** |
| **TC-SCR-02** | Scoring (Duration) | Chuẩn hóa chiều `min` cho thời lượng (`estimated_duration`) | - A: 2.0h (ngắn nhất)<br>- B: 6.0h (dài nhất) | Gọi `score_candidates` với tiêu chí duration (`min`) | - Score Duration A = **100.0**<br>- Score Duration B = **0.0** | **P0** |
| **TC-SCR-03** | Scoring (Activities) | Chuẩn hóa chiều `max` cho số hoạt động (`activities`) | - A: 5 hoạt động<br>- B: 10 hoạt động<br>- C: 15 hoạt động (cao nhất) | Gọi `score_candidates` với tiêu chí activities (`max`) | - Score Activities A = **0.0**<br>- Score Activities B = **50.0**<br>- Score Activities C = **100.0** | **P0** |
| **TC-SCR-04** | Scoring Edge Case | Tất cả ứng viên có giá trị tiêu chí bằng nhau ($Min = Max$) | 3 địa điểm đều có `estimated_cost = 500.000đ` | Gọi `score_candidates` | Cả 3 đều nhận `EQUAL_RANGE_SCORE = 100.0` (không gây lỗi chia cho 0). | **P0** |
| **TC-SCR-05** | Scoring Missing Data | Ứng viên thiếu dữ liệu tiêu chí (None/null) | Điểm A có `activities = None` | Gọi `score_candidates` | Điểm A nhận `activities: None` trong `criteria_scores` (**không tự suy diễn điểm**). | **P0** |
| **TC-SCR-06** | Scoring Isolation | `score_candidates` không tính tổng WSM và không mutate input | Danh sách candidates gốc | Gọi `score_candidates` | Output trả về chứa `criteria_scores`, **không chứa key `score`**; candidate dict gốc không bị thay đổi. | **P1** |

---

### Nhóm 5: Weighted Sum Model (WSM Calculation)

| Mã TC | Hạng mục | Mục tiêu / Tình huống | Dữ liệu đầu vào (Input) | Các bước thực hiện | Kết quả mong đợi (Expected Output) | Mức độ |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-WSM-01** | WSM Calculation | Tính WSM với trọng số mặc định (0.4, 0.3, 0.3) | Điểm X:<br>- Cost Score: 100<br>- Duration Score: 80<br>- Activities Score: 60 | Gọi `calculate_wsm` | $\text{Score} = 100 \times 0.4 + 80 \times 0.3 + 60 \times 0.3 = \mathbf{82.0}$. | **P0** |
| **TC-WSM-02** | WSM Calculation | Tính WSM với trọng số tùy chỉnh của User | Weights: `cost: 0.6, duration: 0.2, activities: 0.2`. Điểm X như TC-WSM-01 | Gọi `calculate_wsm` | $\text{Score} = 100 \times 0.6 + 80 \times 0.2 + 60 \times 0.2 = \mathbf{88.0}$. | **P1** |
| **TC-WSM-03** | WSM Missing Field | Xử lý WSM khi có tiêu chí bị `None` | Điểm Y: Cost Score=100 ($w=0.4$), Activities Score=50 ($w=0.3$), Duration Score=`None` ($w=0.3$) | Gọi `calculate_wsm` | Chuẩn hóa theo tổng trọng số các tiêu chí còn lại ($w_{\text{effective}} = 0.7$). Không crash hệ thống. | **P1** |

---

### Nhóm 6: Ranking & Tie-breaking (Xếp hạng và Hòa điểm)

| Mã TC | Hạng mục | Mục tiêu / Tình huống | Dữ liệu đầu vào (Input) | Các bước thực hiện | Kết quả mong đợi (Expected Output) | Mức độ |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-RNK-01** | Ranking | Sắp xếp giảm dần theo điểm WSM | - Điểm A: 85.0đ<br>- Điểm B: 92.5đ<br>- Điểm C: 70.0đ | Gọi `rank_candidates` | Thứ tự: B (`rank 1`), A (`rank 2`), C (`rank 3`). | **P0** |
| **TC-RNK-02** | Tie-Breaking Level 1 | Bằng điểm WSM $\rightarrow$ Ưu tiên chi phí thấp hơn (`estimated_cost`) | - Điểm A: Score 80.0, Cost 400.000đ<br>- Điểm B: Score 80.0, Cost 300.000đ | Gọi `rank_candidates` | Điểm B xếp trước Điểm A (chi phí 300k < 400k). | **P0** |
| **TC-RNK-03** | Tie-Breaking Level 2 | Bằng điểm WSM và Bằng Chi phí $\rightarrow$ Ưu tiên Tên A–Z | - Điểm A: Score 80, Cost 300k, Tên: "Tràng An"<br>- Điểm B: Score 80, Cost 300k, Tên: "Ba Vì" | Gọi `rank_candidates` | "Ba Vì" xếp trước "Tràng An" ('B' đứng trước 'T'). | **P1** |
| **TC-RNK-04** | Tie-Breaking Level 3 | Bằng điểm, Bằng chi phí, Bằng tên $\rightarrow$ Ưu tiên ID nhỏ hơn | 2 bản ghi cùng tên, cùng cost, cùng score, `id: 5` và `id: 8` | Gọi `rank_candidates` | Bản ghi `id: 5` xếp trước `id: 8`. | **P2** |
| **TC-RNK-05** | Ranking Limit | Áp dụng tham số `limit` (Top N) | Danh sách 10 địa điểm hợp lệ, `limit: 3` | Gọi `rank_candidates(limit=3)` | Trả về đúng 3 địa điểm có rank 1, 2, 3. `returned_count = 3`, `total_valid = 10`. | **P0** |

---

### Nhóm 7: Explanation & Gợi ý (Bước 6)

| Mã TC | Hạng mục | Mục tiêu / Tình huống | Dữ liệu đầu vào (Input) | Các bước thực hiện | Kết quả mong đợi (Expected Output) | Mức độ |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-EXP-01** | Explanation | Tạo lý do đề xuất dựa trên dữ liệu thật (1–3 lý do) | Địa điểm Top 1 có chi phí rẻ nhất và nhiều hoạt động nhất | Gọi bộ tạo explanation | Trả về lý do thực tế (vd: *"Chi phí tiết kiệm nhất trong các lựa chọn"*, *"Có nhiều hoạt động trải nghiệm đặc sắc"*); không bịa đặt dữ liệu. | **P0** |
| **TC-EXP-02** | Exclusion Reason | Giải thích rõ ràng phương án bị loại | Địa điểm bị loại do `estimated_cost = 2.500.000 > budget_max = 2.000.000` | Kiểm tra `excluded_candidates` | Mục bị loại có đủ `id`, `name`, `status: "excluded"`, `exclusion_reason` chỉ rõ số liệu chênh lệch. | **P0** |
| **TC-EXP-03** | Excluded Detail Cap | Giới hạn số lượng chi tiết bị loại trong response | 35 địa điểm bị loại | Kiểm tra response payload | `total_excluded = 35`, danh sách chi tiết `excluded_candidates` giới hạn tối đa `MAX_EXCLUDED_DETAIL = 20`. | **P1** |

---

### Nhóm 8: Edge Cases & Trường hợp đặc biệt

| Mã TC | Hạng mục | Mục tiêu / Tình huống | Dữ liệu đầu vào (Input) | Các bước thực hiện | Kết quả mong đợi (Expected Output) | Mức độ |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-EDG-01** | Edge Case | Danh sách ứng viên ban đầu rỗng (`candidates = []`) | Bảng `travel_places` rỗng hoặc query không ra bản ghi | Gọi `evaluate_decision` | `has_valid_candidates: False`, `message: "Không có phương án nào được cung cấp để đánh giá"`, trả mảng `[]`, không crash. | **P0** |
| **TC-EDG-02** | Edge Case | Toàn bộ ứng viên bị loại bởi Hard Constraints | Ngân sách đặt quá thấp (`budget_max: 50.000đ`), không địa điểm nào đạt | Chạy `evaluate_decision` | - `has_valid_candidates: False`.<br>- **Tuyệt đối không chạy Scoring/WSM**.<br>- Trả về thông báo kèm gợi ý nới lỏng điều kiện. | **P0** |
| **TC-EDG-03** | Edge Case | Chỉ duy nhất 1 ứng viên hợp lệ | 1 ứng viên duy nhất sau khi lọc | Chạy toàn bộ pipeline | Trả về đúng ứng viên đó, `rank: 1`, `score: 100.0` (do min=max), giải thích hợp lệ. | **P1** |
| **TC-EDG-04** | Edge Case | Địa điểm miễn phí vé tham quan (`estimated_cost = 0`) | `estimated_cost: 0` (hợp lệ trong thực tế) | Chạy scoring chiều `min` | Tính toán chính xác tỉ lệ Min-Max, không bị lỗi chia cho 0 hay nhận nhầm là `None`. | **P1** |
| **TC-EDG-05** | Edge Case | Thời lượng dạng số thập phân (`estimated_duration = 1.5h`, `0.5h`) | `Decimal("1.5")` hoặc `float(1.5)` | Chạy adapter và scoring | Xử lý trơn tru kiểu số học, không gặp lỗi `TypeError` giữa `Decimal` và `float`. | **P1** |

---

### Nhóm 9: Contract & API Readiness (Hợp đồng API trước khi ghép nối)

| Mã TC | Hạng mục | Mục tiêu / Tình huống | Dữ liệu đầu vào (Input) | Các bước thực hiện | Kết quả mong đợi (Expected Output) | Mức độ |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-API-01** | API Contract | Cấu trúc phản hồi đúng chuẩn `DecisionResponse` | Mock Travel candidates $\rightarrow$ `evaluate_decision` | Kiểm tra schema kết quả trả về | Response chứa các trường bắt buộc: `success`, `has_valid_candidates`, `message`, `valid_candidates` (chứa `rank`, `score`, `criteria_scores`), `excluded_candidates`, `total_valid`, `returned_count`. | **P0** |
| **TC-API-02** | API Contract | Không chứa đối tượng SQLAlchemy ORM sống | Đối tượng SQLAlchemy `TravelPlace` | Kiểm tra json-serializable của response | Toàn bộ response đều là dict/primitive types, serialize thành JSON thành công (không dính lỗi instance ORM không serialize được). | **P0** |

---

## 3. Quy Trình & Chiến Lược Thực Thi

1. **Giai đoạn 1 (Unit Test độc lập - Pre-integration):**
   - Viết file test độc lập `backend/tests/test_travel_decision.py` sử dụng mock candidates / SimpleNamespace.
   - Chạy kiểm thử tự động toàn bộ test case mức **P0** và **P1** với `pytest`.
2. **Giai đoạn 2 (Integration Service & Repository):**
   - Ghép nối hàm truy vấn từ DB MySQL (sử dụng dữ liệu seed `sql/seeds/travel_places.sql`).
   - Kiểm tra tương thích với bảng `decision_criteria` domain `travel`.
3. **Giai đoạn 3 (Endpoint & Router Integration):**
   - Định tuyến API `POST /api/v1/travel/recommend` (hoặc domain `travel` trong decision router).
   - Kiểm thử contract response đầu ra với Frontend.
