-- =====================================================================
-- DecisionHub - Thiết kế bảng decisions & Seed dữ liệu mẫu Lịch sử quyết định
--
-- Mục đích:
--   1. Tạo bảng `decisions` lưu lịch sử các quyết định của người dùng.
--   2. Lưu dữ liệu đầu vào (`input_snapshot`) và kết quả (`result_snapshot`)
--      dưới dạng JSON tại thời điểm thực hiện đề xuất (Food / Travel).
--   3. Seed dữ liệu mẫu an toàn (chạy lại nhiều lần không bị trùng lặp).
--
-- Chạy SAU khi đã tạo database (sql/init.sql), đã tạo bảng users
-- (alembic upgrade head) và đã chạy sql/seeds/users.sql.
-- =====================================================================

SET NAMES utf8mb4;

USE decision_hub;

-- ---------------------------------------------------------------------
-- 1. Tạo bảng decisions
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS decisions (
    id BIGINT NOT NULL AUTO_INCREMENT
        COMMENT 'Khóa chính tự tăng định danh phiên quyết định',

    user_id BIGINT NOT NULL
        COMMENT 'ID người dùng thực hiện quyết định (FK -> users.id)',

    domain VARCHAR(20) NOT NULL
        COMMENT 'Phân loại miền quyết định: food (ăn uống) hoặc travel (du lịch)',

    input_snapshot JSON NOT NULL
        COMMENT 'Snapshot JSON toàn bộ dữ liệu đầu vào tại thời điểm đề xuất (tiêu chí, điều kiện lọc, trọng số WSM)',

    result_snapshot JSON NOT NULL
        COMMENT 'Snapshot JSON kết quả đề xuất (danh sách phương án xếp hạng, điểm số, lý do giải thích, thống kê bị loại)',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        COMMENT 'Thời điểm tạo quyết định',

    -- Ràng buộc khóa chính
    CONSTRAINT pk_decisions PRIMARY KEY (id),

    -- Ràng buộc khóa ngoại tham chiếu bảng users(id)
    -- ON DELETE CASCADE: Khi xóa tài khoản người dùng, tự động xóa lịch sử của người dùng đó, tránh dữ liệu mồ côi.
    -- ON UPDATE CASCADE: Đồng bộ khi ID người dùng thay đổi.
    CONSTRAINT fk_decisions_user FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    -- Ràng buộc miền giá trị domain hợp lệ (MySQL 8.0.16+ thực thi CHECK constraint)
    CONSTRAINT ck_decisions_domain CHECK (domain IN ('food', 'travel')),

    -- Ràng buộc đảm bảo input_snapshot và result_snapshot là JSON Object hợp lệ
    CONSTRAINT ck_decisions_input_json_object CHECK (JSON_TYPE(input_snapshot) = 'OBJECT'),
    CONSTRAINT ck_decisions_result_json_object CHECK (JSON_TYPE(result_snapshot) = 'OBJECT'),

    -- Các chỉ mục (INDEX) tối ưu truy vấn lịch sử
    INDEX idx_decisions_user_id (user_id),
    INDEX idx_decisions_user_created_at (user_id, created_at DESC),
    INDEX idx_decisions_user_domain_created_at (user_id, domain, created_at DESC)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Bảng lưu lịch sử các phiên quyết định (input_snapshot và result_snapshot) của người dùng';


-- ---------------------------------------------------------------------
-- 2. Seed dữ liệu mẫu lịch sử quyết định (Food & Travel)
-- Tra cứu user_id theo email từ bảng users để không phụ thuộc AUTO_INCREMENT.
-- Dùng INSERT ... SELECT ... WHERE NOT EXISTS để chạy lại không tạo bản ghi trùng.
-- ---------------------------------------------------------------------

-- Mẫu 1: Lịch sử quyết định Food của user1@example.com
INSERT INTO decisions (user_id, domain, input_snapshot, result_snapshot)
SELECT
    u.id,
    'food',
    JSON_OBJECT(
        'budget_max', 50000,
        'meal_type', 'lunch',
        'max_prep_time', 25,
        'excluded_ingredients', JSON_ARRAY('Đậu phộng', 'Tôm sú'),
        'preferred_tags', JSON_ARRAY('truyền thống', 'đậm đà'),
        'limit', 5,
        'scoring', JSON_OBJECT(
            'method', 'WSM',
            'weights', JSON_OBJECT('price', 0.40, 'preference', 0.35, 'prep_time', 0.25)
        )
    ),
    JSON_OBJECT(
        'has_valid_candidates', true,
        'message', 'Đánh giá thành công 2 phương án hợp lệ.',
        'total', 2,
        'total_excluded', 1,
        'limit', 5,
        'items', JSON_ARRAY(
            JSON_OBJECT(
                'food_id', 3,
                'id', 3,
                'name', 'Bún chả Hà Nội',
                'price', 50000,
                'meal_type', 'lunch',
                'prep_time', 20,
                'tags', JSON_ARRAY('truyền thống', 'đậm đà'),
                'score', 65.0,
                'total_score', 65.0,
                'rank', 1,
                'criteria_scores', JSON_OBJECT('price', 100.0, 'preference', 0.0, 'prep_time', 100.0),
                'reasons', JSON_ARRAY(
                    'Giá 50.000đ nằm trong ngân sách tối đa 50.000đ',
                    'Phù hợp khẩu vị ưu tiên: truyền thống, đậm đà',
                    'Thời gian chuẩn bị 20 phút (đạt giới hạn ≤ 25 phút)'
                )
            ),
            JSON_OBJECT(
                'food_id', 5,
                'id', 5,
                'name', 'Cơm chiên đậu hũ nấm',
                'price', 35000,
                'meal_type', 'lunch',
                'prep_time', 12,
                'tags', JSON_ARRAY('chay', 'thanh đạm', 'nhanh'),
                'score', 60.0,
                'total_score', 60.0,
                'rank', 2,
                'criteria_scores', JSON_OBJECT('price', 0.0, 'preference', 100.0, 'prep_time', 100.0),
                'reasons', JSON_ARRAY(
                    'Giá 35.000đ nằm trong ngân sách tối đa 50.000đ',
                    'Phù hợp cho bữa lunch',
                    'Thời gian chuẩn bị 12 phút (đạt giới hạn ≤ 25 phút)'
                )
            )
        ),
        'excluded_items', JSON_ARRAY(
            JSON_OBJECT(
                'id', 4,
                'name', 'Cơm tấm sườn bì chả',
                'status', 'excluded',
                'is_excluded', true,
                'exclusion_reason', 'Giá (55,000đ) vượt quá ngân sách tối đa (50,000đ).',
                'exclusion_reasons', JSON_ARRAY('Giá (55,000đ) vượt quá ngân sách tối đa (50,000đ).')
            )
        )
    )
FROM users u
WHERE u.email = 'user1@example.com'
  AND NOT EXISTS (
      SELECT 1
      FROM decisions d
      WHERE d.user_id = u.id
        AND d.domain = 'food'
        AND JSON_EXTRACT(d.input_snapshot, '$.budget_max') = 50000
        AND JSON_UNQUOTE(JSON_EXTRACT(d.input_snapshot, '$.meal_type')) = 'lunch'
  );


-- Mẫu 2: Lịch sử quyết định Travel của user1@example.com
INSERT INTO decisions (user_id, domain, input_snapshot, result_snapshot)
SELECT
    u.id,
    'travel',
    JSON_OBJECT(
        'budget_max', 2000000,
        'region', 'Bắc',
        'max_duration', 24.0,
        'activity_type', 'Khám phá thiên nhiên',
        'preferred_highlights', JSON_ARRAY('cáp treo', 'ruộng bậc thang'),
        'limit', 5,
        'scoring', JSON_OBJECT(
            'method', 'WSM',
            'weights', JSON_OBJECT('estimated_cost', 0.40, 'estimated_duration', 0.30, 'activities', 0.30)
        )
    ),
    JSON_OBJECT(
        'has_valid_candidates', true,
        'message', 'Đánh giá thành công 2 phương án hợp lệ.',
        'total', 2,
        'total_excluded', 0,
        'limit', 5,
        'items', JSON_ARRAY(
            JSON_OBJECT(
                'destination_id', 2,
                'id', 2,
                'name', 'Quần thể danh thắng Tràng An',
                'province_city', 'Ninh Bình',
                'region', 'Bắc',
                'estimated_cost', 450000,
                'estimated_duration', 6.0,
                'activity_type', 'Khám phá thiên nhiên',
                'rating', 4.9,
                'score', 88.5,
                'total_score', 88.5,
                'rank', 1,
                'criteria_scores', JSON_OBJECT(
                    'estimated_cost', 100.0,
                    'estimated_duration', 100.0,
                    'activities', 61.67
                ),
                'reasons', JSON_ARRAY(
                    'Chi phí tham khảo 450.000đ nằm trong ngân sách 2.000.000đ',
                    'Thời lượng trải nghiệm 6.0 giờ phù hợp lịch trình trong ngày',
                    'Thuộc khu vực Bắc, loại hình Khám phá thiên nhiên'
                )
            )
        ),
        'excluded_items', JSON_ARRAY()
    )
FROM users u
WHERE u.email = 'user1@example.com'
  AND NOT EXISTS (
      SELECT 1
      FROM decisions d
      WHERE d.user_id = u.id
        AND d.domain = 'travel'
        AND JSON_EXTRACT(d.input_snapshot, '$.budget_max') = 2000000
        AND JSON_UNQUOTE(JSON_EXTRACT(d.input_snapshot, '$.region')) = 'Bắc'
  );


-- ---------------------------------------------------------------------
-- 3. Kiểm tra dữ liệu lịch sử sau khi tạo bảng và seed
-- ---------------------------------------------------------------------
SELECT
    d.id AS decision_id,
    u.username,
    u.email,
    d.domain,
    JSON_UNQUOTE(JSON_EXTRACT(d.input_snapshot, '$.budget_max')) AS budget_max,
    JSON_UNQUOTE(JSON_EXTRACT(d.result_snapshot, '$.items[0].name')) AS top1_recommendation,
    JSON_UNQUOTE(JSON_EXTRACT(d.result_snapshot, '$.items[0].total_score')) AS top1_score,
    d.created_at
FROM decisions d
JOIN users u ON d.user_id = u.id
ORDER BY d.created_at DESC, d.id DESC;

