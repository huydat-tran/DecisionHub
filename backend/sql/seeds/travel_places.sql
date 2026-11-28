-- =====================================================================
-- DecisionHub - Seed dữ liệu mẫu Travel Places
--
-- Chạy SAU khi đã tạo database (sql/init.sql) và đã apply migration Alembic
-- (tạo bảng travel_places).
--
-- 30 địa điểm du lịch đại diện cho 5 vùng miền Việt Nam:
--   - Khu vực: Bắc, Trung, Nam, Tây Nguyên, Tây Nam Bộ
--   - Loại hình: Nghỉ dưỡng biển, Khám phá thiên nhiên, Văn hóa lịch sử,
--               Vui chơi giải trí, Sinh thái sông nước, Nghỉ dưỡng sinh thái,
--               Nghỉ dưỡng & Chữa lành
--   - Chi phí: 200.000 VND - 7.500.000 VND
--   - Thời lượng: 4.0h - 72.0h
--
-- INSERT IGNORE: an toàn khi chạy lại file nhiều lần (không duplicate).
-- =====================================================================

SET NAMES utf8mb4;
USE decision_hub;

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
  'https://ss-images.saostar.vn/wp700/2025/5/17/pc/1747483581177/tvfnaudfnh1-xcmfw6w7ub2-dod2f79uyb3.jpg',
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
  'https://mia.vn/media/uploads/blog-du-lich/an-tuong-ve-dep-hung-vi-noi-quan-the-danh-thang-trang-an-1640246787.jpg',
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
  'https://bcp.cdnchinhphu.vn/334894974524682240/2025/6/23/phu-quoc-17506756503251936667562.jpg',
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
  'https://hungvuongtravel.com.vn/uploads/up/root/tour/2023/11/18/17/23/51700281409_3677.png',
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
  'https://khamphahue.com.vn/Portals/0/Medias/Nam2022/T10/QuanTheDiTichCoDoHue-1.jpg',
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
  'https://danangfantasticity.com/wp-content/uploads/2018/07/cay-cau-vang-sun-world-ba-na-hills-da-nang-vao-top-nhung-cau-di-bo-tuong-nhat-gioi-1.jpg',
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
  'https://nhandan.vn/special/30-nam-mot-chang-duong-di-san-Vinh-Ha-Long/assets/HLCklusX0n/things-to-do-in-ha-long-bay-banner-1-1920x1080.jpg',
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
  'https://hoangthanhthanglong.vn/wp-content/uploads/2023/05/phongnha.jpg',
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
  'https://phetravel.com/uploads/2026/06/cho-cai-rang-1.jpeg',
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
  'https://d-annamtravel.com/static/media/BU%C3%94N%20MA%20THU%E1%BB%98T/M%C4%82NG%20%C4%90EN/2070920.jpg',
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
  'https://bizweb.dktcdn.net/thumb/grande/100/101/075/articles/bt-3b21d513-79ff-4fbf-8abf-ee6502755f64.jpg?v=1563266119937',
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
  'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRN57LHpWo3SMKv2czUokXE1V-PIcD_8K2CAv1Mby6j0b0h_KQRMFPDqvQ&s=10',
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
  'https://kimlientravel.com.vn/upload/image/tour-ho-ba-be-thac-ban-gioc-4.jpg',
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
  'https://r2.nucuoimekong.com/wp-content/uploads/ban-dao-son-tra-co-gi.jpg',
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
  'https://tourdulichdalatkhuyenmai.wordpress.com/wp-content/uploads/2014/12/tour-du-lich-da-lat-791.jpg',
  4.7,
  1
),
(
  'Du thuyền Vịnh Lan Hạ & Đảo Cát Bà',
  'Hải Phòng',
  'Bắc',
  5800000,
  48.0,
  'Nghỉ dưỡng biển',
  'Du thuyền 5 sao đẳng cấp trên vịnh Lan Hạ, Chèo kayak qua Hang Sáng Hang Tối, Đạp xe thăm làng chài cổ Việt Hải, Thưởng thức tiệc hải sản trên boong tàu',
  'Kỳ nghỉ dưỡng sang trọng giữa không gian vịnh biển yên bình liền kề Hạ Long với làn nước ngọc bích và hàng trăm bãi tắm tự nhiên hoang sơ.',
  'https://catbaduky.vn/image/catalog/TOUR%20%C4%82N%20T%E1%BB%90I%20C%C3%81T%20B%C3%80/dinner_vinhlanha10.jpg',
  4.9,
  1
),
(
  'Làng cổ Đường Lâm',
  'Hà Nội',
  'Bắc',
  200000,
  5.0,
  'Văn hóa lịch sử',
  'Thăm cổng làng Mông Phụ và đình cổ trăm tuổi, Đạp xe trên đường gạch nghiêng ngắm nhà đá ong, Thưởng thức chè lam và tương nếp truyền thống',
  'Bảo tàng sống về kiến trúc làng quê Bắc Bộ xưa, lưu giữ vẹn nguyên cây đa, bến nước, sân đình và nét văn hóa ngàn năm.',
  'https://cdn.realtech.com.vn/uploads/gostay/news/4086/kinh-nghiem-kham-pha-lang-co-duong-lam.jpg',
  4.5,
  1
),
(
  'Thị trấn trong sương Tam Đảo',
  'Vĩnh Phúc',
  'Bắc',
  700000,
  8.0,
  'Nghỉ dưỡng sinh thái',
  'Check-in Nhà thờ đá cổ Tam Đảo phong cách Gothic, Uống cà phê ngắm mây bay tại Quán Gió, Thăm Thác Bạc và Cổng Trời, Thưởng thức ngọn su su xào tỏi',
  'Đà Lạt của miền Bắc ở độ cao hơn 900m với thời tiết bốn mùa trong một ngày, sương khói mờ ảo và không khí mát lành quanh năm.',
  'https://bizweb.dktcdn.net/thumb/grande/100/456/675/products/img-20180708163604.jpg?v=1659409935080',
  4.5,
  1
),
(
  'Khu bảo tồn thiên nhiên Pù Luông',
  'Thanh Hóa',
  'Bắc',
  1400000,
  24.0,
  'Nghỉ dưỡng sinh thái',
  'Ngắm ruộng bậc thang mùa lúa chín vàng, Tắm thác Hiêu nước trong vắt giữa rừng già, Nghỉ dưỡng ecolodge ngắm mây thung lũng, Trải nghiệm ẩm thực Thái',
  'Thiên đường nghỉ dưỡng xanh bình yên nằm giữa núi non miền Tây Thanh Hóa, địa điểm lý tưởng để detox tâm hồn và hòa mình vào thiên nhiên.',
  'https://thiennhienmoitruong.vn/upload/images/btv/btv/btv-6.1/pu-luong.jpg',
  4.7,
  1
),
(
  'Suối khoáng nóng Yoko Onsen Quang Hanh',
  'Quảng Ninh',
  'Bắc',
  1600000,
  8.0,
  'Nghỉ dưỡng & Chữa lành',
  'Tắm khoáng nóng thiên nhiên chuẩn Onsen Nhật Bản, Xông hơi đá nóng muối hồng Himalaya, Thư giãn tại vườn Nhật tĩnh lặng, Thưởng thức ẩm thực Nhật',
  'Tổ hợp nghỉ dưỡng khoáng nóng chuẩn phong cách Nhật Bản giữa thung lũng xanh Quang Hanh, mang đến trải nghiệm phục hồi sức khỏe trọn vẹn.',
  'https://phetravel.com/uploads/unnamed-2025-02-24t145737303.png',
  4.8,
  1
),
(
  'Vịnh Vĩnh Hy & Vườn quốc gia Núi Chúa',
  'Ninh Thuận',
  'Trung',
  6500000,
  72.0,
  'Nghỉ dưỡng sinh thái',
  'Nghỉ dưỡng resort ven biển đẳng cấp quốc tế, Đi tàu đáy kính ngắm rạn san hô nguyên sơ, Trekking rừng khô hạn Núi Chúa, Thưởng thức hải sản vịnh',
  'Một trong bốn vịnh biển đẹp nhất Việt Nam với sự kết hợp kỳ vĩ giữa rừng nguyên sinh khô hạn nhiệt đới và biển xanh ngọc bích.',
  'https://images2.thanhnien.vn/528068263637045248/2023/10/3/nui-chua-3-16963046713511129131108.jpg',
  4.9,
  1
),
(
  'Kỳ Co & Eo Gió - Nhơn Lý',
  'Bình Định',
  'Trung',
  950000,
  10.0,
  'Nghỉ dưỡng biển',
  'Đi cano ra bãi biển Kỳ Co nước xanh trong vắt, Dạo bước trên con đường ven biển hùng vĩ tại Eo Gió, Lặn ngắm san hô Bãi Dứa, Ăn bánh xèo tôm nhảy',
  'Được ví như Maldives của miền Trung với bãi cát trắng mịn, vách đá dựng đứng kỳ vĩ và cảnh hoàng hôn tuyệt mỹ bên bờ biển Quy Nhơn.',
  'https://images.unsplash.com/photo-1507525428034-b723cf961d3e',
  4.7,
  1
),
(
  'Thám hiểm hệ thống Hang Tú Làn',
  'Quảng Bình',
  'Trung',
  7500000,
  72.0,
  'Khám phá thiên nhiên',
  'Bơi xuyên hang động ngầm thạch nhũ kỳ bí, Băng qua rừng rậm nhiệt đới và thung lũng đá vôi, Cắm trại bên bờ sông ngầm hoang sơ, Khám phá phim trường bom tấn',
  'Tour thám hiểm hang động mạo hiểm hàng đầu đưa bạn hòa mình vào hệ thống hang động hoang sơ kỳ vĩ và vẻ đẹp thiên nhiên nguyên bản.',
  'https://phongnhatourist.com/wp-content/uploads/2017/09/21191954_1148307991937024_7436779383564101520_n.jpg',
  4.9,
  1
),
(
  'Đảo Cù Lao Chàm',
  'Quảng Nam',
  'Trung',
  650000,
  8.0,
  'Nghỉ dưỡng biển',
  'Cano cao tốc vượt sóng ra đảo, Lặn ngắm san hô Bãi Chồng, Thăm giếng cổ Chăm Pa và chùa Hải Tạng, Thưởng thức cua đá và mực một nắng',
  'Khu dự trữ sinh quyển thế giới nổi tiếng với bãi biển sạch nói không với túi nilon, rạn san hô đầy màu sắc và không gian làng chài hiền hòa.',
  'https://danatravel.vn/data/images/70d7dd49-cu-lao-cham-1.jpg',
  4.6,
  1
),
(
  'Quần đảo Côn Đảo hoang sơ',
  'Bà Rịa - Vũng Tàu',
  'Nam',
  5200000,
  60.0,
  'Nghỉ dưỡng biển',
  'Viếng Nghĩa trang Hàng Dương và mộ nữ anh hùng Võ Thị Sáu, Thăm Nhà tù Côn Đảo, Ngắm rùa đẻ trứng tại Hòn Bảy Cạnh, Tắm biển Bãi Đầm Trầu',
  'Vừa là di tích lịch sử hào hùng thiêng liêng, vừa là quần đảo thiên đường với những bãi tắm hoang sơ và thiên nhiên biển đảo được bảo tồn nguyên vẹn.',
  'https://baohagiang.vn/file/4028eaa4679b32c401679c0c74382a7e/082024/1_20240807090631.jpg',
  4.8,
  1
),
(
  'Vườn quốc gia Cát Tiên & Bàu Sấu',
  'Đồng Nai',
  'Nam',
  1100000,
  24.0,
  'Khám phá thiên nhiên',
  'Đi xe mui trần xem thú rừng săn mồi ban đêm, Trekking chiêm ngưỡng cây Tung đại thụ trăm tuổi, Chèo xuồng ngắm cá sấu tại Bàu Sấu, Thăm Đảo Khỉ',
  'Khu dự trữ sinh quyển thế giới đất thấp lớn nhất miền Nam sở hữu hệ động thực vật nhiệt đới vô cùng đa dạng và phong phú.',
  'https://thiennhienmoitruong.vn/upload/images/btv/btv/dat-bau.jpg',
  4.6,
  1
),
(
  'Tổ hợp giải trí Grand World & Safari Phú Quốc',
  'Kiên Giang',
  'Nam',
  1200000,
  10.0,
  'Vui chơi giải trí',
  'Xem show Tinh hoa Việt Nam và nhạc nước Venice, Đi thuyền Gondola trên dòng kênh, Ngắm động vật hoang dã cự ly gần tại Vinpearl Safari',
  'Tổ hợp du lịch giải trí không ngủ 24/7 hàng đầu Đông Nam Á với hàng trăm hoạt động lễ hội, biểu diễn nghệ thuật và công trình kỷ lục.',
  'https://image.vietgoing.com/ticket/vietgoing_hbv2505091990.webp',
  4.7,
  1
),
(
  'Hồ Tà Đùng - Vịnh Hạ Long Tây Nguyên',
  'Đắk Nông',
  'Tây Nguyên',
  1300000,
  24.0,
  'Khám phá thiên nhiên',
  'Đi thuyền du ngoạn ngắm hơn 40 ốc đảo xanh trên lòng hồ thủy điện, Cắm trại glamping săn mây sáng sớm trên đồi, Thưởng thức rượu cần và gà nướng',
  'Tuyệt tác thiên nhiên giữa đại ngàn Tây Nguyên với mặt hồ tĩnh lặng ôm trọn hàng chục đảo xanh nhấp nhô, khí hậu mát lành quanh năm.',
  'https://media-cdn-v2.laodong.vn/Storage/NewsPortal/2021/10/9/961828/1111.jpg',
  4.7,
  1
),
(
  'Rừng tràm Trà Sư & Miếu Bà Chúa Xứ',
  'An Giang',
  'Tây Nam Bộ',
  350000,
  6.0,
  'Sinh thái sông nước',
  'Ngồi xuồng ba lá lướt trên thảm bèo cám xanh mướt, Lên đài quan sát ngắm toàn cảnh rừng tràm ngập nước, Viếng Miếu Bà Chúa Xứ Núi Sam, Ăn lẩu cá linh',
  'Biểu tượng du lịch mùa nước nổi miền Tây với hệ sinh thái rừng ngập nước nguyên sinh độc đáo cùng văn hóa tâm linh tín ngưỡng đặc sắc.',
  'https://luhanhtour.com/wp-content/uploads/2022/05/R%E1%BB%ABng-tr%C3%A0m-tr%C3%A0-s%C6%B0.jpg',
  4.6,
  1
),
(
  'Quần đảo Nam Du hoang sơ',
  'Kiên Giang',
  'Tây Nam Bộ',
  2100000,
  48.0,
  'Nghỉ dưỡng biển',
  'Tắm biển Bãi Cây Mến rặng dừa xanh mát, Đi tàu lặn ngắm san hô Hòn Hai Bờ Đập, Thăm ngọn hải đăng Nam Du cao nhất Việt Nam, Ăn nhum biển nướng',
  'Quần đảo hoang sơ tuyệt đẹp giữa biển Tây Nam giữ trọn vẻ đẹp thuần khiết, làn nước xanh màu ngọc bích và nhịp sống thanh bình của ngư dân.',
  'https://vietpowertravel.com.vn/blog/wp-content/uploads/2016/03/bora-bora-colour-spectrum-wow.jpg',
  4.6,
  1
);
