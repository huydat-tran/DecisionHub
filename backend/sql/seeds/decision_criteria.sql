-- =====================================================================
-- DecisionHub - Seed dữ liệu mẫu Decision Criteria
--
-- Chạy SAU khi đã tạo database (sql/init.sql) và đã apply migration Alembic
-- (tạo bảng decision_criteria).
--
-- Dữ liệu mẫu dựa theo rubric Food mặc định trong DecisionHub.md (Mục 7.4):
--   - Giá: ưu tiên giá thấp (min), trọng số 40% (0.4000)
--   - Mức phù hợp nhu cầu/khẩu vị: ưu tiên điểm cao (max), trọng số 35% (0.3500)
--   - Thời gian chuẩn bị: ưu tiên thời gian ngắn (min), trọng số 25% (0.2500)
-- =====================================================================

SET NAMES utf8mb4;

USE decision_hub;

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Giá', 'min', 0.4000
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Giá'
);

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Mức phù hợp nhu cầu/khẩu vị', 'max', 0.3500
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Mức phù hợp nhu cầu/khẩu vị'
);

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Thời gian chuẩn bị', 'min', 0.2500
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Thời gian chuẩn bị'
);

-- Dữ liệu mẫu tiêu chí Travel (Rubric Travel: Chi phí 40%, Sở thích 35%, Thời lượng 25%)
INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Chi phí du lịch', 'min', 0.4000
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Chi phí du lịch'
);

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Mức phù hợp sở thích', 'max', 0.3500
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Mức phù hợp sở thích'
);

INSERT INTO decision_criteria (name, direction, weight)
SELECT 'Thời lượng trải nghiệm', 'min', 0.2500
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.name = 'Thời lượng trải nghiệm'
);
