// Trang Đề xuất món ăn (Food Recommendation).
//
// Dữ liệu mẫu + tiêu chí riêng của phân hệ Food; phần hiển thị dùng chung
// nằm trong result-common.js (DHResults).

const FOOD_CRITERIA = [
  { key: "price", label: "Giá", weight: 0.4 },
  { key: "preference", label: "Mức phù hợp nhu cầu/khẩu vị", weight: 0.35 },
  { key: "prep_time", label: "Thời gian chuẩn bị", weight: 0.25 },
];

const FOOD_RESULTS = [
  {
    id: 1,
    name: "Bún chả Hà Nội",
    image: "../assets/images/foods/hihi.png",
    score: 87.3,
    ranking: 1,
    criteria: { price: 86, preference: 94, prep_time: 80 },
    explanation:
      "Đứng đầu nhờ điểm phù hợp khẩu vị cao nhất (94/100) và mức giá nằm trong ngân sách. Thời gian chuẩn bị ở mức khá nên chỉ bị trừ nhẹ ở tiêu chí này.",
    advantages: [
      "Mức phù hợp khẩu vị cao nhất trong 5 phương án",
      "Giá thấp hơn ngân sách tối đa",
      "Đủ đạm và rau, hợp một bữa trưa đầy đủ",
    ],
    disadvantages: [
      "Thời gian chuẩn bị lâu hơn phở và bánh mì",
      "Giá cao hơn bánh mì thịt",
    ],
  },
  {
    id: 2,
    name: "Phở bò tái",
    image: "../assets/images/foods/hihi.png",
    score: 85.2,
    ranking: 2,
    criteria: { price: 78, preference: 90, prep_time: 90 },
    explanation:
      "Xếp thứ hai nhờ chuẩn bị nhanh (90/100) và khẩu vị tốt (90/100). Giá cao hơn bún chả nên kém phương án đứng đầu 2,1 điểm.",
    advantages: [
      "Phục vụ nhanh, ít phải chờ",
      "Mức phù hợp khẩu vị cao",
      "Món nước nóng, dễ ăn",
    ],
    disadvantages: [
      "Giá cao hơn bún chả và bánh mì",
      "Thiên về đạm và tinh bột, ít rau",
    ],
  },
  {
    id: 3,
    name: "Bánh mì thịt",
    image: "../assets/images/foods/hihi.png",
    score: 84.5,
    ranking: 3,
    criteria: { price: 90, preference: 70, prep_time: 96 },
    explanation:
      "Thắng ở giá (90/100) và tốc độ chuẩn bị (96/100), nhưng mức phù hợp khẩu vị chỉ đạt 70/100 nên không vượt được hai phương án đầu.",
    advantages: [
      "Giá thấp nhất trong 5 phương án",
      "Chuẩn bị nhanh nhất, có thể mang đi",
      "Linh hoạt khi cần ăn vội",
    ],
    disadvantages: [
      "Mức phù hợp khẩu vị thấp nhất trong 5 phương án",
      "Khó no lâu nếu ăn một mình",
    ],
  },
  {
    id: 4,
    name: "Cơm tấm sườn",
    image: "../assets/images/foods/hihi.png",
    score: 80.6,
    ranking: 4,
    criteria: { price: 72, preference: 88, prep_time: 84 },
    explanation:
      "Khẩu vị tốt (88/100) và chuẩn bị khá nhanh (84/100), nhưng điểm giá chỉ 72/100 nên điểm tổng dừng ở 80,6.",
    advantages: [
      "No lâu, đủ năng lượng cho buổi chiều",
      "Mức phù hợp khẩu vị cao",
      "Thời gian chuẩn bị ngắn",
    ],
    disadvantages: [
      "Giá cao hơn nhiều phương án khác",
      "Dễ vượt ngân sách nếu gọi thêm món",
    ],
  },
  {
    id: 5,
    name: "Lẩu mini một người",
    image: "../assets/images/foods/hihi.png",
    score: 60.5,
    ranking: 5,
    criteria: { price: 52, preference: 82, prep_time: 44 },
    explanation:
      "Khẩu vị khá (82/100) nhưng giá cao (52/100) và thời gian chuẩn bị dài (44/100) nên điểm tổng thấp nhất nhóm.",
    advantages: [
      "Phù hợp khi muốn ăn ấm, nhiều món",
      "Có thể điều chỉnh khẩu phần",
    ],
    disadvantages: [
      "Điểm giá thấp nhất trong 5 phương án",
      "Thời gian chuẩn bị dài nhất",
      "Không phù hợp khi cần ăn nhanh",
    ],
  },
];

DHResults.initResultsPage({ results: FOOD_RESULTS, criteria: FOOD_CRITERIA });
