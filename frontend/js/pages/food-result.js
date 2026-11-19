// ==========================================================
// Module: Food Results Data & Client-Side Decision Engine
// Chứa danh mục món ăn chuẩn và thuật toán lọc + chấm điểm WSM
// ==========================================================

const FOOD_CRITERIA = [
  { key: "price", label: "Giá", weight: 0.4 },
  { key: "preference", label: "Mức phù hợp nhu cầu/khẩu vị", weight: 0.35 },
  { key: "prep_time", label: "Thời gian chuẩn bị", weight: 0.25 },
];

// Danh mục toàn bộ món ăn thực tế của hệ thống
const FOOD_CATALOG = [
  {
    id: 1,
    name: "Phở bò tái",
    price: 45000,
    prep_time: 15,
    meal_types: ["breakfast", "dinner"],
    ingredients: ["bánh phở", "thịt bò", "hành lá", "nước dùng ninh xương"],
    tags: ["nước", "truyền thống", "nóng", "đậm đà"],
    image: "../assets/images/foods/phobo.jpg",
  },
  {
    id: 2,
    name: "Bánh mì thịt đặc biệt",
    price: 25000,
    prep_time: 5,
    meal_types: ["breakfast", "lunch", "snack"],
    ingredients: ["bánh mì", "thịt heo", "chả lụa", "pate", "dưa leo", "hành ngò"],
    tags: ["nhanh", "khô", "giòn", "tiết kiệm"],
    image: "../assets/images/foods/banhmi.jpg",
  },
  {
    id: 3,
    name: "Bún chả Hà Nội",
    price: 50000,
    prep_time: 20,
    meal_types: ["lunch", "dinner"],
    ingredients: ["bún", "thịt heo", "chả nướng", "nước mắm", "rau sống", "đu đủ"],
    tags: ["đậm đà", "truyền thống", "thịt", "nổi tiếng"],
    image: "../assets/images/foods/buncha.jpg",
  },
  {
    id: 4,
    name: "Cơm tấm sườn bì chả",
    price: 55000,
    prep_time: 15,
    meal_types: ["breakfast", "lunch", "dinner"],
    ingredients: ["cơm tấm", "sườn heo", "bì", "chả trứng", "mỡ hành", "nước mắm"],
    tags: ["no lâu", "đậm đà", "cơm", "năng lượng"],
    image: "../assets/images/foods/comtam.jpg",
  },
  {
    id: 5,
    name: "Cơm chiên đậu hũ nấm",
    price: 35000,
    prep_time: 12,
    meal_types: ["lunch", "dinner"],
    ingredients: ["cơm", "đậu hũ", "nấm", "cà rốt", "đậu hà lan"],
    tags: ["chay", "thanh đạm", "cơm", "healthy"],
    image: "../assets/images/foods/comtam.jpg",
  },
  {
    id: 6,
    name: "Mì Quảng tôm thịt",
    price: 48000,
    prep_time: 18,
    meal_types: ["lunch", "dinner"],
    ingredients: ["mì quảng", "tôm", "thịt heo", "bánh tráng mè", "đậu phộng", "rau sống"],
    tags: ["đậm đà", "miền trung", "hải sản"],
    image: "../assets/images/foods/buncha.jpg",
  },
  {
    id: 7,
    name: "Bún thái hải sản cay",
    price: 65000,
    prep_time: 25,
    meal_types: ["dinner"],
    ingredients: ["bún", "tôm", "mực", "nghêu", "sả", "ớt", "cà chua"],
    tags: ["cay", "chua cay", "hải sản", "nước", "ấm nóng"],
    image: "../assets/images/foods/laumini.jpg",
  },
  {
    id: 8,
    name: "Gỏi cuốn tôm thịt",
    price: 30000,
    prep_time: 10,
    meal_types: ["snack", "lunch"],
    ingredients: ["bánh tráng", "tôm", "thịt heo", "bún", "hẹ", "rau thơm"],
    tags: ["thanh mát", "nhẹ bụng", "healthy", "ít béo"],
    image: "../assets/images/foods/banhmi.jpg",
  },
  {
    id: 9,
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
