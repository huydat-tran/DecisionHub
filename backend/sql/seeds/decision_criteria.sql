-- =====================================================================
-- DecisionHub - Seed dữ liệu mẫu Decision Criteria
--
-- Chạy SAU khi đã tạo database (sql/init.sql) và đã apply migration Alembic
-- (bảng decision_criteria có cột domain).
--
-- Food giữ nguyên rubric DecisionHub.md (Mục 7.4):
--   - Giá: min, 0.4000
--   - Mức phù hợp nhu cầu/khẩu vị: max, 0.3500
--   - Thời gian chuẩn bị: min, 0.2500
--
-- Travel (mặc định, tổng weight = 1):
--   - cost: min, 0.4000
--   - duration: min, 0.3000
--   - activities: max, 0.3000
--
-- Xác định bản ghi theo (domain, name). Chạy lại không tạo trùng và
-- không cập nhật weight của Food.
-- =====================================================================

SET NAMES utf8mb4;

USE decision_hub;

INSERT INTO decision_criteria (domain, name, direction, weight)
SELECT 'food', 'Giá', 'min', 0.4000
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc
  WHERE dc.domain = 'food' AND dc.name = 'Giá'
);

INSERT INTO decision_criteria (domain, name, direction, weight)
SELECT 'food', 'Mức phù hợp nhu cầu/khẩu vị', 'max', 0.3500
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc
  WHERE dc.domain = 'food' AND dc.name = 'Mức phù hợp nhu cầu/khẩu vị'
);

INSERT INTO decision_criteria (domain, name, direction, weight)
SELECT 'food', 'Thời gian chuẩn bị', 'min', 0.2500
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc
  WHERE dc.domain = 'food' AND dc.name = 'Thời gian chuẩn bị'
);

INSERT INTO decision_criteria (domain, name, direction, weight)
SELECT 'travel', 'cost', 'min', 0.4000
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc
  WHERE dc.domain = 'travel' AND dc.name = 'cost'
);

INSERT INTO decision_criteria (domain, name, direction, weight)
SELECT 'travel', 'duration', 'min', 0.3000
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc
  WHERE dc.domain = 'travel' AND dc.name = 'duration'
);

INSERT INTO decision_criteria (domain, name, direction, weight)
SELECT 'travel', 'activities', 'max', 0.3000
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc
  WHERE dc.domain = 'travel' AND dc.name = 'activities'
);
