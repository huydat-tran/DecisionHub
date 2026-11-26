-- =====================================================================
-- DecisionHub - Seed dữ liệu mẫu WSM để kiểm chứng (WSM Verification)
--
-- Bộ dữ liệu mẫu gồm 4 phương án (3 hợp lệ, 1 bị loại) và 3 tiêu chí
-- để đối chiếu kết quả tính toán WSM thủ công với kết quả của WSM Engine.
-- =====================================================================

SET NAMES utf8mb4;

USE decision_hub;

-- 1. Tiêu chí đánh giá WSM (Decision Criteria)
-- Tổng trọng số = 0.4000 + 0.3500 + 0.2500 = 1.0000 (100%)
INSERT INTO decision_criteria (domain, name, direction, weight)
SELECT 'food', 'Giá', 'min', 0.4000
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.domain = 'food' AND dc.name = 'Giá'
);

INSERT INTO decision_criteria (domain, name, direction, weight)
SELECT 'food', 'Mức phù hợp nhu cầu/khẩu vị', 'max', 0.3500
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.domain = 'food' AND dc.name = 'Mức phù hợp nhu cầu/khẩu vị'
);

INSERT INTO decision_criteria (domain, name, direction, weight)
SELECT 'food', 'Thời gian chuẩn bị', 'min', 0.2500
WHERE NOT EXISTS (
  SELECT 1 FROM decision_criteria dc WHERE dc.domain = 'food' AND dc.name = 'Thời gian chuẩn bị'
);

-- 2. Dữ liệu mẫu các món ăn (Candidates) để kiểm chứng
-- Phương án A: 30k, 15p, điểm 80 -> Hợp lệ
-- Phương án B: 50k, 25p, điểm 90 -> Hợp lệ
-- Phương án C: 40k, 10p, điểm 70 -> Hợp lệ
-- Phương án D: 75k, 20p, điểm 95, có hành -> Bị loại vì vượt ngân sách 60k và có hành
INSERT INTO foods (id, name, description, price, prep_time, meal_type, tags, is_active)
VALUES
  (901, 'Phương án A (Phở Bò Tái)', 'Món phở bò tái nước dùng thơm ngon', 30000, 15, 'breakfast', '["truyền thống", "bò"]', 1),
  (902, 'Phương án B (Cơm Sườn Nướng)', 'Cơm sườn nướng mật ong đậm đà', 50000, 25, 'breakfast', '["cơm", "sườn"]', 1),
  (903, 'Phương án C (Bún Chả Hà Nội)', 'Bún chả nướng than hoa truyền thống', 40000, 10, 'breakfast', '["bún", "chả"]', 1),
  (904, 'Phương án D (Mì Xào Bò Đặc Biệt)', 'Mì xào bò nhiều hành phi', 75000, 20, 'breakfast', '["mì", "bò", "hành"]', 1)
ON DUPLICATE KEY UPDATE
  price = VALUES(price),
  prep_time = VALUES(prep_time),
  meal_type = VALUES(meal_type);
