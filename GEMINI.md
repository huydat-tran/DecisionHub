# DecisionHub – Workspace Rules

Quy tắc phát triển hợp nhất cho dự án **DecisionHub** (chuyển đổi và tổng hợp từ `.cursor/rules/decisionhub.mdc`, `DecisionHub.md`, `README.md`, `backend/README.md`, `frontend/README.md`, `frontend/docs/DESIGN-SYSTEM-README.md` và `frontend/docs/UI-GUIDELINES.md`).

---

## 1. Tổng quan & Tech Stack

**DecisionHub** là ứng dụng hỗ trợ người dùng đưa ra quyết định thông qua tìm kiếm nhanh (Quick Search) và gợi ý có chấm điểm/xếp hạng (Smart Recommendation).

- **Kiến trúc:** Modular Monolith (1 ứng dụng FastAPI chia theo module nghiệp vụ; không microservices trong MVP).
- **Backend:** Python 3.10+ (venv tại `backend/.venv` theo `pyrightconfig.json`), FastAPI, SQLAlchemy 2.x, MySQL 8 (`utf8mb4`), PyMySQL, Pydantic v2, Ruff (lint/format), Pytest.
- **Frontend:** HTML5, CSS3, JavaScript thuần, Bootstrap 5.0.2, Roboto font, SweetAlert2.
  - *Lưu ý hiện trạng repo:* `.cursor/rules/decisionhub.mdc` quy định dùng **Fetch API**, trong khi base code `frontend/js/api.js` đang bọc sẵn **axios** (CDN) cùng `CONFIG.API_BASE_URL` trong `frontend/js/config.js`. Khi làm tính năng mới hoặc tích hợp API, cần kiểm tra `frontend/js/api.js` và thống nhất theo phạm vi task (không tự ý viết lại hàng loạt ngoài phạm vi).

---

## 2. Phạm vi MVP & Thứ tự ưu tiên (`DecisionHub.md`)

**Nguyên tắc xuyên suốt:** *Hoàn thiện Food trước — mở rộng Travel sau — chỉ triển khai History và Group Voting khi đáp ứng điều kiện ưu tiên.*

1. **P0 – MUST (`food`):** Quick Search, bộ lọc cơ bản, Smart Recommendation theo tiêu chí (lọc điều kiện + WSM + xếp hạng + giải thích), trang chi tiết món ăn. Phải chạy end-to-end và qua kiểm thử trước khi chuyển trọng tâm.
2. **P1 – SHOULD (`travel`):** Chỉ triển khai sau khi Food ổn định (Gate 1). Ưu tiên Quick Search, bộ lọc cơ bản, danh sách và trang chi tiết; Recommendation chỉ làm nếu nền tảng chung đã sẵn sàng và đủ thời gian.
3. **P2 – OPTIONAL (`history`):** Chỉ xem xét sau Gate 2 (Travel cơ bản ổn định) và sau khi thống nhất cách nhận diện người dùng.
4. **P3 – OPTIONAL (`group voting`):** Chỉ xem xét sau Gate 3; không tự động làm chat, realtime hoặc thuật toán bình chọn phức tạp.

**Khóa phạm vi (Out of Scope MVP):**
- Không thêm module thứ ba ngoài lộ trình.
- Không tích hợp AI/LLM hội thoại; Quick Search dùng từ khóa và bộ lọc có cấu trúc.
- Không phụ thuộc API bên ngoài để lấy dữ liệu cốt lõi (dùng dữ liệu seed của nhóm).
- Không làm bản đồ tương tác, GPS, định tuyến, đặt vé/đặt bàn/giỏ hàng/thanh toán, cập nhật giá realtime, RBAC phức tạp hoặc dashboard quản trị lớn.

---

## 3. Quy tắc kiến trúc Backend (`backend/`)

Luồng xử lý chuẩn:
`Frontend --HTTP--> modules/<module>/router.py --> service.py --> repository.py (nếu cần) --> MySQL`

- **Cấu trúc thư mục:**
  - `backend/app/main.py`: Khởi động FastAPI, CORS, đăng ký exception handlers và router. Không đặt logic nghiệp vụ vào `main.py`.
  - `backend/app/core/`: Hạ tầng dùng chung (`config.py` đọc `.env`, `database.py` cung cấp `engine`, `SessionLocal`, `Base`, `get_db`, `security.py`).
  - `backend/app/common/`: Thành phần dùng chung (`responses.py` với `success_response`, `exceptions.py` với `DecisionHubException`, `ResourceNotFoundException`).
  - `backend/app/modules/`: Mỗi module (`auth`, `users`, `food`, `travel`, `decision`) chịu trách nhiệm cho một nghiệp vụ riêng.
- Không tạo module mới nếu chức năng thuộc về một module hiện có.
- Không biến Decision Engine thành module độc lập nếu nó là thành phần xử lý bên trong `app/modules/decision/` (`engine/filters.py`, `scoring.py`, `ranking.py`, `explanations.py`).

### FastAPI, SQLAlchemy & Pydantic
- Dùng `APIRouter` trong từng module; khai báo HTTP method và Pydantic response schema rõ ràng.
- Không viết business logic hoặc truy vấn database trực tiếp trong router/endpoint.
- Dùng SQLAlchemy 2.x style (`Mapped`, `mapped_column`), lấy session qua dependency `get_db`; không tạo `engine` hoặc `SessionLocal` riêng trong module.
- Dùng Pydantic v2; tách request/response schema khi cần; không trả trực tiếp SQLAlchemy model làm response nếu không có chủ đích rõ ràng.
- Không tự ý thay đổi schema database ngoài phạm vi task; giá/chi phí dùng đơn vị `VND` và có seed script thống nhất.

### Bảo mật
- Không lưu mật khẩu plaintext; dùng password hashing an toàn.
- Không hardcode JWT secret hoặc database password.
- Không trả thông tin nội bộ hoặc dữ liệu nhạy cảm trong response.
- Kiểm tra quyền truy cập trước khi thực hiện thao tác cần phân quyền; không tin tưởng dữ liệu từ frontend.

---

## 4. Decision Engine & Quy tắc API (`DecisionHub.md`)

- **Decision Engine (`modules/decision/`):** Nhận danh sách ứng viên đã chuẩn hóa từ module Food/Travel; **không truy vấn database** và không chứa logic đặc thù domain.
- **Quy trình 6 bước:** Candidate Retrieval (module) → Constraint Filtering → Criteria Scoring (0–100) → Weighted Sum Model `Score(A) = Σ(wᵢ × sᵢ(A))`, `Σwᵢ = 1` → Ranking (Top N giảm dần; hòa điểm ưu tiên chi phí thấp hơn, rồi tên/ID) → Explanation (1–3 lý do dựa trên dữ liệu thực, không bịa).
- Điều kiện bắt buộc lọc trước, không dùng điểm số bù trừ vi phạm; không tự suy diễn điểm cho trường bị thiếu; danh sách hợp lệ rỗng thì trả rỗng kèm gợi ý nới điều kiện.
- **Rubric Food mặc định:** Giá 40%, Mức phù hợp nhu cầu/khẩu vị 35%, Thời gian chuẩn bị 25%.
- **API chuẩn:**
  - `GET /health`
  - Food (P0): `GET /api/v1/food/quick-search`, `GET /api/v1/food/{food_id}`, `POST /api/v1/food/recommend`
  - Travel (P1): `GET /api/v1/travel/quick-search`, `GET /api/v1/travel/{destination_id}` (`POST /api/v1/travel/recommend` chỉ làm khi được chốt)
  - Quick Search dùng `GET`; Recommendation dùng `POST`. Validate số âm, `limit`, enum không hợp lệ; frontend không tự tính điểm cuối cùng.

---

## 5. Quy tắc Frontend & Design System (`frontend/`)

- Dùng HTML, CSS, JavaScript thuần kết hợp **Bootstrap 5.0.2** (và **SweetAlert2** khi cần thông báo/xác nhận).
- **Không** sử dụng Tailwind CSS.
- **Không** viết JavaScript inline trong HTML và **không** dùng thuộc tính `onclick` (tách CSS/JS ra file riêng, dùng `addEventListener`).
- Khi chèn dữ liệu người dùng nhập vào `innerHTML`, luôn bọc `escapeHtml(...)` (`frontend/js/utils.js`) để chống XSS.
- **Thứ tự import CSS bắt buộc** (điều chỉnh đường dẫn tương đối theo vị trí trang):
  1. Bootstrap 5.0.2 CSS
  2. `css/variables.css`
  3. `css/common.css`
  4. `css/components.css`
  5. CSS riêng của module (nếu có)
- **Design System (Green SaaS – Roboto):**
  - Tuân thủ bảng token trong `frontend/css/variables.css` & `frontend/docs/UI-GUIDELINES.md`: Primary `#16845B`, Primary hover `#116B49`, Primary soft `#E8F5EF`, App bg `#F5F8F6`, Surface `#FFFFFF`, Text primary `#172B23`, Text muted `#66776F`, Border `#E3EBE6`, Warning `#B7791F`, Danger `#C2413B`, Info `#2876A8`.
  - Dùng class chuẩn `.dh-btn` (`dh-btn-primary`, `dh-btn-secondary`, `dh-btn-outline`, `dh-btn-danger`), `.dh-card`, `.dh-label`, `.dh-input`, `.dh-select`, `.dh-help`, `.dh-error`.
  - **Namespace CSS module:** Chỉ viết selector có phạm vi (vd: `.food-page .food-result-card`); **không** ghi đè selector toàn cục (`button`, `.card`, `body`, `:root`) hoặc copy/sửa lại token dùng chung.
  - Không thiết kế lại shared navbar/sidebar theo từng module; đảm bảo responsive (`< 992px` sidebar collapsible, `< 768px` padding 16px, bảng cuộn ngang, form 1 cột), `:focus-visible`, `aria-label` cho nút chỉ có icon, và đầy đủ trạng thái loading / empty / error.

---

## 6. Anti-Overengineering & Chất lượng code

- **Ưu tiên cao nhất:** Simplicity over Complexity · Reusability over Duplication · Readability over Cleverness · Consistency over Personal Preference · Maintainability over Premature Abstraction.
- Triển khai đúng yêu cầu được giao; không tự ý mở rộng phạm vi.
- Không tạo class, function, file hoặc tầng abstraction trung gian chỉ để chuyển tiếp dữ liệu nếu chưa có lý do thực tế.
- Không tạo `BaseService`, `BaseRepository`, `Factory` hay `Manager` chung một cách máy móc; không thêm Design Pattern khi bài toán không cần.
- Không thêm dependency mới khi thư viện hiện tại giải quyết được (nếu bắt buộc thêm phải giải thích rõ lý do).
- Không refactor code không liên quan đến task.
- Giữ function rõ ràng, tập trung một nhiệm vụ, hạn chế lặp code và nested logic sâu; xóa import/biến thừa và code debug.
- Kiểm tra và format code Python bằng **Ruff**.

---

## 7. Git, Phối hợp nhóm & Quy trình làm việc của AI

### Git & Làm việc nhóm
- Không commit trực tiếp lên `main`; làm việc trên branch riêng theo `feature/...` hoặc `fix/...`.
- Không tự ý sửa code thuộc module của thành viên khác, không tự ý đổi tên file/thư mục/endpoint đã thống nhất, không ghi đè code hiện có khi chưa đọc kỹ.
- Không commit `.env`, mật khẩu, token hoặc dữ liệu bí mật.

### AI Working Protocol
- **Trước khi làm:** Đọc các file liên quan, kiểm tra cấu trúc hiện tại, xác định phần tái sử dụng được và phạm vi thay đổi chính xác; đề xuất phương án nếu có nhiều cách triển khai.
- **Trong khi làm:** Không tự suy diễn thêm yêu cầu; không tự ý đổi kiến trúc; không sửa file ngoài phạm vi; không hỏi xác nhận cho các quyết định kỹ thuật nhỏ đã được quy định trong rule.
- **Sau khi hoàn thành:**
  1. Liệt kê các file đã tạo hoặc chỉnh sửa.
  2. Giải thích ngắn gọn các thay đổi chính.
  3. Báo cáo dependency mới (nếu có).
  4. Chạy kiểm tra phù hợp (test, lint/Ruff, kiểm tra cú pháp).
  5. Nêu rõ phần chưa hoàn thành hoặc chưa được kiểm thử.
