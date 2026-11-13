-- =====================================================================
-- DecisionHub - Single All-in-One Database Setup Script
--
-- Đồng bộ chuẩn 1:1 theo toàn bộ Alembic migrations (alembic/versions/):
--   - 1b04f303d588: roles, users
--   - 0ffe6300e06b: users.username
--   - b3f74c8eecf8: decision_criteria
--   - f92a86007329: hard_constraints
--   - e59757051dea: travel_places
--
-- File này tổng hợp:
--   1. Tạo cấu trúc toàn bộ các bảng (CREATE TABLE IF NOT EXISTS)
--   2. Nạp dữ liệu mẫu (Roles, Users, Food & Travel Criteria, Hard Constraints, Travel Places)
--
-- Chạy 1 lệnh duy nhất:
--   mysql -u root -p decision_hub < backend/sql/setup.sql
-- =====================================================================

SET NAMES utf8mb4;
USE decision_hub;

-- ---------------------------------------------------------------------
-- 1. BẢNG roles (Alembic: 1b04f303d588)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
  id          BIGINT       NOT NULL AUTO_INCREMENT,
  name        VARCHAR(20)  NOT NULL,
  description VARCHAR(255) NULL,
  CONSTRAINT pk_roles PRIMARY KEY (id),
  CONSTRAINT uq_roles_name UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2. BẢNG users (Alembic: 1b04f303d588 + 0ffe6300e06b)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  username      VARCHAR(50)  NULL,
  email         VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role_id       BIGINT       NOT NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_users PRIMARY KEY (id),
  CONSTRAINT uq_users_email UNIQUE (email),
  CONSTRAINT uq_users_username UNIQUE (username),
  KEY idx_users_role_id (role_id),
  CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles (id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 3. BẢNG decision_criteria (Alembic: b3f74c8eecf8)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS decision_criteria (
  id        BIGINT         NOT NULL AUTO_INCREMENT,
  name      VARCHAR(100)   NOT NULL,
  direction VARCHAR(10)    NOT NULL,
  weight    NUMERIC(5, 4)  NOT NULL,
  CONSTRAINT pk_decision_criteria PRIMARY KEY (id),
  CONSTRAINT ck_decision_criteria_direction CHECK (direction IN ('min', 'max')),
  CONSTRAINT ck_decision_criteria_weight CHECK (weight >= 0 AND weight <= 1),
  CONSTRAINT uq_decision_criteria_name UNIQUE (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 4. BẢNG hard_constraints (Alembic: f92a86007329)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hard_constraints (
  id          BIGINT       NOT NULL AUTO_INCREMENT,
  domain      VARCHAR(20)  NOT NULL,
  name        VARCHAR(100) NOT NULL,
  field_name  VARCHAR(50)  NOT NULL,
  operator    VARCHAR(20)  NOT NULL,
  description VARCHAR(255) NULL,
  is_active   BOOLEAN      NOT NULL DEFAULT 1,
  CONSTRAINT pk_hard_constraints PRIMARY KEY (id),
  CONSTRAINT ck_hard_constraints_domain CHECK (domain IN ('food', 'travel')),
  CONSTRAINT ck_hard_constraints_operator CHECK (operator IN ('<=', '>=', '=', '!=', 'in', 'not_in')),
  CONSTRAINT uq_hard_constraints_domain_name UNIQUE (domain, name),
  INDEX idx_hard_constraints_domain_active (domain, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 5. BẢNG travel_places (Alembic: e59757051dea)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS travel_places (
  id                 BIGINT        NOT NULL AUTO_INCREMENT COMMENT 'Khóa chính tự tăng',
  name               VARCHAR(200)  NOT NULL COMMENT 'Tên địa điểm',
  province_city      VARCHAR(100)  NOT NULL COMMENT 'Tỉnh hoặc Thành phố',
  region             ENUM('Bắc', 'Trung', 'Nam', 'Tây Nguyên', 'Tây Nam Bộ') NOT NULL COMMENT 'Khu vực địa lý',
  estimated_cost     INT           NOT NULL DEFAULT 0 COMMENT 'Chi phí tham khảo trung bình (VND)',
  estimated_duration NUMERIC(4, 1) NOT NULL DEFAULT 1.0 COMMENT 'Thời lượng ước tính (giờ)',
  activity_type      VARCHAR(100)  NOT NULL COMMENT 'Loại hình trải nghiệm chính',
  highlights         TEXT          NULL COMMENT 'Hoạt động nổi bật',
  description        TEXT          NULL COMMENT 'Mô tả chi tiết',
  image_url          VARCHAR(500)  NULL COMMENT 'URL ảnh minh họa',
  rating             NUMERIC(2, 1) NOT NULL DEFAULT 4.5 COMMENT 'Điểm đánh giá (1.0 - 5.0)',
  is_active          BOOLEAN       NOT NULL DEFAULT 1 COMMENT 'Trạng thái hoạt động',
  created_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT pk_travel_places PRIMARY KEY (id),
  CONSTRAINT uq_travel_places_name UNIQUE (name),
  INDEX idx_travel_places_region (region),
  INDEX idx_travel_places_cost (estimated_cost),
  INDEX idx_travel_places_duration (estimated_duration),
  INDEX idx_travel_places_activity_type (activity_type),
  INDEX idx_travel_places_is_active (is_active),
  INDEX idx_travel_places_composite_filter (region, estimated_cost, estimated_duration)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================
-- NẠP DỮ LIỆU MẪU (SEEDS) - AN TOÀN KHI CHẠY LẠI NHIỀU LẦN
-- =====================================================================

-- Seed Roles
INSERT IGNORE INTO roles (name, description) VALUES
  ('USER',  'Người dùng thông thường'),
  ('ADMIN', 'Quản trị viên hệ thống');

-- Seed Users (mật khẩu dev: Password@123, hash Argon2id)
INSERT INTO users (username, email, password_hash, role_id)
SELECT 'user1', 'user1@example.com',
       '$argon2id$v=19$m=65536,t=3,p=4$ga4hWKOusoUARMMTIhXXTw$gskTrlvTDqFw8OL5yvS+BCULE+qer8qRwlv4n6O37w4',
       r.id
FROM roles r WHERE r.name = 'USER'
AND NOT EXISTS (SELECT 1 FROM users u WHERE u.email = 'user1@example.com');

INSERT INTO users (username, email, password_hash, role_id)
SELECT 'user2', 'user2@example.com',
       '$argon2id$v=19$m=65536,t=3,p=4$1am2cZ3a97w7qaL0fNK50Q$esKRd0rOMlSELf1zeCvtN1hgdcEZkavI6lfFLs4FvsM',
       r.id
FROM roles r WHERE r.name = 'USER'
AND NOT EXISTS (SELECT 1 FROM users u WHERE u.email = 'user2@example.com');

INSERT INTO users (username, email, password_hash, role_id)
SELECT 'admin', 'admin@example.com',
       '$argon2id$v=19$m=65536,t=3,p=4$xXBoO59lEFymXcNd5iS7/g$PE5vpfrw8bx+aQ+H9tEtTpcHrQw9zxLMtSwhE1woGAU',
       r.id
FROM roles r WHERE r.name = 'ADMIN'
AND NOT EXISTS (SELECT 1 FROM users u WHERE u.email = 'admin@example.com');

-- Seed Decision Criteria (Food & Travel)
INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Giá', 'min', 0.4000
WHERE NOT EXISTS (SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Giá');

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Mức phù hợp nhu cầu/khẩu vị', 'max', 0.3500
WHERE NOT EXISTS (SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Mức phù hợp nhu cầu/khẩu vị');

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Thời gian chuẩn bị', 'min', 0.2500
WHERE NOT EXISTS (SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Thời gian chuẩn bị');

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Chi phí du lịch', 'min', 0.4000
WHERE NOT EXISTS (SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Chi phí du lịch');

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Mức phù hợp sở thích', 'max', 0.3500
WHERE NOT EXISTS (SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Mức phù hợp sở thích');

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Thời lượng trải nghiệm', 'min', 0.2500
WHERE NOT EXISTS (SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Thời lượng trải nghiệm');

-- Seed Hard Constraints (Food & Travel)
INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'food', 'Ngân sách tối đa', 'price', '<=',
       'Loại món có giá vượt quá ngân sách tối đa người dùng chọn', 1
WHERE NOT EXISTS (SELECT 1 FROM hard_constraints hc WHERE hc.domain = 'food' AND hc.name = 'Ngân sách tối đa');

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'food', 'Loại bữa ăn', 'meal_type', '=',
       'Loại món không đúng loại bữa ăn bắt buộc được chọn', 1
WHERE NOT EXISTS (SELECT 1 FROM hard_constraints hc WHERE hc.domain = 'food' AND hc.name = 'Loại bữa ăn');

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'food', 'Thời gian chuẩn bị tối đa', 'prep_time', '<=',
       'Loại món có thời gian chuẩn bị vượt quá giới hạn tối đa', 1
WHERE NOT EXISTS (SELECT 1 FROM hard_constraints hc WHERE hc.domain = 'food' AND hc.name = 'Thời gian chuẩn bị tối đa');

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'food', 'Nguyên liệu cần tránh', 'ingredients', 'not_in',
       'Loại món có chứa nguyên liệu thuộc danh sách cần tránh', 1
WHERE NOT EXISTS (SELECT 1 FROM hard_constraints hc WHERE hc.domain = 'food' AND hc.name = 'Nguyên liệu cần tránh');

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'travel', 'Ngân sách tối đa', 'estimated_cost', '<=',
       'Loại trừ địa điểm có chi phí vượt quá ngân sách tối đa', 1
WHERE NOT EXISTS (SELECT 1 FROM hard_constraints hc WHERE hc.domain = 'travel' AND hc.name = 'Ngân sách tối đa');

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'travel', 'Thời lượng tối đa', 'estimated_duration', '<=',
       'Loại trừ địa điểm có thời lượng vượt quá quỹ thời gian', 1
WHERE NOT EXISTS (SELECT 1 FROM hard_constraints hc WHERE hc.domain = 'travel' AND hc.name = 'Thời lượng tối đa');

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'travel', 'Khu vực ưu tiên', 'region', 'in',
       'Chỉ giữ các địa điểm thuộc khu vực người dùng lựa chọn', 1
WHERE NOT EXISTS (SELECT 1 FROM hard_constraints hc WHERE hc.domain = 'travel' AND hc.name = 'Khu vực ưu tiên');

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'travel', 'Loại hình bắt buộc', 'activity_type', '=',
       'Chỉ giữ đúng loại hình trải nghiệm được yêu cầu', 1
WHERE NOT EXISTS (SELECT 1 FROM hard_constraints hc WHERE hc.domain = 'travel' AND hc.name = 'Loại hình bắt buộc');

-- Seed Travel Places (15 địa điểm)
INSERT IGNORE INTO travel_places
  (name, province_city, region, estimated_cost, estimated_duration, activity_type, highlights, description, image_url, rating, is_active)
VALUES
(
  'Phố cổ Hội An', 'Quảng Nam', 'Trung', 500000, 8.0, 'Văn hóa lịch sử',
  'Thả đèn hoa đăng trên sông Hoài, Thưởng thức cao lầu và bánh mì Phượng, Check-in Chùa Cầu, Đạp xe tham quan làng gốm Thanh Hà',
  'Đô thị cổ được UNESCO công nhận là Di sản Thế giới với những ngôi nhà cổ sơn vàng, giàn hoa giấy rực rỡ và lồng đèn lung linh về đêm.',
  'https://images.unsplash.com/photo-1559592413-7cec4d0cae2b', 4.8, 1
),
(
  'Quần thể danh thắng Tràng An', 'Ninh Bình', 'Bắc', 450000, 6.0, 'Khám phá thiên nhiên',
  'Đi thuyền nan ngắm hang động tự nhiên, Viếng đền Trình và phủ Khống, Chụp ảnh bối cảnh phim trường Kong: Skull Island, Leo núi ngắm thung lũng đá vôi',
  'Di sản thế giới kép đầu tiên tại Đông Nam Á, nổi tiếng với hệ sinh thái đất ngập nước và cảnh quan hang động núi đá vôi kỳ vĩ.',
  'https://images.unsplash.com/photo-1528127269322-539801943592', 4.9, 1
),
(
  'Đảo ngọc Phú Quốc', 'Kiên Giang', 'Nam', 3500000, 48.0, 'Nghỉ dưỡng biển',
  'Ngắm hoàng hôn Bãi Sao và Sunset Sanato, Lặn biển ngắm san hô tại hòn Móng Tay, Thưởng thức hải sản Hàm Ninh, Khám phá cáp treo Hòn Thơm',
  'Hòn đảo lớn nhất Việt Nam sở hữu bãi cát trắng mịn, nước biển trong xanh và hệ sinh thái giải trí, nghỉ dưỡng đẳng cấp quốc tế.',
  'https://images.unsplash.com/photo-1583417319070-4a69db38a482', 4.7, 1
),
(
  'Vịnh Hạ Long', 'Quảng Ninh', 'Bắc', 1200000, 24.0, 'Khám phá thiên nhiên',
  'Ngủ đêm trên du thuyền vịnh Hạ Long, Chèo thuyền kayak qua hang Luồn, Tham quan hang Sửng Sốt, Tắm biển tại đảo Ti Tốp',
  'Kỳ quan thiên nhiên thế giới với hàng nghìn đảo đá vôi nhô lên từ làn nước xanh ngọc bích.',
  'https://images.unsplash.com/photo-1528127269322-539801943592', 4.8, 1
),
(
  'Bà Nà Hills & Cầu Vàng', 'Đà Nẵng', 'Trung', 950000, 10.0, 'Vui chơi giải trí',
  'Check-in Cầu Vàng bàn tay khổng lồ, Trải nghiệm tuyến cáp treo đạt nhiều kỷ lục thế giới, Vui chơi tại Fantasy Park, Tham quan Làng Pháp cổ kính',
  'Khu du lịch trên đỉnh núi Chúa với khí hậu 4 mùa trong một ngày và cây Cầu Vàng nổi tiếng toàn cầu.',
  'https://images.unsplash.com/photo-1570789210967-2cac24afeb00', 4.6, 1
),
(
  'Thung lũng Mường Hoa & Fansipan', 'Lào Cai', 'Bắc', 1500000, 36.0, 'Khám phá thiên nhiên',
  'Chinh phục đỉnh Fansipan 3.143m nóc nhà Đông Dương, Đi tàu hỏa leo núi Mường Hoa ngắm ruộng bậc thang, Trekking bản Cát Cát, Thưởng thức thắng cố Sa Pa',
  'Thị xã mờ sương với đỉnh Fansipan hùng vĩ, những thửa ruộng bậc thang kỳ vĩ và nét văn hóa độc đáo của đồng bào H\'Mông, Dao.',
  'https://images.unsplash.com/photo-1544644181-1484b3fdfc62', 4.7, 1
),
(
  'Thác Bản Giốc', 'Cao Bằng', 'Bắc', 800000, 18.0, 'Khám phá thiên nhiên',
  'Ngắm thác nước tự nhiên lớn thứ 4 thế giới trên biên giới, Đi bè mảng đến chân thác cảm nhận làn nước mát lạnh, Thăm chùa Phật Tích Trúc Lâm Bản Giốc',
  'Thác nước hùng vĩ bậc nhất Đông Nam Á, nằm giữa khung cảnh núi rừng biên cương kỳ vĩ.',
  'https://images.unsplash.com/photo-1506744038136-46273834b3fb', 4.8, 1
),
(
  'Hồ Tuyền Lâm & Đồi chè Cầu Đất', 'Lâm Đồng', 'Tây Nguyên', 700000, 16.0, 'Khám phá thiên nhiên',
  'Chèo SUP đón bình minh trên hồ Tuyền Lâm, Săn mây sáng sớm tại đồi chè Cầu Đất, Thưởng thức cà phê arabica nguyên chất, Cắm trại rừng thông',
  'Thành phố ngàn hoa với khí hậu se lạnh quanh năm, những đồi thông thơ mộng và không gian thanh bình lý tưởng để thư giãn.',
  'https://images.unsplash.com/photo-1569154941061-e231b4725ef1', 4.5, 1
),
(
  'Vườn quốc gia Yok Đôn', 'Đắk Lắk', 'Tây Nguyên', 650000, 12.0, 'Khám phá thiên nhiên',
  'Trải nghiệm mô hình ngắm voi thân thiện trong môi trường bán hoang dã, Trekking rừng khộp nguyên sinh, Thăm buôn Đôn và tìm hiểu văn hóa người Ê Đê',
  'Vườn quốc gia lớn thứ 2 Việt Nam, nơi bảo tồn hệ sinh thái rừng khộp độc đáo và quần thể voi châu Á.',
  'https://images.unsplash.com/photo-1551632811-561732d1e306', 4.4, 1
),
(
  'Chợ nổi Cái Răng', 'Cần Thơ', 'Tây Nam Bộ', 300000, 5.0, 'Sinh thái sông nước',
  'Đi ghe máy ngắm bình minh trên sông Hậu, Thưởng thức hủ tiếu gõ và cà phê ngay trên sông, Tìm hiểu cây bẹo bán hàng độc đáo, Thăm lò hủ tiếu truyền thống',
  'Chợ nổi đầu mối lớn nhất miền Tây Nam Bộ, lưu giữ trọn vẹn nét văn hóa giao thương sông nước đặc sắc của người dân Nam Bộ.',
  'https://images.unsplash.com/photo-1508873696983-2df5293cb32b', 4.5, 1
),
(
  'Rừng tràm Trà Sư', 'An Giang', 'Tây Nam Bộ', 350000, 6.0, 'Sinh thái sông nước',
  'Đi xuồng ba lá lướt trên thảm bèo cám xanh mướt, Ngắm các loài chim nước quý hiếm từ đài quan sát cao 14m, Chụp ảnh cây cầu tre vạn bước xuyên rừng',
  'Khu rừng tràm ngập nước tiêu biểu cho vùng Tây sông Hậu với hệ sinh thái phong phú và cảnh sắc xanh mướt ngút ngàn.',
  'https://images.unsplash.com/photo-1507525428034-b723cf961d3e', 4.6, 1
),
(
  'Quần đảo Côn Đảo', 'Bà Rịa - Vũng Tàu', 'Nam', 3000000, 36.0, 'Nghỉ dưỡng biển',
  'Viếng mộ nữ anh hùng Võ Thị Sáu tại nghĩa trang Hàng Dương, Tham quan hệ thống nhà tù Côn Đảo, Lặn ngắm san hô và thả rùa con về biển tại Hòn Bảy Cạnh',
  'Vùng đất thiêng liêng vừa mang đậm dấu ấn lịch sử hào hùng vừa sở hữu những bãi biển nguyên sơ, trong lành bậc nhất.',
  'https://images.unsplash.com/photo-1507525428034-b723cf961d3e', 4.9, 1
),
(
  'Địa đạo Củ Chi', 'Hồ Chí Minh', 'Nam', 250000, 4.0, 'Văn hóa lịch sử',
  'Chui hầm địa đạo thu nhỏ trải nghiệm cuộc sống thời chiến, Thưởng thức khoai mì chấm muối mè dưới hầm, Xem phim tư liệu và sa bàn trận đánh',
  'Hệ thống công trình quân sự ngầm độc nhất vô nhị dài hơn 250km, biểu tượng cho lòng kiên cường và nghệ thuật chiến tranh nhân dân.',
  'https://images.unsplash.com/photo-1544644181-1484b3fdfc62', 4.6, 1
),
(
  'Đại Nội Huế & Lăng tẩm triều Nguyễn', 'Thừa Thiên Huế', 'Trung', 600000, 8.0, 'Văn hóa lịch sử',
  'Tham quan Ngọ Môn và điện Thái Hòa, Khám phá kiến trúc độc đáo của lăng Khải Định và lăng Tự Đức, Nghe ca Huế trên sông Hương về đêm',
  'Quần thể di tích Cố đô Huế lưu giữ những giá trị văn hóa, kiến trúc cung đình đỉnh cao của triều đại phong kiến cuối cùng Việt Nam.',
  'https://images.unsplash.com/photo-1559592413-7cec4d0cae2b', 4.7, 1
),
(
  'Động Phong Nha & Động Thiên Đường', 'Quảng Bình', 'Trung', 850000, 10.0, 'Khám phá thiên nhiên',
  'Đi thuyền ngược dòng sông Son vào thám hiểm động Phong Nha, Leo hơn 500 bậc thang gỗ chiêm ngưỡng thạch nhũ tráng lệ động Thiên Đường',
  'Vương quốc hang động thế giới với hệ thống sông ngầm dài nhất và những khối thạch nhũ muôn hình vạn trạng hàng triệu năm tuổi.',
  'https://images.unsplash.com/photo-1506744038136-46273834b3fb', 4.8, 1
);
