-- =====================================================================
-- DecisionHub - Module Travel: Schema DDL & Seed dữ liệu mẫu
--
-- File: backend/sql/seeds/travel_places.sql
-- Mục đích:
--   1. Tự động tạo bảng `travel_places` nếu chưa tồn tại (DDL đầy đủ Index,
--      Full-text search, kiểm tra ràng buộc chi phí, thời lượng).
--   2. Nạp toàn bộ 15 bản ghi dữ liệu mẫu đại diện cho 5 vùng miền Việt Nam,
--      đa dạng loại hình hoạt động, chi phí (150k - 3.5tr) và thời lượng (4h - 48h).
--   3. An toàn khi chạy lại nhiều lần (idempotent, không bị duplicate dữ liệu).
-- =====================================================================

SET NAMES utf8mb4;
USE decision_hub;

-- ---------------------------------------------------------------------
-- 1. DDL: TẠO BẢNG travel_places
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS travel_places (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT 'Khóa chính định danh địa điểm',
    name VARCHAR(200) NOT NULL COMMENT 'Tên địa điểm du lịch',
    province_city VARCHAR(100) NOT NULL COMMENT 'Tỉnh/Thành phố trực thuộc',
    region ENUM('Bắc', 'Trung', 'Nam', 'Tây Nguyên', 'Tây Nam Bộ') NOT NULL COMMENT 'Khu vực địa lý (phục vụ lọc vùng miền)',
    estimated_cost INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Chi phí tham khảo trung bình (VND) - phục vụ lọc trần ngân sách và tính WSM Cost',
    estimated_duration DECIMAL(4, 1) UNSIGNED NOT NULL DEFAULT 1.0 COMMENT 'Thời lượng trải nghiệm ước tính (giờ) - phục vụ lọc trần thời lượng và tính WSM Time',
    activity_type VARCHAR(100) NOT NULL COMMENT 'Loại hình trải nghiệm chính (Nghỉ dưỡng biển, Khám phá thiên nhiên, Văn hóa lịch sử...)',
    highlights TEXT NULL COMMENT 'Danh sách hoạt động nổi bật, trải nghiệm đặc trưng',
    description TEXT NULL COMMENT 'Mô tả chi tiết về địa điểm',
    image_url VARCHAR(500) NULL DEFAULT NULL COMMENT 'URL ảnh đại diện minh họa (nếu NULL frontend tự fallback)',
    rating DECIMAL(2, 1) UNSIGNED NOT NULL DEFAULT 4.5 COMMENT 'Điểm đánh giá tham khảo (1.0 - 5.0)',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'Trạng thái hoạt động (1: Đang hoạt động, 0: Tạm ngưng)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm tạo bản ghi',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Thời điểm cập nhật bản ghi',

    -- Ràng buộc duy nhất theo tên địa điểm để tránh trùng lặp khi chạy seed lại
    CONSTRAINT uq_travel_places_name UNIQUE (name),

    -- Các chỉ mục tối ưu hóa cho Decision Engine và Quick Search
    INDEX idx_travel_places_region (region),
    INDEX idx_travel_places_cost (estimated_cost),
    INDEX idx_travel_places_duration (estimated_duration),
    INDEX idx_travel_places_activity_type (activity_type),
    INDEX idx_travel_places_is_active (is_active),
    INDEX idx_travel_places_composite_filter (region, estimated_cost, estimated_duration),
    FULLTEXT INDEX ft_travel_places_search (name, province_city, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng lưu trữ thông tin địa điểm du lịch cho DecisionHub Travel Module';

-- ---------------------------------------------------------------------
-- 2. DML: SEED 15 ĐỊA ĐIỂM DU LỊCH MẪU
-- (Dùng INSERT IGNORE để an toàn khi chạy lại file nhiều lần)
-- ---------------------------------------------------------------------
INSERT IGNORE INTO travel_places 
  (name, province_city, region, estimated_cost, estimated_duration, activity_type, highlights, description, image_url, rating, is_active)
VALUES
(
  'Phố cổ Hội An',
  'Quảng Nam',
  'Trung',
  500000,
  8.0,
  'Văn hóa lịch sử',
  'Thả đèn hoa đăng trên sông Hoài, Thưởng thức cao lầu và bánh mì Phượng, Check-in Chùa Cầu, Đạp xe tham quan làng gốm Thanh Hà',
  'Đô thị cổ được UNESCO công nhận là Di sản Thế giới với những ngôi nhà cổ sơn vàng, giàn hoa giấy rực rỡ và lồng đèn lung linh về đêm.',
  'https://images.unsplash.com/photo-1559592413-7cec4d0cae2b',
  4.8,
  1
),
(
  'Quần thể danh thắng Tràng An',
  'Ninh Bình',
  'Bắc',
  450000,
  6.0,
  'Khám phá thiên nhiên',
  'Đi thuyền nan ngắm hang động tự nhiên, Viếng đền Trình và phủ Khống, Chụp ảnh bối cảnh phim trường Kong: Skull Island, Leo núi ngắm thung lũng đá vôi',
  'Di sản thế giới kép đầu tiên tại Đông Nam Á, nổi tiếng với hệ sinh thái đất ngập nước và cảnh quan hang động núi đá vôi kỳ vĩ.',
  'https://images.unsplash.com/photo-1528127269322-539801943592',
  4.9,
  1
),
(
  'Đảo ngọc Phú Quốc',
  'Kiên Giang',
  'Nam',
  3500000,
  48.0,
  'Nghỉ dưỡng biển',
  'Ngắm hoàng hôn Bãi Sao và Sunset Sanato, Lặn biển ngắm san hô tại hòn Móng Tay, Thưởng thức hải sản Hàm Ninh, Khám phá cáp treo Hòn Thơm',
  'Hòn đảo lớn nhất Việt Nam sở hữu bãi cát trắng mịn, nước biển trong xanh và hệ sinh thái giải trí, nghỉ dưỡng đẳng cấp quốc tế.',
  'https://images.unsplash.com/photo-1583417319070-4a69db38a482',
  4.7,
  1
),
(
  'Bản Cát Cát & Đỉnh Fansipan',
  'Lào Cai',
  'Bắc',
  1800000,
  24.0,
  'Khám phá thiên nhiên',
  'Chinh phục nóc nhà Đông Dương Fansipan bằng cáp treo, Thuê trang phục dân tộc H''Mông chụp ảnh, Thưởng thức thắng cố và lợn bản nướng, Check-in ruộng bậc thang',
  'Khu du lịch miền núi Tây Bắc nổi tiếng với không khí se lạnh, mây mù bao phủ quanh năm và bản sắc văn hóa vùng cao độc đáo.',
  'https://images.unsplash.com/photo-1544735716-392fe2489ffa',
  4.6,
  1
),
(
  'Cố đô Huế & Sông Hương',
  'Thừa Thiên Huế',
  'Trung',
  600000,
  12.0,
  'Văn hóa lịch sử',
  'Tham quan Đại Nội Huế, Du thuyền nghe ca Huế trên sông Hương, Viếng chùa Thiên Mụ và lăng Tự Đức, Ăn bún bò Huế và các loại bánh cung đình',
  'Vùng đất cố đô lưu giữ trọn vẹn những nét đẹp trầm mặc của các công trình kiến trúc cung đình triều Nguyễn cùng nét văn hóa ẩm thực tinh tế.',
  'https://images.unsplash.com/photo-1599707367072-cd6ada2bc375',
  4.7,
  1
),
(
  'Bà Nà Hills & Cầu Vàng',
  'Đà Nẵng',
  'Trung',
  1200000,
  8.0,
  'Vui chơi giải trí',
  'Check-in biểu tượng Cầu Vàng đôi bàn tay khổng lồ, Trải nghiệm hệ thống cáp treo đạt kỷ lục thế giới, Khám phá làng Pháp và hầm rượu Debay, Vui chơi công viên Fantasy Park',
  'Thiên đường giải trí trên đỉnh núi Chúa ở độ cao 1.487m với khí hậu 4 mùa trong một ngày và lối kiến trúc phong cách châu Âu cổ kính.',
  'https://images.unsplash.com/photo-1569154941061-e231b4725ef1',
  4.8,
  1
),
(
  'Vịnh Hạ Long',
  'Quảng Ninh',
  'Bắc',
  2200000,
  36.0,
  'Nghỉ dưỡng biển',
  'Du thuyền ngủ đêm trên vịnh, Chèo kayak luồn qua hang Luồn, Thăm hang Sửng Sốt và đảo Ti Tốp, Ngắm hoàng hôn trên boong tàu',
  'Kỳ quan thiên nhiên thế giới với hàng nghìn hòn đảo đá vôi nhấp nhô trên mặt nước xanh ngọc bích, lý tưởng cho kỳ nghỉ dưỡng sang trọng.',
  'https://images.unsplash.com/photo-1528127269322-539801943592',
  4.9,
  1
),
(
  'Vườn quốc gia Phong Nha - Kẻ Bàng',
  'Quảng Bình',
  'Trung',
  1500000,
  16.0,
  'Khám phá thiên nhiên',
  'Thám hiểm Động Thiên Đường và Động Phong Nha, Chèo thuyền kayak trên sông Chày và đu zipline Hang Tối, Thử thách trekking rừng nguyên sinh',
  'Vương quốc hang động thế giới sở hữu hệ thống hang động đá vôi cổ nhất châu Á cùng vẻ đẹp địa chất hoang sơ tráng lệ.',
  'https://images.unsplash.com/photo-1570789210967-2cac24afeb00',
  4.8,
  1
),
(
  'Chợ nổi Cái Răng',
  'Cần Thơ',
  'Tây Nam Bộ',
  300000,
  4.0,
  'Sinh thái sông nước',
  'Đi ghe máy ngắm bình minh trên sông Hậu, Thưởng thức hủ tiếu tô và cà phê ghe lắc lư trên sông, Mua trái cây miệt vườn qua cây bẹo, Ghé thăm lò làm hủ tiếu truyền thống',
  'Nét văn hóa giao thương đường thủy đặc sắc của miền Tây Nam Bộ, nhộn nhịp mua bán trái cây và nông sản từ tờ mờ sáng.',
  'https://images.unsplash.com/photo-1583417319070-4a69db38a482',
  4.5,
  1
),
(
  'Măng Đen - Đại ngàn Kon Tum',
  'Kon Tum',
  'Tây Nguyên',
  850000,
  24.0,
  'Nghỉ dưỡng sinh thái',
  'Tản bộ dưới rừng thông bạt ngàn, Thăm thác Pa Sỹ và hồ Đăk Ke, Săn mây sáng sớm tại đồi cỏ, Uống cà phê hữu cơ Măng Đen bên sườn đồi',
  'Được mệnh danh là Đà Lạt thứ hai của Tây Nguyên với khí hậu trong lành, rừng thông nguyên sinh và nhịp sống thanh bình, không xô bồ.',
  'https://images.unsplash.com/photo-1506744038136-46273834b3fb',
  4.6,
  1
),
(
  'Đồi Cát Bay & Bàu Trắng Mũi Né',
  'Bình Thuận',
  'Trung',
  750000,
  10.0,
  'Khám phá thiên nhiên',
  'Lái xe môtô địa hình ATV trên đồi cát trắng, Trượt ván cát tại Đồi Hồng, Ngắm hồ sen nở giữa tiểu sa mạc, Chụp ảnh phong cách du mục hoang dã',
  'Tiểu sa mạc Sahara độc nhất vô nhị của Việt Nam với những cồn cát đổi màu theo thời gian trong ngày và khung cảnh bao la bát ngát.',
  'https://images.unsplash.com/photo-1507525428034-b723cf961d3e',
  4.6,
  1
),
(
  'Địa đạo Củ Chi',
  'TP. Hồ Chí Minh',
  'Nam',
  250000,
  5.0,
  'Văn hóa lịch sử',
  'Chui hầm địa đạo trải nghiệm thực tế, Thử bắn súng thể thao tại trường bắn, Ăn khoai mì luộc chấm muối mè thời chiến, Xem phim tài liệu lịch sử',
  'Hệ thống công trình quân sự dưới lòng đất độc đáo dài hơn 250km, biểu tượng lịch sử hào hùng và ý chí kiên cường.',
  'https://images.unsplash.com/photo-1544735716-392fe2489ffa',
  4.7,
  1
),
(
  'Hồ Ba Bể & Thác Bản Giốc',
  'Cao Bằng',
  'Bắc',
  2500000,
  48.0,
  'Khám phá thiên nhiên',
  'Đi bè mảng ngắm thác nước Bản Giốc hùng vĩ, Chèo kayak lướt trên mặt hồ Ba Bể xanh biếc, Thăm động Ngườm Ngao thạch nhũ lung linh, Thưởng thức cá suối nướng',
  'Cung đường du lịch Đông Bắc tuyệt đẹp kết hợp giữa hồ nước ngọt tự nhiên lớn nhất Việt Nam và một trong bốn thác nước xuyên biên giới kỳ vĩ nhất thế giới.',
  'https://images.unsplash.com/photo-1528127269322-539801943592',
  4.8,
  1
),
(
  'Biển Mỹ Khê & Bán đảo Sơn Trà',
  'Đà Nẵng',
  'Trung',
  350000,
  6.0,
  'Nghỉ dưỡng biển',
  'Tắm biển tại bãi biển đẹp nhất hành tinh, Viếng chùa Linh Ứng ngắm tượng Phật Bà 67m, Lên đỉnh Bàn Cờ ngắm trọn thành phố Đà Nẵng, Ngắm voọc chà vá chân nâu quý hiếm',
  'Sự kết hợp hoàn hảo giữa biển xanh cát trắng trải dài và bán đảo nguyên sinh hoang sơ ngay sát lòng đô thị hiện đại.',
  'https://images.unsplash.com/photo-1569154941061-e231b4725ef1',
  4.8,
  1
),
(
  'Thung lũng Tình Yêu & Đỉnh Langbiang',
  'Lâm Đồng',
  'Tây Nguyên',
  900000,
  12.0,
  'Nghỉ dưỡng sinh thái',
  'Đi xe jeep lên đỉnh radar ngắm trọn thành phố sương mù, Check-in mê cung cây và đồi thông mộng mơ, Uống trà atiso ngắm hoàng hôn, Trải nghiệm cưỡi ngựa quanh hồ',
  'Điểm đến thơ mộng giữa lòng Đà Lạt mộng mơ với khí hậu mát mẻ, muôn hoa đua sắc và câu chuyện tình sử K''lang và H''biang huyền thoại.',
  'https://images.unsplash.com/photo-1506744038136-46273834b3fb',
  4.7,
  1
);
