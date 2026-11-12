```sql
-- =====================================================================
-- DecisionHub - Seed dữ liệu mẫu Users & Roles
--
-- Chạy SAU khi đã tạo database (sql/init.sql) và đã apply migration Alembic
-- (tạo bảng roles và users).
--
-- Lưu ý về password_hash:
-- Hash dùng cơ chế bcrypt (cost factor 12), đồng bộ với app/core/security.py.
-- Tất cả tài khoản mẫu đều dùng mật khẩu dev: Password@123
-- Sinh lại hash mới khi cần:
-- python -c "import bcrypt; print(bcrypt.hashpw(b'Password@123', bcrypt.gensalt(rounds=12)).decode())"
--
-- Đây là dữ liệu mẫu cho môi trường phát triển, KHÔNG dùng cho production.
-- =====================================================================

SET NAMES utf8mb4;

USE decision_hub;


-- ---------------------------------------------------------------------
-- Seed roles
-- INSERT IGNORE để chạy lại file không bị lỗi trùng UNIQUE.
-- ---------------------------------------------------------------------

INSERT IGNORE INTO roles (name, description) VALUES
    ('USER', 'Người dùng thông thường'),
    ('ADMIN', 'Quản trị viên hệ thống');


-- ---------------------------------------------------------------------
-- Seed users
-- Mỗi tài khoản dùng mật khẩu dev "Password@123" (đã hash bcrypt).
-- Username phải duy nhất theo ràng buộc UNIQUE của bảng users.
-- role_id được tra theo tên role để không phụ thuộc AUTO_INCREMENT.
--
-- Dùng INSERT ... SELECT ... WHERE NOT EXISTS:
-- - Chạy lại file không tạo trùng email.
-- - Lỗi khác vẫn được báo ra thay vì bị INSERT IGNORE bỏ qua.
-- ---------------------------------------------------------------------


-- USER 1
INSERT INTO users (username, email, password_hash, role_id)
SELECT
    'user1',
    'user1@example.com',
    '$2b$12$Opn8Aq.OUgrSHj2jt7GAL.2cNx6f8nKoXMza8Tv46KSu3SlqdGG5G',
    r.id
FROM roles r
WHERE r.name = 'USER'
  AND NOT EXISTS (
      SELECT 1
      FROM users u
      WHERE u.email = 'user1@example.com'
  );


-- USER 2
INSERT INTO users (username, email, password_hash, role_id)
SELECT
    'user2',
    'user2@example.com',
    '$2b$12$I3uC/DMFMDHF3jKm3fSdt.HakiCrIWof8iO7ILVpgBv5ZxhPCTg42',
    r.id
FROM roles r
WHERE r.name = 'USER'
  AND NOT EXISTS (
      SELECT 1
      FROM users u
      WHERE u.email = 'user2@example.com'
  );


-- ADMIN 1
INSERT INTO users (username, email, password_hash, role_id)
SELECT
    'admin',
    'admin@example.com',
    '$2b$12$7fiQXd.vGCPiXC9cxAiyHuwAHrG0n8S8ZYCjjg5RcOt/gUQMBZvP.q',
    r.id
FROM roles r
WHERE r.name = 'ADMIN'
  AND NOT EXISTS (
      SELECT 1
      FROM users u
      WHERE u.email = 'admin@example.com'
  );


-- ADMIN 2
INSERT INTO users (username, email, password_hash, role_id)
SELECT
    'admin2',
    'admin2@example.com',
    '$2b$12$BjrT.JsV.HaBndzjWrjoiOY18gEiU9DeKRPrnuS/3iGVeRaTKLDdK',
    r.id
FROM roles r
WHERE r.name = 'ADMIN'
  AND NOT EXISTS (
      SELECT 1
      FROM users u
      WHERE u.email = 'admin2@example.com'
  );


-- ---------------------------------------------------------------------
-- Kiểm tra dữ liệu sau khi seed
-- ---------------------------------------------------------------------

SELECT
    u.id,
    u.username,
    u.email,
    r.name AS role_name,
    u.created_at
FROM users u
JOIN roles r ON u.role_id = r.id
ORDER BY u.id;
```