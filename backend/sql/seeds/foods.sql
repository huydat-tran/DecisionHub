-- =====================================================================
-- DecisionHub - Seed dữ liệu mẫu Food & Ingredients
--
-- Chạy SAU khi đã tạo database (sql/init.sql) và đã apply migration Alembic
-- (tạo bảng ingredients, foods và food_ingredients).
--
-- An toàn khi chạy lại nhiều lần (INSERT IGNORE / WHERE NOT EXISTS).
-- =====================================================================

SET NAMES utf8mb4;
USE decision_hub;

-- ---------------------------------------------------------------------
-- 1. Seed ingredients
-- ---------------------------------------------------------------------
INSERT IGNORE INTO ingredients (name) VALUES
    ('Bánh phở'),
    ('Thịt bò'),
    ('Hành lá'),
    ('Bún tươi'),
    ('Thịt heo nướng'),
    ('Rau sống'),
    ('Cơm tấm'),
    ('Sườn nướng'),
    ('Trứng ốp la'),
    ('Bánh mì'),
    ('Thịt nguội'),
    ('Pate'),
    ('Tôm sú'),
    ('Đậu hũ'),
    ('Nấm hương'),
    ('Đậu phộng'),
    ('Mì Quảng'),
    ('Thịt gà'),
    ('Sả ớt'),
    ('Hải sản');

-- ---------------------------------------------------------------------
-- 2. Seed foods (đa dạng bữa ăn, mức giá VND, thời gian chuẩn bị, tags)
-- ---------------------------------------------------------------------
INSERT INTO foods (name, description, price, meal_type, prep_time, image_url, tags, is_active)
SELECT 'Phở bò tái', 'Nước dùng ninh xương ngọt thanh, thịt bò tái mềm kèm bánh phở truyền thống.', 45000.00, 'breakfast', 15, https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQvlK0dWOgWjtNmlZIzLPqh-Dbkvt4dszy5lYIh0j6eQQ&s=10, JSON_ARRAY('nước', 'truyền thống', 'nóng'), 1
WHERE NOT EXISTS (SELECT 1 FROM foods f WHERE f.name = 'Phở bò tái');

INSERT INTO foods (name, description, price, meal_type, prep_time, image_url, tags, is_active)
SELECT 'Bánh mì thịt đặc biệt', 'Bánh mì giòn kẹp thịt nguội, pate béo ngậy và rau dưa chua.', 25000.00, 'breakfast', 5, https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTRRyr1GMgLmQge95TsbeOVtr6KYa28F6fbg3h-oGejYA&s=10, JSON_ARRAY('nhanh', 'tiện lợi', 'khô'), 1
WHERE NOT EXISTS (SELECT 1 FROM foods f WHERE f.name = 'Bánh mì thịt đặc biệt');

INSERT INTO foods (name, description, price, meal_type, prep_time, image_url, tags, is_active)
SELECT 'Bún chả Hà Nội', 'Thịt heo nướng than hoa thơm lừng ăn kèm bún tươi, rau sống và nước mắm chua ngọt.', 50000.00, 'lunch', 20, https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTGQ3V8TajN69LpSePYDKJ90Ue00xGBaEsfLgV8GyBW7w&s=10, JSON_ARRAY('truyền thống', 'đậm đà'), 1
WHERE NOT EXISTS (SELECT 1 FROM foods f WHERE f.name = 'Bún chả Hà Nội');

INSERT INTO foods (name, description, price, meal_type, prep_time, image_url, tags, is_active)
SELECT 'Cơm tấm sườn bì chả', 'Cơm tấm dẻo thơm ăn với sườn nướng mật ong, trứng ốp la và mỡ hành.', 55000.00, 'lunch', 15, https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS0NT9HOR098ySLy2TurfnlnLgu38dlg9nzZUNvCqBVbw&s=10, JSON_ARRAY('no lâu', 'đậm đà'), 1
WHERE NOT EXISTS (SELECT 1 FROM foods f WHERE f.name = 'Cơm tấm sườn bì chả');

INSERT INTO foods (name, description, price, meal_type, prep_time, image_url, tags, is_active)
SELECT 'Cơm chiên đậu hũ nấm', 'Món chay thanh đạm với đậu hũ chiên giòn và nấm hương xào thơm.', 35000.00, 'lunch', 12, https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS1LRT9ppOzNgUFUJd4fspqHh8TV6H-6bXWUix-GjDpIKpU3KmVw0iRzAFr&s=10, JSON_ARRAY('chay', 'thanh đạm', 'nhanh'), 1
WHERE NOT EXISTS (SELECT 1 FROM foods f WHERE f.name = 'Cơm chiên đậu hũ nấm');

INSERT INTO foods (name, description, price, meal_type, prep_time, image_url, tags, is_active)
SELECT 'Mì Quảng tôm thịt', 'Sợi mì Quảng vàng óng ăn kèm tôm sú, thịt gà, đậu phộng rang và bánh tráng.', 48000.00, 'dinner', 18, https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTtpsTdQenvge6SMSdeIQqKDkRxRxaKmBxEWeAqGrVjww&s=10, JSON_ARRAY('đặc sản', 'đậm đà'), 1
WHERE NOT EXISTS (SELECT 1 FROM foods f WHERE f.name = 'Mì Quảng tôm thịt');

INSERT INTO foods (name, description, price, meal_type, prep_time, image_url, tags, is_active)
SELECT 'Bún thái hải sản cay', 'Nước dùng chua cay sả ớt kích thích vị giác với tôm sú và hải sản tươi.', 65000.00, 'dinner', 25, https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS8ppHyH4cKK_4YJNbXhrde7yJff9FGFQItNmnZQv5GBA&s=10, JSON_ARRAY('cay', 'nước', 'hải sản'), 1
WHERE NOT EXISTS (SELECT 1 FROM foods f WHERE f.name = 'Bún thái hải sản cay');

INSERT INTO foods (name, description, price, meal_type, prep_time, image_url, tags, is_active)
SELECT 'Gỏi cuốn tôm thịt', 'Bữa nhẹ thanh mát với tôm sú, rau sống cuốn bánh tráng chấm tương đậu phộng.', 30000.00, 'snack', 10, https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ_J3WwDs5yo43RuNKNqUo_wJUm0Rpz8TWqfk8Rk_ROLA&s=10, JSON_ARRAY('thanh đạm', 'nhanh', 'ít dầu mỡ'), 1
WHERE NOT EXISTS (SELECT 1 FROM foods f WHERE f.name = 'Gỏi cuốn tôm thịt');

-- ---------------------------------------------------------------------
-- 3. Seed food_ingredients (tra cứu theo tên để không phụ thuộc ID)
-- ---------------------------------------------------------------------
INSERT IGNORE INTO food_ingredients (food_id, ingredients_id)
SELECT f.id, i.id
FROM foods f
JOIN ingredients i ON (
    (f.name = 'Phở bò tái' AND i.name IN ('Bánh phở', 'Thịt bò', 'Hành lá'))
    OR (f.name = 'Bánh mì thịt đặc biệt' AND i.name IN ('Bánh mì', 'Thịt nguội', 'Pate', 'Rau sống'))
    OR (f.name = 'Bún chả Hà Nội' AND i.name IN ('Bún tươi', 'Thịt heo nướng', 'Rau sống'))
    OR (f.name = 'Cơm tấm sườn bì chả' AND i.name IN ('Cơm tấm', 'Sườn nướng', 'Trứng ốp la', 'Hành lá'))
    OR (f.name = 'Cơm chiên đậu hũ nấm' AND i.name IN ('Cơm tấm', 'Đậu hũ', 'Nấm hương', 'Hành lá'))
    OR (f.name = 'Mì Quảng tôm thịt' AND i.name IN ('Mì Quảng', 'Tôm sú', 'Thịt gà', 'Đậu phộng', 'Rau sống'))
    OR (f.name = 'Bún thái hải sản cay' AND i.name IN ('Bún tươi', 'Tôm sú', 'Hải sản', 'Sả ớt'))
    OR (f.name = 'Gỏi cuốn tôm thịt' AND i.name IN ('Bún tươi', 'Tôm sú', 'Rau sống', 'Đậu phộng'))
);
