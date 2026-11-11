-- =====================================================================
-- DecisionHub - Seed dữ liệu mẫu Users & Roles
--
-- Chạy SAU khi đã tạo database (sql/init.sql) và đã apply migration Alembic
-- (tạo bảng roles và users).
--
-- Lưu ý về password_hash:
--   Hash dùng cơ chế Argon2id (thư viện pwdlib, mặc định argon2 recommended).
--   Tất cả tài khoản mẫu đều dùng mật khẩu dev: Password@123
--   Đây là dữ liệu mẫu cho môi trường phát triển, KHÔNG dùng cho production.
-- =====================================================================

SET NAMES utf8mb4;

USE decision_hub;

-- ---------------------------------------------------------------------
-- Seed roles
-- INSERT IGNORE để chạy lại file không bị lỗi trùng UNIQUE.
-- ---------------------------------------------------------------------
INSERT IGNORE INTO roles (name, description) VALUES
  ('USER',  'Người dùng thông thường'),
  ('ADMIN', 'Quản trị viên hệ thống');

-- ---------------------------------------------------------------------
-- Seed users
-- Mỗi tài khoản dùng mật khẩu dev "Password@123" (đã hash Argon2id).
-- role_id được tra theo tên role để không phụ thuộc giá trị AUTO_INCREMENT.
--
-- Dùng INSERT ... SELECT ... WHERE NOT EXISTS thay vì INSERT IGNORE:
--   - Chạy lại file không tạo trùng email.
--   - Lỗi khác (ví dụ role không tồn tại, hash quá dài, vi phạm NOT NULL)
--     vẫn bị báo ra thay vì bị IGNORE bỏ qua trong im lặng.
-- ---------------------------------------------------------------------
INSERT INTO users (email, password_hash, role_id)
SELECT 'user1@example.com',
       '$argon2id$v=19$m=65536,t=3,p=4$ga4hWKOusoUARMMTIhXXTw$gskTrlvTDqFw8OL5yvS+BCULE+qer8qRwlv4n6O37w4',
       r.id
FROM roles r
WHERE r.name = 'USER'
  AND NOT EXISTS (
    SELECT 1 FROM users u WHERE u.email = 'user1@example.com'
  );

INSERT INTO users (email, password_hash, role_id)
SELECT 'user2@example.com',
       '$argon2id$v=19$m=65536,t=3,p=4$1am2cZ3a97w7qaL0fNK50Q$esKRd0rOMlSELf1zeCvtN1hgdcEZkavI6lfFLs4FvsM',
       r.id
FROM roles r
WHERE r.name = 'USER'
  AND NOT EXISTS (
    SELECT 1 FROM users u WHERE u.email = 'user2@example.com'
  );

INSERT INTO users (email, password_hash, role_id)
SELECT 'admin@example.com',
       '$argon2id$v=19$m=65536,t=3,p=4$xXBoO59lEFymXcNd5iS7/g$PE5vpfrw8bx+aQ+H9tEtTpcHrQw9zxLMtSwhE1woGAU',
       r.id
FROM roles r
WHERE r.name = 'ADMIN'
  AND NOT EXISTS (
    SELECT 1 FROM users u WHERE u.email = 'admin@example.com'
  );

INSERT INTO users (email, password_hash, role_id)
SELECT 'admin2@example.com',
       '$argon2id$v=19$m=65536,t=3,p=4$3usJH1a3vIZynPI5V92wVg$lmDaKYQH/nnIlyEDvRNbTwNT+Ldj8R1Z+4YkpeuD4lQ',
       r.id
FROM roles r
WHERE r.name = 'ADMIN'
  AND NOT EXISTS (
    SELECT 1 FROM users u WHERE u.email = 'admin2@example.com'
  );
