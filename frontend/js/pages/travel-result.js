// Trang Đề xuất du lịch (Travel Recommendation).
//
// Dữ liệu mẫu + tiêu chí riêng của phân hệ Travel; phần hiển thị dùng chung
// nằm trong result-common.js (DHResults).

const TRAVEL_CRITERIA = [
  { key: "cost", label: "Chi phí tham khảo", weight: 0.4 },
  { key: "experience", label: "Mức phù hợp trải nghiệm", weight: 0.35 },
  { key: "duration", label: "Thời lượng & Tiếp cận", weight: 0.25 },
];

const TRAVEL_RESULTS = [
  {
    id: 101,
    name: "Phố cổ Hội An (Quảng Nam)",
    image: "../assets/images/travel/hoian.jpg",
    score: 88.5,
    ranking: 1,
    criteria: { cost: 85, experience: 95, duration: 84 },
    explanation:
      "Đứng đầu đề xuất du lịch nhờ điểm trải nghiệm văn hóa ẩm thực vượt trội (95/100) và chi phí du lịch hợp lý, phù hợp lịch trình 2-3 ngày.",
    advantages: [
      "Di sản văn hóa thế giới, trải nghiệm phố đi bộ và đèn lồng đặc sắc",
      "Ẩm thực phong phú, chi phí ăn uống và lưu trú rất phải chăng",
      "Thuận tiện kết hợp tham quan Đà Nẵng và biển An Bàng",
    ],
    disadvantages: [
      "Mùa cao điểm du lịch khá đông đúc",
      "Mùa mưa cuối năm (tháng 10 - 11) có nguy cơ ngập lụt",
    ],
  },
  {
    id: 102,
    name: "Vịnh Hạ Long (Quảng Ninh)",
    image: "../assets/images/travel/halong.jpg",
    score: 86.8,
    ranking: 2,
    criteria: { cost: 76, experience: 96, duration: 90 },
    explanation:
      "Xếp thứ hai với điểm trải nghiệm cảnh quan thiên nhiên kỳ vĩ đạt 96/100, đường cao tốc di chuyển nhanh chóng, chi phí du thuyền nhỉnh hơn các điểm khác.",
    advantages: [
      "Kỳ quan thiên nhiên thế giới với hàng nghìn đảo đá vôi kỳ thú",
      "Trải nghiệm du thuyền ngủ đêm và chèo thuyền kayak đẳng cấp",
      "Hạ tầng giao thông thuận tiện từ Hà Nội (chỉ khoảng 2 giờ)",
    ],
    disadvantages: [
      "Chi phí tour du thuyền cao hơn các hình thức du lịch tự túc",
      "Dễ bị ảnh hưởng bởi bão hoặc lệnh cấm tàu vào mùa mưa bão",
    ],
  },
  {
    id: 103,
    name: "Đà Lạt (Lâm Đồng)",
    image: "../assets/images/travel/dalat.jpg",
    score: 84.2,
    ranking: 3,
    criteria: { cost: 88, experience: 86, duration: 76 },
    explanation:
      "Được ưa chuộng nhờ khí hậu se lạnh quanh năm, chi phí nghỉ dưỡng và ẩm thực rất dễ chịu, thời gian di chuyển từ miền Bắc/Trung dài hơn.",
    advantages: [
      "Khí hậu mát mẻ ôn hòa quanh năm, cảnh quan thông reo lãng mạn",
      "Vô số quán cà phê đẹp, điểm check-in nông trại và đồi chè",
      "Chi phí dịch vụ ăn uống và homestay đa dạng, hợp túi tiền",
    ],
    disadvantages: [
      "Tình trạng đông đúc, ùn tắc vào các dịp lễ tết và cuối tuần",
      "Đường đèo dốc uốn lượn, cần tay lái vững khi tự di chuyển",
    ],
  },
  {
    id: 104,
    name: "Đảo Phú Quốc (Kiên Giang)",
    image: "../assets/images/travel/phuquoc.jpg",
    score: 81.6,
    ranking: 4,
    criteria: { cost: 68, experience: 94, duration: 84 },
    explanation:
      "Thiên đường nghỉ dưỡng biển đảo với tổ hợp giải trí hiện đại, tuy nhiên chi phí vé máy bay và lưu trú cao nên xếp thứ tư.",
    advantages: [
      "Bãi biển trong xanh, cát mịn và ngắm hoàng hôn đẹp nhất Việt Nam",
      "Tổ hợp vui chơi giải trí VinWonders, Safari và cáp treo Hòn Thơm",
      "Hải sản tươi ngon, hệ thống resort nghỉ dưỡng quốc tế phong phú",
    ],
    disadvantages: [
      "Chi phí vé máy bay và dịch vụ du lịch thuộc mức cao",
      "Khoảng cách giữa các cụm điểm tham quan Bắc đảo và Nam đảo khá xa",
    ],
  },
  {
    id: 105,
    name: "Tràng An - Bái Đính (Ninh Bình)",
    image: "../assets/images/travel/trangan.jpg",
    score: 79.4,
    ranking: 5,
    criteria: { cost: 86, experience: 82, duration: 92 },
    explanation:
      "Rất tối ưu cho chuyến đi ngắn 1 - 2 ngày với chi phí tiết kiệm và vị trí gần, nhưng hoạt động trải nghiệm về đêm chưa thực sự phong phú.",
    advantages: [
      "Di sản kép văn hóa và thiên nhiên, phong cảnh non nước kỳ vĩ",
      "Khoảng cách gần Hà Nội (chỉ khoảng 1.5 - 2 giờ di chuyển)",
      "Chi phí vé tham quan và dịch vụ thuyền đò niêm yết rõ ràng",
    ],
    disadvantages: [
      "Ngồi thuyền tham quan ngoài trời khá lâu, dễ bị nắng nóng mùa hè",
      "Các hoạt động vui chơi giải trí về đêm còn hạn chế",
    ],
  },
  {
    id: 106,
    name: "Sa Pa & Đỉnh Fansipan (Lào Cai)",
    image: "../assets/images/travel/halong.jpg",
    score: 78.8,
    ranking: 6,
    criteria: { cost: 74, experience: 88, duration: 75 },
    explanation:
      "Điểm đến hấp dẫn vùng núi Tây Bắc với nóc nhà Đông Dương Fansipan và văn hóa bản địa, tuy nhiên thời gian di chuyển từ miền Trung/Nam khá dài.",
    advantages: [
      "Hệ thống cáp treo Fansipan hiện đại, ngắm mây trời và thung lũng Mường Hoa",
      "Bản sắc văn hóa dân tộc H'Mông, Dao đỏ độc đáo cùng ẩm thực vùng cao",
      "Khí hậu mát mẻ quanh năm, mùa đông có cơ hội ngắm băng tuyết",
    ],
    disadvantages: [
      "Dễ bị say xe do cung đường đèo dốc uốn lượn liên tục",
      "Thời tiết thay đổi nhanh, mùa sương mù có thể hạn chế tầm nhìn trên đỉnh",
    ],
  },
  {
    id: 107,
    name: "Măng Đen - Đại ngàn (Kon Tum)",
    image: "../assets/images/travel/dalat.jpg",
    score: 77.2,
    ranking: 7,
    criteria: { cost: 82, experience: 80, duration: 70 },
    explanation:
      "Không gian sinh thái đại ngàn thanh bình, chi phí lưu trú và ăn uống tiết kiệm, rất phù hợp cho kỳ nghỉ chữa lành và thư giãn yên tĩnh.",
    advantages: [
      "Rừng thông nguyên sinh bạt ngàn, không khí trong lành không khói bụi",
      "Chi phí du lịch rất hợp lý, người dân bản địa thân thiện, mến khách",
      "Cảnh quan hoang sơ với thác Pa Sỹ, hồ Đăk Ke và đồi thông săn mây",
    ],
    disadvantages: [
      "Hạ tầng giao thông và dịch vụ du lịch vui chơi giải trí còn đơn giản",
      "Chưa có đường bay thẳng, cần di chuyển đường bộ từ Pleiku",
    ],
  },
];

DHResults.initResultsPage({ results: TRAVEL_RESULTS, criteria: TRAVEL_CRITERIA });
