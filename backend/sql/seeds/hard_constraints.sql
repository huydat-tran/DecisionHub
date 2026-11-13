-- =====================================================================
-- DecisionHub - Seed dữ liệu mẫu Hard Constraints
--
-- Chạy SAU khi đã tạo database (sql/init.sql) và đã apply migration Alembic
-- (tạo bảng hard_constraints).
--
-- Dữ liệu mẫu dựa theo mục Lọc bắt buộc của Food trong DecisionHub.md (Mục 4.3):
--   - price <= max_price (Ngân sách tối đa)
--   - meal_type = meal_type (Loại bữa ăn bắt buộc)
--   - prep_time <= max_prep_time (Thời gian chuẩn bị tối đa)
--   - ingredients not_in excluded_ingredients (Nguyên liệu cần tránh)
-- =====================================================================

SET NAMES utf8mb4;

USE decision_hub;

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'food', 'Ngân sách tối đa', 'price', '<=',
       'Loại món có giá vượt quá ngân sách tối đa người dùng chọn', 1
WHERE NOT EXISTS (
  SELECT 1 FROM hard_constraints hc
  WHERE hc.domain = 'food' AND hc.name = 'Ngân sách tối đa'
);

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'food', 'Loại bữa ăn', 'meal_type', '=',
       'Loại món không đúng loại bữa ăn bắt buộc được chọn', 1
WHERE NOT EXISTS (
  SELECT 1 FROM hard_constraints hc
  WHERE hc.domain = 'food' AND hc.name = 'Loại bữa ăn'
);

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'food', 'Thời gian chuẩn bị tối đa', 'prep_time', '<=',
       'Loại món có thời gian chuẩn bị vượt quá giới hạn tối đa', 1
WHERE NOT EXISTS (
  SELECT 1 FROM hard_constraints hc
  WHERE hc.domain = 'food' AND hc.name = 'Thời gian chuẩn bị tối đa'
);

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'food', 'Nguyên liệu cần tránh', 'ingredients', 'not_in',
       'Loại món có chứa nguyên liệu thuộc danh sách cần tránh', 1
WHERE NOT EXISTS (
  SELECT 1 FROM hard_constraints hc
  WHERE hc.domain = 'food' AND hc.name = 'Nguyên liệu cần tránh'
);

-- =====================================================================
-- Hard constraints cho Travel
-- =====================================================================
INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'travel', 'Ngân sách tối đa', 'estimated_cost', '<=',
       'Loại trừ địa điểm có chi phí vượt quá ngân sách tối đa', 1
WHERE NOT EXISTS (
  SELECT 1 FROM hard_constraints hc
  WHERE hc.domain = 'travel' AND hc.name = 'Ngân sách tối đa'
);

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'travel', 'Thời lượng tối đa', 'estimated_duration', '<=',
       'Loại trừ địa điểm có thời lượng vượt quá quỹ thời gian', 1
WHERE NOT EXISTS (
  SELECT 1 FROM hard_constraints hc
  WHERE hc.domain = 'travel' AND hc.name = 'Thời lượng tối đa'
);

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'travel', 'Khu vực ưu tiên', 'region', 'in',
       'Chỉ giữ các địa điểm thuộc khu vực người dùng lựa chọn', 1
WHERE NOT EXISTS (
  SELECT 1 FROM hard_constraints hc
  WHERE hc.domain = 'travel' AND hc.name = 'Khu vực ưu tiên'
);

INSERT INTO hard_constraints (domain, name, field_name, operator, description, is_active)
SELECT 'travel', 'Loại hình bắt buộc', 'activity_type', '=',
       'Chỉ giữ đúng loại hình trải nghiệm được yêu cầu', 1
WHERE NOT EXISTS (
  SELECT 1 FROM hard_constraints hc
  WHERE hc.domain = 'travel' AND hc.name = 'Loại hình bắt buộc'
);
