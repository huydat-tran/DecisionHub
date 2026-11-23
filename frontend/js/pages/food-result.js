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
    ingredients: [
      "bánh mì",
      "thịt heo",
      "chả lụa",
      "pate",
      "dưa leo",
      "hành ngò",
    ],
    tags: ["nhanh", "khô", "giòn", "tiết kiệm"],
    image: "../assets/images/foods/banhmi.jpg",
  },
  {
    id: 3,
    name: "Bún chả Hà Nội",
    price: 50000,
    prep_time: 20,
    meal_types: ["lunch", "dinner"],
    ingredients: [
      "bún",
      "thịt heo",
      "chả nướng",
      "nước mắm",
      "rau sống",
      "đu đủ",
    ],
    tags: ["đậm đà", "truyền thống", "thịt", "nổi tiếng"],
    image: "../assets/images/foods/buncha.jpg",
  },
  {
    id: 4,
    name: "Cơm tấm sườn bì chả",
    price: 55000,
    prep_time: 15,
    meal_types: ["breakfast", "lunch", "dinner"],
    ingredients: [
      "cơm tấm",
      "sườn heo",
      "bì",
      "chả trứng",
      "mỡ hành",
      "nước mắm",
    ],
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
    ingredients: [
      "mì quảng",
      "tôm",
      "thịt heo",
      "bánh tráng mè",
      "đậu phộng",
      "rau sống",
    ],
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
    price: 65000,
    prep_time: 25,
    meal_types: ["dinner"],
    ingredients: ["thịt bò", "tôm", "rau", "nấm", "nước lẩu"],
    tags: ["nóng", "nhiều món", "ấm bụng"],
    image: "../assets/images/foods/hihi.png",
  },
];

// Client-Side Decision Engine: mô phỏng thuật toán WSM chuẩn xác khi Backend offline
function filterAndScoreFoods(payload) {
  const budgetMax = Number(payload.budget_max || 100000);
  const mealType = payload.meal_type
    ? String(payload.meal_type).trim().toLowerCase()
    : null;
  const maxPrepTime = payload.max_prep_time
    ? Number(payload.max_prep_time)
    : null;
  const avoidList = Array.isArray(payload.excluded_ingredients)
    ? payload.excluded_ingredients
        .map((s) => s.trim().toLowerCase())
        .filter(Boolean)
    : [];
  const prefTags = Array.isArray(payload.preferred_tags)
    ? payload.preferred_tags.map((s) => s.trim().toLowerCase()).filter(Boolean)
    : [];
  const limit = Math.min(20, Math.max(1, Number(payload.limit || 5)));

  const validCandidates = [];
  const excludedCandidates = [];

  FOOD_CATALOG.forEach((item) => {
    const reasons = [];

    // 1. Kiểm tra ngân sách
    if (item.price > budgetMax) {
      reasons.push(
        `Giá (${item.price.toLocaleString("vi-VN")} ₫) vượt quá ngân sách tối đa (${budgetMax.toLocaleString("vi-VN")} ₫).`,
      );
    }

    // 2. Kiểm tra loại bữa ăn
    if (
      mealType &&
      Array.isArray(item.meal_types) &&
      !item.meal_types.includes(mealType)
    ) {
      const mealLabels = {
        breakfast: "bữa sáng",
        lunch: "bữa trưa",
        dinner: "bữa tối",
        snack: "bữa phụ / ăn vặt",
      };
      reasons.push(
        `Loại bữa ăn không phù hợp với yêu cầu (${mealLabels[mealType] || mealType}).`,
      );
    }

    // 3. Kiểm tra thời gian chuẩn bị tối đa
    if (maxPrepTime && item.prep_time > maxPrepTime) {
      reasons.push(
        `Thời gian chuẩn bị (${item.prep_time} phút) vượt quá giới hạn tối đa (${maxPrepTime} phút).`,
      );
    }

    // 4. Kiểm tra nguyên liệu cần tránh
    if (avoidList.length > 0 && Array.isArray(item.ingredients)) {
      const matchedAvoid = item.ingredients.filter((ing) =>
        avoidList.some(
          (avoid) =>
            ing.toLowerCase().includes(avoid) ||
            avoid.includes(ing.toLowerCase()),
        ),
      );
      if (matchedAvoid.length > 0) {
        reasons.push(`Chứa nguyên liệu cần tránh: ${matchedAvoid.join(", ")}.`);
      }
    }

    if (reasons.length > 0) {
      excludedCandidates.push({
        id: item.id,
        name: item.name,
        status: "excluded",
        is_excluded: true,
        exclusion_reason: reasons.join(" "),
        exclusion_reasons: reasons,
      });
    } else {
      validCandidates.push(item);
    }
  });

  if (validCandidates.length === 0) {
    return {
      items: [],
      excluded_items: excludedCandidates,
      total: 0,
      total_excluded: excludedCandidates.length,
      has_valid_candidates: false,
      message:
        "Không có phương án hợp lệ để đánh giá do tất cả phương án đều đã bị loại bởi điều kiện bắt buộc.",
    };
  }

  // Chấm điểm từng tiêu chí theo WSM
  const scoredCandidates = validCandidates.map((cand) => {
    // Tiêu chí 1: Giá (Cost: càng rẻ càng tốt)
    // price_score = 100 * (1 - price / budgetMax)
    const priceScore = Math.max(
      0,
      Math.min(100, Math.round(100 * (1 - cand.price / budgetMax))),
    );

    // Tiêu chí 2: Sở thích (Benefit: càng khớp tag càng tốt)
    let prefScore = 50.0;
    if (prefTags.length > 0 && Array.isArray(cand.tags)) {
      const matched = cand.tags.filter((t) =>
        prefTags.includes(t.toLowerCase()),
      ).length;
      prefScore = Math.round((matched / prefTags.length) * 100);
    }

    // Tiêu chí 3: Thời gian chuẩn bị (Cost: càng nhanh càng tốt)
    let prepScore = 50.0;
    if (maxPrepTime) {
      prepScore = Math.max(
        0,
        Math.min(100, Math.round(100 * (1 - cand.prep_time / maxPrepTime))),
      );
    } else {
      // Chuẩn hóa theo khoảng 0-30 phút
      prepScore = Math.max(
        0,
        Math.min(100, Math.round(100 * (1 - cand.prep_time / 30))),
      );
    }

    const wPrice = 0.4;
    const wPref = 0.35;
    const wPrep = 0.25;

    const contribPrice = Math.round(wPrice * priceScore * 100) / 100;
    const contribPref = Math.round(wPref * prefScore * 100) / 100;
    const contribPrep = Math.round(wPrep * prepScore * 100) / 100;
    const totalScore =
      Math.round((contribPrice + contribPref + contribPrep) * 100) / 100;

    return {
      id: cand.id,
      food_id: cand.id,
      name: cand.name,
      price: cand.price,
      prep_time: cand.prep_time,
      image: cand.image,
      score: totalScore,
      total_score: totalScore,
      criteria_scores: {
        price: priceScore,
        preference: prefScore,
        prep_time: prepScore,
      },
      criteria: {
        price: priceScore,
        preference: prefScore,
        prep_time: prepScore,
      },
      criteria_details: {
        price: {
          label: "Giá / Ngân sách",
          normalized_score: priceScore,
          weight: wPrice,
          contribution: contribPrice,
        },
        preference: {
          label: "Mức phù hợp nhu cầu/khẩu vị",
          normalized_score: prefScore,
          weight: wPref,
          contribution: contribPref,
        },
        prep_time: {
          label: "Thời gian chuẩn bị",
          normalized_score: prepScore,
          weight: wPrep,
          contribution: contribPrep,
        },
      },
      reasons: [
        `Mức giá ${cand.price.toLocaleString("vi-VN")} ₫ nằm trong ngân sách ${budgetMax.toLocaleString("vi-VN")} ₫`,
        `Thời gian làm ${cand.prep_time} phút`,
      ],
      advantages: [
        `Điểm giá đạt ${priceScore}/100`,
        `Thời gian chuẩn bị nhanh (${cand.prep_time} phút)`,
      ],
      disadvantages: [
        cand.price > budgetMax * 0.8
          ? "Giá tiệm cận mức ngân sách tối đa"
          : "Cần chọn thêm món phụ nếu dùng bữa chính",
      ],
      explanation: `Được đánh giá dựa trên mô hình WSM với tổng điểm ${totalScore.toFixed(1)}/100.`,
    };
  });

  // Xếp hạng: điểm giảm dần, hòa điểm thì rẻ hơn đứng trước
  scoredCandidates.sort(
    (a, b) =>
      b.total_score - a.total_score ||
      a.price - b.price ||
      a.name.localeCompare(b.name),
  );

  const rankedItems = scoredCandidates.slice(0, limit).map((item, idx) => {
    item.ranking = idx + 1;
    item.rank = idx + 1;
    return item;
  });

  return {
    items: rankedItems,
    excluded_items: excludedCandidates,
    total: rankedItems.length,
    total_excluded: excludedCandidates.length,
    has_valid_candidates: true,
    message: `Đánh giá thành công ${rankedItems.length} phương án hợp lệ.`,
  };
}

window.filterAndScoreFoods = filterAndScoreFoods;
window.FOOD_CATALOG = FOOD_CATALOG;
window.FOOD_CRITERIA = FOOD_CRITERIA;

// Dữ liệu khởi tạo ban đầu cho trang kết quả (trước khi người dùng gửi form lần đầu)
const defaultInit = filterAndScoreFoods({ budget_max: 50000, limit: 5 });
const FOOD_RESULTS = defaultInit.items;
const FOOD_EXCLUDED = defaultInit.excluded_items;

if (typeof DHResults !== "undefined" && typeof DHResults.initResultsPage === "function") {
  DHResults.initResultsPage({
    results: FOOD_RESULTS,
    criteria: FOOD_CRITERIA,
    excluded: FOOD_EXCLUDED,
  });
}
