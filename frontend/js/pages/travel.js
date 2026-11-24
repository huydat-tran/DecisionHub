// =============================================================================
// Phân hệ Travel (WhereShouldITravel) - Client Prototype
// Quản lý form nhập ngân sách, thời lượng, sở thích và hiển thị kết quả gợi ý
// =============================================================================

(function () {
  "use strict";

  // Dữ liệu mẫu các điểm đến du lịch đa dạng phục vụ demo lọc và xếp hạng WSM
  const TRAVEL_DESTINATIONS = [
    {
      id: 1,
      name: "Phố cổ Hội An",
      province: "Quảng Nam",
      region: "trung",
      regionName: "Miền Trung",
      cost: 500000,
      duration: "2-3",
      durationHours: 24,
      durationText: "2 - 3 ngày (24h)",
      preferences: ["van-hoa", "chua-lanh"],
      preferenceLabels: ["🏛️ Văn hóa di sản", "🌿 Chữa lành"],
      rating: 4.8,
      description: "Đô thị cổ được UNESCO công nhận là Di sản Thế giới với những ngôi nhà sơn vàng, đèn lồng rực rỡ và ẩm thực cao lầu đặc sắc.",
      image: "../assets/images/travel/hoian.jpg",
    },
    {
      id: 2,
      name: "Quần thể danh thắng Tràng An",
      province: "Ninh Bình",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 850000,
      duration: "1",
      durationHours: 6,
      durationText: "Đi trong ngày (6h)",
      preferences: ["thien-nhien", "van-hoa"],
      preferenceLabels: ["🌲 Thiên nhiên", "🏛️ Di sản kép"],
      rating: 4.9,
      description: "Di sản thế giới kép đầu tiên tại Đông Nam Á với non nước kỳ vĩ, hệ thống hang động tự nhiên và phim trường Kong kỳ thú.",
      image: "../assets/images/travel/trangan.jpg",
    },
    {
      id: 3,
      name: "Vịnh Hạ Long",
      province: "Quảng Ninh",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 3200000,
      duration: "2-3",
      durationHours: 36,
      durationText: "2 - 3 ngày (36h)",
      preferences: ["bien", "thien-nhien"],
      preferenceLabels: ["🌲 Thiên nhiên kỳ vĩ", "🏖️ Nghỉ dưỡng biển"],
      rating: 4.9,
      description: "Kỳ quan thiên nhiên thế giới sở hữu hàng nghìn đảo đá vôi kỳ thú, trải nghiệm du thuyền ngủ đêm và chèo kayak trên vịnh biển xanh.",
      image: "../assets/images/travel/halong.jpg",
    },
    {
      id: 4,
      name: "Đảo ngọc Phú Quốc",
      province: "Kiên Giang",
      region: "nam",
      regionName: "Miền Nam",
      cost: 4500000,
      duration: "4-5",
      durationHours: 48,
      durationText: "4 - 5 ngày (48h)",
      preferences: ["bien", "giai-tri"],
      preferenceLabels: ["🏖️ Nghỉ dưỡng biển", "🎡 Vui chơi giải trí"],
      rating: 4.8,
      description: "Bãi cát trắng mịn, ngắm hoàng hôn đẹp nhất Việt Nam, tổ hợp vui chơi giải trí Grand World và cáp treo Hòn Thơm vượt biển.",
      image: "../assets/images/travel/phuquoc.jpg",
    },
    {
      id: 5,
      name: "Đà Lạt ngàn hoa",
      province: "Lâm Đồng",
      region: "tay-nguyen",
      regionName: "Tây Nguyên",
      cost: 2200000,
      duration: "2-3",
      durationHours: 36,
      durationText: "2 - 3 ngày (36h)",
      preferences: ["chua-lanh", "giai-tri", "thien-nhien"],
      preferenceLabels: ["🌿 Nghỉ dưỡng & Chill", "🎡 Check-in sống ảo"],
      rating: 4.7,
      description: "Khí hậu mát mẻ quanh năm, cảnh quan đồi thông săn mây lãng mạn cùng vô số quán cà phê đẹp và homestay hợp túi tiền.",
      image: "../assets/images/travel/dalat.jpg",
    },
    {
      id: 6,
      name: "Sa Pa & Đỉnh Fansipan",
      province: "Lào Cai",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 2600000,
      duration: "2-3",
      durationHours: 24,
      durationText: "2 - 3 ngày (24h)",
      preferences: ["thien-nhien", "giai-tri"],
      preferenceLabels: ["🌲 Khám phá thiên nhiên", "🎡 Check-in Fansipan"],
      rating: 4.8,
      description: "Chinh phục nóc nhà Đông Dương bằng cáp treo kỷ lục, chiêm ngưỡng ruộng bậc thang Mường Hoa và trải nghiệm văn hóa bản sắc vùng cao.",
      image: "../assets/images/travel/halong.jpg",
    },
    {
      id: 7,
      name: "Mũi Né - Đồi Cát Bay",
      province: "Bình Thuận",
      region: "trung",
      regionName: "Miền Trung",
      cost: 1800000,
      duration: "2-3",
      durationHours: 24,
      durationText: "2 - 3 ngày (24h)",
      preferences: ["bien", "giai-tri"],
      preferenceLabels: ["🏖️ Biển xanh nắng vàng", "🎡 Lái xe địa hình"],
      rating: 4.6,
      description: "Thiên đường nghỉ dưỡng với những đồi cát mênh mông đổi màu theo giờ, thể thao lái xe ATV địa hình và hải sản tươi ngon giá rẻ.",
      image: "../assets/images/travel/phuquoc.jpg",
    },
    {
      id: 8,
      name: "Cố đô Huế & Sông Hương",
      province: "Thừa Thiên Huế",
      region: "trung",
      regionName: "Miền Trung",
      cost: 1200000,
      duration: "2-3",
      durationHours: 24,
      durationText: "2 - 3 ngày (24h)",
      preferences: ["van-hoa", "chua-lanh"],
      preferenceLabels: ["🏛️ Di sản cố đô", "🌿 Thơ mộng & Chữa lành"],
      rating: 4.7,
      description: "Quần thể di tích Cố đô trầm mặc, Đại Nội uy nghiêm, nghe ca Huế trên sông Hương và thưởng thức ẩm thực cung đình thanh tao.",
      image: "../assets/images/travel/hoian.jpg",
    },
    {
      id: 9,
      name: "Làng cổ Đường Lâm",
      province: "Hà Nội",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 350000,
      duration: "1",
      durationHours: 5,
      durationText: "Đi trong ngày (5h)",
      preferences: ["van-hoa"],
      preferenceLabels: ["🏛️ Làng cổ nghìn năm", "🍵 Trải nghiệm dân dã"],
      rating: 4.5,
      description: "Bảo tàng sống về kiến trúc nông thôn Bắc Bộ xưa với những ngôi nhà đá ong hàng trăm năm tuổi, đình làng Mông Phụ và tương nếp thơm ngon.",
      image: "../assets/images/travel/hoian.jpg",
    },
    {
      id: 10,
      name: "Biển Mỹ Khê & Bán đảo Sơn Trà",
      province: "Đà Nẵng",
      region: "trung",
      regionName: "Miền Trung",
      cost: 550000,
      duration: "1",
      durationHours: 6,
      durationText: "Đi trong ngày (6h)",
      preferences: ["bien", "thien-nhien"],
      preferenceLabels: ["🏖️ Biển đẹp hành tinh", "🌲 Bán đảo nguyên sinh"],
      rating: 4.8,
      description: "Bãi biển quyến rũ với cát trắng thoai thoải, kết hợp cung đường đèo Sơn Trà viếng Chùa Linh Ứng ngắm trọn thành phố đáng sống.",
      image: "../assets/images/travel/halong.jpg",
    },
    {
      id: 11,
      name: "Rừng tràm Trà Sư & Miếu Bà Chúa Xứ",
      province: "An Giang",
      region: "tay-nam-bo",
      regionName: "Tây Nam Bộ",
      cost: 450000,
      duration: "1",
      durationHours: 6,
      durationText: "Đi trong ngày (6h)",
      preferences: ["thien-nhien", "van-hoa"],
      preferenceLabels: ["🌲 Sinh thái sông nước", "🏛️ Tâm linh miệt vườn"],
      rating: 4.6,
      description: "Đi xuồng ba lá len lỏi giữa thảm bèo cám xanh ngắt của rừng tràm ngập nước, kết hợp chiêm bái Miếu Bà Chúa Xứ Núi Sam linh thiêng.",
      image: "../assets/images/travel/trangan.jpg",
    },
    {
      id: 12,
      name: "Chợ nổi Cái Răng",
      province: "Cần Thơ",
      region: "tay-nam-bo",
      regionName: "Tây Nam Bộ",
      cost: 400000,
      duration: "1",
      durationHours: 4,
      durationText: "Đi trong ngày (4h)",
      preferences: ["thien-nhien", "van-hoa"],
      preferenceLabels: ["🛶 Văn hóa sông nước", "🍍 Ẩm thực ghe cào"],
      rating: 4.5,
      description: "Trải nghiệm đi ghe máy ngắm bình minh sông Hậu, thưởng thức tô hủ tiếu lắc lư trên sông và hòa mình vào nét buôn bán độc đáo qua cây bẹo.",
      image: "../assets/images/travel/trangan.jpg",
    },
    {
      id: 13,
      name: "Thị trấn trong sương Tam Đảo",
      province: "Vĩnh Phúc",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 750000,
      duration: "1",
      durationHours: 8,
      durationText: "Đi trong ngày (8h)",
      preferences: ["chua-lanh", "thien-nhien"],
      preferenceLabels: ["🌿 Nghỉ dưỡng săn mây", "🌲 Khí hậu mát lạnh"],
      rating: 4.5,
      description: "Điểm trốn nóng cuối tuần hoàn hảo chỉ cách Hà Nội 70km với nhà thờ đá cổ Gothic, quán Gió ngắm mây trôi và không khí mát lành.",
      image: "../assets/images/travel/dalat.jpg",
    },
    {
      id: 14,
      name: "Kỳ Co & Eo Gió - Nhơn Lý",
      province: "Bình Định",
      region: "trung",
      regionName: "Miền Trung",
      cost: 950000,
      duration: "1",
      durationHours: 10,
      durationText: "Đi trong ngày (10h)",
      preferences: ["bien", "thien-nhien"],
      preferenceLabels: ["🏖️ Maldives miền Trung", "🌲 Cung đường vách đá"],
      rating: 4.7,
      description: "Cano lướt sóng ra bãi tắm nước trong vắt màu ngọc bích, check-in con đường ven biển hùng vĩ tại Eo Gió và lặn ngắm san hô Bãi Dứa.",
      image: "../assets/images/travel/halong.jpg",
    },
    {
      id: 15,
      name: "Bà Nà Hills & Cầu Vàng",
      province: "Đà Nẵng",
      region: "trung",
      regionName: "Miền Trung",
      cost: 1400000,
      duration: "1",
      durationHours: 8,
      durationText: "Đi trong ngày (8h)",
      preferences: ["giai-tri", "van-hoa"],
      preferenceLabels: ["🎡 Thiên đường giải trí", "🌉 Cầu Vàng biểu tượng"],
      rating: 4.8,
      description: "Tổ hợp giải trí trên đỉnh núi cao 1.487m với cây Cầu Vàng đôi bàn tay khổng lồ nổi tiếng thế giới, làng Pháp cổ kính và cáp treo đạt kỷ lục.",
      image: "../assets/images/travel/dalat.jpg",
    },
    {
      id: 16,
      name: "Vườn quốc gia Cát Tiên",
      province: "Đồng Nai",
      region: "nam",
      regionName: "Miền Nam",
      cost: 1100000,
      duration: "2-3",
      durationHours: 24,
      durationText: "2 - 3 ngày (24h)",
      preferences: ["thien-nhien", "chua-lanh"],
      preferenceLabels: ["🌲 Rừng già nguyên sinh", "🌿 Trải nghiệm hoang dã"],
      rating: 4.6,
      description: "Tour xe mui trần xem thú rừng ăn đêm độc đáo, chèo xuồng ngắm cá sấu tại Bàu Sấu và trekking khám phá cây Tung đại thụ nghìn năm tuổi.",
      image: "../assets/images/travel/trangan.jpg",
    },
    {
      id: 17,
      name: "Măng Đen - Đại ngàn Kon Tum",
      province: "Kon Tum",
      region: "tay-nguyen",
      regionName: "Tây Nguyên",
      cost: 1600000,
      duration: "2-3",
      durationHours: 24,
      durationText: "2 - 3 ngày (24h)",
      preferences: ["chua-lanh", "thien-nhien"],
      preferenceLabels: ["🌿 Đà Lạt thứ hai", "🌲 Rừng thông bạt ngàn"],
      rating: 4.6,
      description: "Vùng đất thanh bình giữa rừng thông nguyên sinh se lạnh, hồ Đăk Ke thơ mộng, thác Pa Sỹ hoang sơ và văn hóa cồng chiêng đại ngàn.",
      image: "../assets/images/travel/dalat.jpg",
    },
    {
      id: 18,
      name: "Hồ Tà Đùng - Hạ Long Tây Nguyên",
      province: "Đắk Nông",
      region: "tay-nguyen",
      regionName: "Tây Nguyên",
      cost: 1300000,
      duration: "2-3",
      durationHours: 24,
      durationText: "2 - 3 ngày (24h)",
      preferences: ["thien-nhien", "chua-lanh"],
      preferenceLabels: ["🌲 Tuyệt tác lòng hồ", "🌿 Glamping săn mây"],
      rating: 4.7,
      description: "Khung cảnh ngoạn mục của hơn 40 đảo lớn nhỏ nhấp nhô trên mặt hồ xanh biếc, trải nghiệm cắm trại săn mây sáng sớm và thưởng thức gà đồi nướng.",
      image: "../assets/images/travel/halong.jpg",
    },
    {
      id: 19,
      name: "Quần đảo Nam Du hoang sơ",
      province: "Kiên Giang",
      region: "tay-nam-bo",
      regionName: "Tây Nam Bộ",
      cost: 2100000,
      duration: "2-3",
      durationHours: 48,
      durationText: "2 - 3 ngày (48h)",
      preferences: ["bien", "thien-nhien"],
      preferenceLabels: ["🏖️ Biển đảo hoang sơ", "🌲 Lặn ngắm san hô"],
      rating: 4.6,
      description: "Bãi Cây Mến với dải dừa xanh mát uốn lượn bên bờ cát trắng, nước biển trong vắt thấy đáy và hải sản nhum nướng mỡ hành tươi rói.",
      image: "../assets/images/travel/phuquoc.jpg",
    },
    {
      id: 20,
      name: "Khu bảo tồn Pù Luông",
      province: "Thanh Hóa",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 1500000,
      duration: "2-3",
      durationHours: 24,
      durationText: "2 - 3 ngày (24h)",
      preferences: ["thien-nhien", "chua-lanh"],
      preferenceLabels: ["🌲 Ruộng bậc thang", "🌿 Nghỉ dưỡng ecolodge"],
      rating: 4.7,
      description: "Nghỉ dưỡng ecolodge ngắm mây trôi thung lũng, chiêm ngưỡng ruộng bậc thang rực rỡ mùa lúa chín và tắm mát suối thác Hiêu giữa rừng già.",
      image: "../assets/images/travel/trangan.jpg",
    },
    {
      id: 21,
      name: "Suối khoáng nóng Yoko Onsen",
      province: "Quảng Ninh",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 1800000,
      duration: "1",
      durationHours: 8,
      durationText: "Đi trong ngày (8h)",
      preferences: ["chua-lanh"],
      preferenceLabels: ["🌿 Onsen khoáng nóng", "🧘 Chăm sóc phục hồi"],
      rating: 4.8,
      description: "Trải nghiệm tắm khoáng Onsen chuẩn phong cách Nhật Bản giữa thung lũng Quang Hanh xanh mát, xông hơi đá muối Himalaya và phục hồi năng lượng.",
      image: "../assets/images/travel/dalat.jpg",
    },
    {
      id: 22,
      name: "Vườn quốc gia Phong Nha - Kẻ Bàng",
      province: "Quảng Bình",
      region: "trung",
      regionName: "Miền Trung",
      cost: 2800000,
      duration: "2-3",
      durationHours: 36,
      durationText: "2 - 3 ngày (36h)",
      preferences: ["thien-nhien"],
      preferenceLabels: ["🌲 Vương quốc hang động", "🛶 Chèo kayak sông Son"],
      rating: 4.8,
      description: "Thám hiểm Động Thiên Đường nguy nga, chèo thuyền kayak trên dòng sông Son ngọc bích và đu zipline khám phá Hang Tối kỳ thú.",
      image: "../assets/images/travel/trangan.jpg",
    },
    {
      id: 23,
      name: "Du thuyền Vịnh Lan Hạ 5 sao",
      province: "Hải Phòng",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 5800000,
      duration: "2-3",
      durationHours: 48,
      durationText: "2 - 3 ngày (48h)",
      preferences: ["bien", "chua-lanh"],
      preferenceLabels: ["🏖️ Du thuyền 5 sao", "🌿 Nghỉ dưỡng cao cấp"],
      rating: 4.9,
      description: "Kỳ nghỉ đẳng cấp trên du thuyền cao cấp lướt êm giữa vịnh Lan Hạ thơ mộng, chèo kayak qua Hang Sáng Tối và tiệc nướng BBQ hải sản trên boong tàu.",
      image: "../assets/images/travel/halong.jpg",
    },
    {
      id: 24,
      name: "Quần đảo Côn Đảo hoang sơ",
      province: "Bà Rịa - Vũng Tàu",
      region: "nam",
      regionName: "Miền Nam",
      cost: 5200000,
      duration: "4-5",
      durationHours: 60,
      durationText: "4 - 5 ngày (60h)",
      preferences: ["bien", "van-hoa"],
      preferenceLabels: ["🏖️ Biển ngọc hoang sơ", "🏛️ Dấu ấn lịch sử"],
      rating: 4.8,
      description: "Hành trình ý nghĩa viếng Nghĩa trang Hàng Dương, khám phá hệ sinh thái biển nguyên sinh Bãi Đầm Trầu và trải nghiệm ngắm rùa đẻ trứng tại Hòn Bảy Cạnh.",
      image: "../assets/images/travel/phuquoc.jpg",
    },
    {
      id: 25,
      name: "Thám hiểm Hang Tú Làn",
      province: "Quảng Bình",
      region: "trung",
      regionName: "Miền Trung",
      cost: 7500000,
      duration: "4-5",
      durationHours: 72,
      durationText: "4 - 5 ngày (72h)",
      preferences: ["thien-nhien"],
      preferenceLabels: ["🌲 Thám hiểm mạo hiểm", "🏕️ Cắm trại sông ngầm"],
      rating: 4.9,
      description: "Tour mạo hiểm đẳng cấp quốc tế: bơi sông ngầm kỳ bí dưới bóng thạch nhũ, băng rừng rậm nguyên sinh và cắm trại giữa thung lũng đá vôi ngoạn mục.",
      image: "../assets/images/travel/trangan.jpg",
    },
    {
      id: 26,
      name: "Resort Vịnh Vĩnh Hy & Núi Chúa",
      province: "Ninh Thuận",
      region: "trung",
      regionName: "Miền Trung",
      cost: 6500000,
      duration: "4-5",
      durationHours: 72,
      durationText: "4 - 5 ngày (72h)",
      preferences: ["bien", "chua-lanh"],
      preferenceLabels: ["🏖️ Vịnh biển hoang sơ", "🌿 Resort triệu đô"],
      rating: 4.9,
      description: "Nghỉ dưỡng thượng lưu nhìn ra một trong những vịnh biển đẹp nhất thế giới, đi tàu đáy kính ngắm san hô và trekking vườn quốc gia Núi Chúa độc đáo.",
      image: "../assets/images/travel/phuquoc.jpg",
    },
  ];

  // Trạng thái bộ lọc và sắp xếp
  const filterState = {
    keyword: "",
    region: "all",
    budgetRange: "all",
    maxBudget: null,
    duration: "all",
    preference: "all",
    sortBy: "wsm",
  };

  // DOM Elements
  const searchInput = document.getElementById("travel-search-input");
  const maxBudgetInput = document.getElementById("travel-max-budget");
  const durationSelect = document.getElementById("travel-duration-select");
  const preferenceSelect = document.getElementById("travel-preference-select");
  const sortSelect = document.getElementById("travel-sort-select");
  const btnSearch = document.getElementById("btn-travel-search");
  const btnReset = document.getElementById("btn-travel-reset");
  const btnEmptyReset = document.getElementById("btn-travel-empty-reset");

  const regionChips = document.querySelectorAll("#chip-travel-regions .dh-chip");
  const budgetChips = document.querySelectorAll("#chip-travel-budgets .dh-chip");

  const resultsGrid = document.getElementById("travel-results-grid");
  const resultsCount = document.getElementById("travel-results-count");
  const emptyState = document.getElementById("travel-empty");

  // Kiểm tra điểm đến có thỏa mãn điều kiện ngân sách hay không
  function matchBudget(item) {
    // 1. Nếu người dùng nhập trực tiếp số tiền ở ô input
    if (filterState.maxBudget && filterState.maxBudget > 0) {
      return item.cost <= filterState.maxBudget;
    }

    // 2. Hoặc nếu người dùng chọn chip khoảng giá nhanh
    switch (filterState.budgetRange) {
      case "1000000":
        return item.cost <= 1000000;
      case "3000000":
        return item.cost >= 1000000 && item.cost <= 3000000;
      case "5000000":
        return item.cost >= 3000000 && item.cost <= 5000000;
      case "5000001":
        return item.cost > 5000000;
      default:
        return true;
    }
  }

  // Lọc danh sách điểm đến dựa trên các điều kiện ràng buộc bắt buộc (Hard Constraints)
  function filterDestinations() {
    return TRAVEL_DESTINATIONS.filter((item) => {
      // 1. Từ khóa (tên điểm đến hoặc tỉnh thành)
      if (filterState.keyword) {
        const kw = filterState.keyword.toLowerCase().trim();
        const matchName = item.name.toLowerCase().includes(kw);
        const matchProv = item.province.toLowerCase().includes(kw);
        if (!matchName && !matchProv) return false;
      }

      // 2. Vùng miền
      if (filterState.region !== "all" && item.region !== filterState.region) {
        return false;
      }

      // 3. Ngân sách
      if (!matchBudget(item)) {
        return false;
      }

      // 4. Thời lượng
      if (filterState.duration !== "all" && item.duration !== filterState.duration) {
        return false;
      }

      // 5. Sở thích
      if (filterState.preference !== "all" && !item.preferences.includes(filterState.preference)) {
        return false;
      }

      return true;
    });
  }

  // Chuẩn hóa và tính điểm WSM động cho tập điểm đến đã lọc theo Decision Engine
  // Rubric: Chi phí (min, 40%) + Thời lượng (min, 30%) + Hoạt động (max, 30%)
  function calculateWsmScores(items) {
    if (items.length === 0) return [];
    if (items.length === 1) {
      return [
        {
          ...items[0],
          calculatedScore: 95.0,
          criteriaScores: { cost: 95, duration: 95, activities: 95 },
        },
      ];
    }

    const costs = items.map((i) => i.cost);
    const minCost = Math.min(...costs);
    const maxCost = Math.max(...costs);

    const durations = items.map((i) => i.durationHours || 24);
    const minDur = Math.min(...durations);
    const maxDur = Math.max(...durations);

    return items.map((item) => {
      // Tiêu chí 1: Chi phí (min - càng thấp càng tốt, trọng số 0.40)
      const sCost = maxCost === minCost ? 100 : ((maxCost - item.cost) / (maxCost - minCost)) * 100;

      // Tiêu chí 2: Thời lượng (min - tối ưu thời gian, trọng số 0.30)
      const dur = item.durationHours || 24;
      const sDur = maxDur === minDur ? 100 : ((maxDur - dur) / (maxDur - minDur)) * 100;

      // Tiêu chí 3: Hoạt động & Đánh giá (max - càng cao càng tốt, trọng số 0.30)
      let sAct = (item.rating / 5.0) * 100;
      if (filterState.preference !== "all" && item.preferences.includes(filterState.preference)) {
        // Tăng điểm tương thích khi đúng sở thích người dùng chọn
        sAct = Math.min(100, sAct * 0.5 + 50);
      }

      // Tổng điểm WSM
      const totalScore = Number((0.4 * sCost + 0.3 * sDur + 0.3 * sAct).toFixed(1));

      return {
        ...item,
        calculatedScore: totalScore,
        criteriaScores: {
          cost: Math.round(sCost),
          duration: Math.round(sDur),
          activities: Math.round(sAct),
        },
      };
    });
  }

  // Sắp xếp ứng viên theo tiêu chuẩn WSM (có tie-breakers) hoặc theo tùy chọn
  function sortDestinations(scoredItems) {
    const sortMode = filterState.sortBy || "wsm";
    return [...scoredItems].sort((a, b) => {
      if (sortMode === "cost-asc") return a.cost - b.cost;
      if (sortMode === "cost-desc") return b.cost - a.cost;
      if (sortMode === "rating-desc") return b.rating - a.rating;

      // Mặc định: Xếp hạng WSM giảm dần kèm tie-breakers chuẩn
      if (b.calculatedScore !== a.calculatedScore) {
        return b.calculatedScore - a.calculatedScore;
      }
      // Tie-breaker 1: Chi phí thấp hơn ưu tiên trước
      if (a.cost !== b.cost) {
        return a.cost - b.cost;
      }
      // Tie-breaker 2: Tên theo thứ tự chữ cái A-Z
      return a.name.localeCompare(b.name, "vi");
    });
  }

  // Render danh sách thẻ điểm đến
  function renderResults(list) {
    if (!resultsGrid || !emptyState || !resultsCount) return;

    if (list.length === 0) {
      resultsGrid.innerHTML = "";
      emptyState.classList.remove("d-none");
      resultsCount.textContent = "Không tìm thấy điểm đến nào phù hợp";
      return;
    }

    emptyState.classList.add("d-none");
    resultsCount.textContent = `Tìm thấy ${list.length} địa điểm gợi ý phù hợp (đã xếp hạng)`;

    const html = list
      .map((item, index) => {
        const rank = index + 1;
        const rankClass = rank === 1 ? "rank-1" : rank === 2 ? "rank-2" : rank === 3 ? "rank-3" : "";
        const rankText = rank === 1 ? "🥇 #1 Top đề xuất" : rank === 2 ? "🥈 #2" : rank === 3 ? "🥉 #3" : `#${rank}`;

        const safeName = typeof escapeHtml === "function" ? escapeHtml(item.name) : item.name;
        const safeProv = typeof escapeHtml === "function" ? escapeHtml(item.province) : item.province;
        const safeDesc = typeof escapeHtml === "function" ? escapeHtml(item.description) : item.description;
        const formattedCost = typeof formatMoney === "function" ? formatMoney(item.cost) : item.cost.toLocaleString("vi-VN") + " ₫";

        const tagsHtml = item.preferenceLabels
          .map((label) => `<span class="travel-tag-pill">${escapeHtml(label)}</span>`)
          .join(" ");

        return `
          <div class="col-12 col-md-6 col-xl-4">
            <article class="travel-item-card" aria-label="${safeName}">
              <!-- Ảnh đại diện & badges -->
              <div class="travel-card-media">
                <img
                  src="${item.image}"
                  alt="${safeName}"
                  class="travel-card-img"
                  loading="lazy"
                  onerror="this.src='../assets/images/travel/dalat.jpg'"
                >
                <span class="travel-rank-pill ${rankClass}">${rankText}</span>
                <span class="travel-floating-badge">★ ${item.calculatedScore.toFixed(1)} WSM</span>
                <span class="travel-region-pill">${escapeHtml(item.regionName)}</span>
              </div>

              <!-- Nội dung thẻ -->
              <div class="travel-card-body">
                <h3 class="travel-card-title">${safeName}</h3>
                <div class="travel-card-location">
                  <span>📍</span>
                  <span>${safeProv}</span>
                </div>

                <!-- Điểm chi tiết 3 tiêu chí WSM -->
                <div class="travel-criteria-scores">
                  <span class="travel-criteria-item" title="Điểm chi phí (tối ưu ngân sách)">💰 Giá: <strong>${item.criteriaScores.cost}</strong></span>
                  <span class="travel-criteria-item" title="Điểm thời lượng (tối ưu thời gian)">⏱️ Thời lượng: <strong>${item.criteriaScores.duration}</strong></span>
                  <span class="travel-criteria-item" title="Điểm sở thích & chất lượng">🎯 Trải nghiệm: <strong>${item.criteriaScores.activities}</strong></span>
                </div>

                <!-- Thông số ngân sách & thời lượng -->
                <div class="travel-card-specs">
                  <div>
                    <div class="travel-cost-lbl">Ngân sách ước tính</div>
                    <div class="travel-cost-val">${formattedCost}</div>
                  </div>
                  <div class="text-end">
                    <div class="travel-cost-lbl">Thời lượng</div>
                    <div class="travel-duration-val">⏱️ ${escapeHtml(item.durationText)}</div>
                  </div>
                </div>

                <!-- Tags sở thích -->
                <div class="travel-tags-wrap">
                  ${tagsHtml}
                </div>

                <!-- Mô tả tóm tắt -->
                <p class="travel-card-desc">${safeDesc}</p>

                <!-- Footer hành động -->
                <div class="travel-card-footer">
                  <div class="travel-rating-box">
                    <span class="travel-rating-star">⭐</span>
                    <span>${item.rating} / 5.0</span>
                  </div>
                  <a href="travel-results.html" class="dh-btn dh-btn-sm dh-btn-outline" style="text-decoration:none;">
                    Chi tiết đề xuất →
                  </a>
                </div>
              </div>
            </article>
          </div>
        `;
      })
      .join("");

    resultsGrid.innerHTML = html;
  }

  // Áp dụng bộ lọc, chấm điểm WSM và render lại
  function applyFilter() {
    const filtered = filterDestinations();
    const scored = calculateWsmScores(filtered);
    const sorted = sortDestinations(scored);
    renderResults(sorted);
  }

  // Đặt lại toàn bộ form về mặc định
  function resetFilter() {
    filterState.keyword = "";
    filterState.region = "all";
    filterState.budgetRange = "all";
    filterState.maxBudget = null;
    filterState.duration = "all";
    filterState.preference = "all";
    filterState.sortBy = "wsm";

    if (searchInput) searchInput.value = "";
    if (maxBudgetInput) maxBudgetInput.value = "";
    if (durationSelect) durationSelect.value = "all";
    if (preferenceSelect) preferenceSelect.value = "all";
    if (sortSelect) sortSelect.value = "wsm";

    regionChips.forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.region === "all");
    });

    budgetChips.forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.budget === "all");
    });

    applyFilter();
    if (typeof showToast === "function") {
      showToast("Đã đặt lại bộ lọc tìm kiếm", "success");
    }
  }

  // Gắn sự kiện tương tác
  function initEvents() {
    // 1. Ô tìm kiếm từ khóa
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        filterState.keyword = e.target.value;
        applyFilter();
      });
      searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          applyFilter();
        }
      });
    }

    // 2. Nhập ngân sách tối đa
    if (maxBudgetInput) {
      maxBudgetInput.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        filterState.maxBudget = val ? Number(val) : null;
        // Bỏ active ở các chip khoảng giá nếu tự nhập tay
        if (val) {
          filterState.budgetRange = "custom";
          budgetChips.forEach((c) => c.classList.remove("active"));
        } else {
          filterState.budgetRange = "all";
          const allChip = document.querySelector("#chip-travel-budgets [data-budget='all']");
          if (allChip) allChip.classList.add("active");
        }
        applyFilter();
      });
    }

    // 3. Chip ngân sách nhanh
    budgetChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        budgetChips.forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");

        filterState.budgetRange = chip.dataset.budget;
        filterState.maxBudget = null;
        if (maxBudgetInput) maxBudgetInput.value = "";

        applyFilter();
      });
    });

    // 4. Chip vùng miền
    regionChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        regionChips.forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");

        filterState.region = chip.dataset.region;
        applyFilter();
      });
    });

    // 5. Select thời lượng
    if (durationSelect) {
      durationSelect.addEventListener("change", (e) => {
        filterState.duration = e.target.value;
        applyFilter();
      });
    }

    // 6. Select sở thích
    if (preferenceSelect) {
      preferenceSelect.addEventListener("change", (e) => {
        filterState.preference = e.target.value;
        applyFilter();
      });
    }

    // 7. Select sắp xếp xếp hạng
    if (sortSelect) {
      sortSelect.addEventListener("change", (e) => {
        filterState.sortBy = e.target.value;
        applyFilter();
      });
    }

    // 8. Nút tìm kiếm & nút đặt lại
    if (btnSearch) {
      btnSearch.addEventListener("click", () => {
        applyFilter();
        if (typeof showToast === "function") {
          showToast("Đã cập nhật kết quả tìm kiếm", "success");
        }
      });
    }

    if (btnReset) {
      btnReset.addEventListener("click", resetFilter);
    }

    if (btnEmptyReset) {
      btnEmptyReset.addEventListener("click", resetFilter);
    }

    // 9. Đóng/mở sidebar trên màn hình di động
    const sidebarEl = document.querySelector(".dh-sidebar");
    const sidebarToggleEl = document.querySelector("[data-sidebar-toggle]");
    if (sidebarToggleEl && sidebarEl) {
      sidebarToggleEl.addEventListener("click", () => {
        const isOpen = sidebarEl.classList.toggle("is-open");
        sidebarToggleEl.setAttribute("aria-expanded", String(isOpen));
      });
      document.addEventListener("click", (event) => {
        if (event.target.closest(".dh-sidebar, [data-sidebar-toggle]")) return;
        sidebarEl.classList.remove("is-open");
        sidebarToggleEl.setAttribute("aria-expanded", "false");
      });
    }
  }

  // Khởi chạy khi tài liệu sẵn sàng
  document.addEventListener("DOMContentLoaded", () => {
    initEvents();
    applyFilter();
  });
})();
