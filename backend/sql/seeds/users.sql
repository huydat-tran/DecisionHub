-- =====================================================================
-- DecisionHub - Seed dữ liệu mẫu Users & Roles
--
-- Chạy SAU khi đã tạo database (sql/init.sql) và đã apply migration Alembic
-- (tạo bảng roles và users).
--
-- Lưu ý về password_hash:
--   Hash dùng cơ chế bcrypt (cost factor 12), đồng bộ với app/core/security.py.
--   Tất cả tài khoản mẫu đều dùng mật khẩu dev: Password@123
--   Sinh lại hash mới khi cần (mỗi lần sinh ra salt khác nhau, đều verify được):
--     python -c "import bcrypt; print(bcrypt.hashpw(b'Password@123', bcrypt.gensalt(rounds=12)).decode())"
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
-- Mỗi tài khoản dùng mật khẩu dev "Password@123" (đã hash bcrypt).
-- role_id được tra theo tên role để không phụ thuộc giá trị AUTO_INCREMENT.
--
-- Dùng INSERT ... SELECT ... WHERE NOT EXISTS thay vì INSERT IGNORE:
--   - Chạy lại file không tạo trùng email.
--   - Lỗi khác (ví dụ role không tồn tại, hash quá dài, vi phạm NOT NULL)
--     vẫn bị báo ra thay vì bị IGNORE bỏ qua trong im lặng.
-- ---------------------------------------------------------------------
INSERT INTO users (email, password_hash, role_id)
SELECT 'user1@example.com',
       '$2b$12$Opn8Aq.OUgrSHj2jt7GAL.2cNx6f8nKoXMza8Tv46KSu3SlqdGG5G',
       r.id
FROM roles r
WHERE r.name = 'USER'
  AND NOT EXISTS (
    SELECT 1 FROM users u WHERE u.email = 'user1@example.com'
  );

INSERT INTO users (email, password_hash, role_id)
SELECT 'user2@example.com',
       '$2b$12$I3uC/DMFMDHF3jKm3fSdt.HakiCrIWof8iO7ILVpgBv5ZxhPCTg42',
       r.id
FROM roles r
WHERE r.name = 'USER'
  AND NOT EXISTS (
    SELECT 1 FROM users u WHERE u.email = 'user2@example.com'
  );

INSERT INTO users (email, password_hash, role_id)
SELECT 'admin@example.com',
       '$2b$12$7fiQXd.vGCPiXC9cxAiyHuwAHrG0nS8ZYCjjg5RcOt/gUQMBZvP.q',
       r.id
FROM roles r
WHERE r.name = 'ADMIN'
  AND NOT EXISTS (
    SELECT 1 FROM users u WHERE u.email = 'admin@example.com'
  );

INSERT INTO users (email, password_hash, role_id)
SELECT 'admin2@example.com',
       '$2b$12$BjrT.JsV.HaBndzjWrjoiOY18gEiU9DeKRPrnuS/3iGVeRaTKLDdK',
       r.id
FROM roles r
WHERE r.name = 'ADMIN'
  AND NOT EXISTS (
    SELECT 1 FROM users u WHERE u.email = 'admin2@example.com'
  );
