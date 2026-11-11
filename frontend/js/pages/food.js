// ==========================================================
// JS riêng cho phân hệ Food (Đề xuất món ăn - WhatShouldIEat)
// Dựa trên DecisionHub.md Mục 4 & UI Guidelines
// ==========================================================

const FOOD_ITEMS = [
  {
    id: 1,
    name: "Phở Bò Tái Nạm",
    meal_type: "breakfast",
    meal_name: "Bữa sáng",
    price: 45000,
    prep_time: 10,
    score: 92,
    description: "Phở bò truyền thống nước dùng hầm xương ngọt thanh, thơm mùi thảo mộc quế hồi.",
    reasons: ["Giá 45.000đ nằm trong ngân sách", "Thời gian ăn nhanh (~10 phút)", "Phù hợp cho bữa sáng"]
  },
  {
    id: 2,
    name: "Cơm Tấm Sườn Bì Chả",
    meal_type: "lunch",
    meal_name: "Bữa trưa",
    price: 40000,
    prep_time: 15,
    score: 88,
    description: "Cơm tấm hạt thơm ăn kèm sườn nướng mỡ hành đậm đà, chả trứng béo ngậy.",
    reasons: ["Nằm trong ngân sách trưa dưới 50.000đ", "No lâu và chuẩn bị nhanh (15 phút)"]
  },
  {
    id: 3,
    name: "Bún Chả Hà Nội",
    meal_type: "lunch",
    meal_name: "Bữa trưa",
    price: 50000,
    prep_time: 20,
    score: 84,
    description: "Thịt ba chỉ và chả viên nướng than hoa ăn kèm bún tươi và nước chấm chua ngọt.",
    reasons: ["Hương vị thanh mát dễ ăn vào buổi trưa", "Giá vừa vặn ngân sách"]
  },
  {
    id: 4,
    name: "Salad Rau Củ Ức Gà (Eat Clean)",
    meal_type: "dinner",
    meal_name: "Bữa tối",
    price: 48000,
    prep_time: 12,
    score: 81,
    description: "Rau xà lách tươi giòn kết hợp ức gà áp chảo và xốt mè rang thanh mát.",
    reasons: ["Thời gian chuẩn bị cực nhanh (12 phút)", "Nhẹ bụng thích hợp cho bữa tối"]
  },
  {
    id: 5,
    name: "Cơm Chiên Chay Rau Củ",
    meal_type: "lunch",
    meal_name: "Bữa trưa",
    price: 30000,
    prep_time: 15,
    score: 75,
    description: "Cơm chiên hạt sen vàng đều với ngô ngọt, đậu Hà Lan và nấm hương tươi thanh tịnh.",
    reasons: ["Món ăn chay thanh đạm", "Mức giá tiết kiệm chỉ 30.000đ"]
  }
];

let foodFilter = {
  keyword: "",
  meal: "all",
  maxPrice: null,
  maxPrep: null,
  diet: null
};

function formatMoney(num) {
  return Number(num).toLocaleString("vi-VN") + " ₫";
}

function renderFoodResults() {
  const grid = document.getElementById("food-results-grid");
  const countEl = document.getElementById("food-results-count");
  const emptyEl = document.getElementById("food-empty");
  if (!grid) return;

  let list = [...FOOD_ITEMS];

  // Lọc theo từ khóa
  if (foodFilter.keyword) {
    const q = foodFilter.keyword.toLowerCase().trim();
    list = list.filter(f => f.name.toLowerCase().includes(q) || f.description.toLowerCase().includes(q));
  }
  // Lọc theo bữa ăn
  if (foodFilter.meal !== "all") {
    list = list.filter(f => f.meal_type === foodFilter.meal);
  }
  // Lọc theo giá
  if (foodFilter.maxPrice) {
    list = list.filter(f => f.price <= foodFilter.maxPrice);
  }
  // Lọc theo thời gian chuẩn bị
  if (foodFilter.maxPrep) {
    list = list.filter(f => f.prep_time <= foodFilter.maxPrep);
  }
  // Lọc ăn chay
  if (foodFilter.diet === "chay") {
    list = list.filter(f => f.name.toLowerCase().includes("chay") || f.description.toLowerCase().includes("chay"));
  }

  countEl.textContent = `Hiển thị ${list.length} món ăn phù hợp`;

  if (list.length === 0) {
    grid.innerHTML = "";
    emptyEl.classList.remove("d-none");
    return;
  }
  emptyEl.classList.add("d-none");

  grid.innerHTML = list.map((item, idx) => `
    <div class="col-12 col-md-6 col-lg-4">
      <div class="dh-card food-item-card h-100 d-flex flex-column">
        <div class="dh-card-body d-flex flex-column flex-grow-1">
          <!-- WSM Score Badge -->
          <div class="d-flex align-items-center justify-content-between p-2 mb-2 rounded" style="background: var(--dh-primary-soft);">
            <div class="d-flex align-items-center gap-2">
              <span class="dh-score-value" style="font-size: 16px; color: var(--dh-primary); font-weight: 700;">#${idx + 1}</span>
              <span class="dh-small" style="font-weight: 600; color: var(--dh-primary);">Điểm WSM: ${item.score}/100</span>
            </div>
            <span class="dh-status dh-status-success food-card-badge">Phù hợp</span>
          </div>

          <div class="d-flex justify-content-between align-items-start mb-1">
            <h3 class="dh-section-title mb-0" style="font-size: 16px;">${item.name}</h3>
            <span class="badge bg-light text-dark border">${item.meal_name}</span>
          </div>

          <p class="dh-muted mb-2 flex-grow-1" style="font-size: 13px;">${item.description}</p>

          <!-- Lý do giải thích theo WSM -->
          <ul class="dh-reason-list mb-3">
            ${item.reasons.map(r => `
              <li class="dh-reason-item">
                <span class="dh-reason-icon">✓</span>
                <span style="font-size: 12px;">${r}</span>
              </li>
            `).join("")}
          </ul>

          <div class="d-flex justify-content-between align-items-center pt-2 border-top mt-auto">
            <div>
              <strong class="food-price-tag">${formatMoney(item.price)}</strong>
              <span class="food-time-tag d-block">⏱ ${item.prep_time} phút</span>
            </div>
            <span class="dh-small text-muted">Food P0</span>
          </div>
        </div>
      </div>
    </div>
  `).join("");
}

document.addEventListener("DOMContentLoaded", () => {
  renderFoodResults();

  // Mobile sidebar toggle
  const toggleBtn = document.querySelector("[data-sidebar-toggle]");
  const sidebar = document.querySelector(".dh-sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("is-open");
    });
  }

  // Tìm kiếm
  const searchInput = document.getElementById("food-search-input");
  const searchBtn = document.getElementById("btn-food-search");
  const resetBtn = document.getElementById("btn-food-reset");
  const emptyResetBtn = document.getElementById("btn-food-empty-reset");

  if (searchBtn && searchInput) {
    searchBtn.addEventListener("click", () => {
      foodFilter.keyword = searchInput.value;
      renderFoodResults();
    });
    searchInput.addEventListener("keyup", (e) => {
      if (e.key === "Enter") {
        foodFilter.keyword = searchInput.value;
        renderFoodResults();
      }
    });
  }

  // Chip bữa ăn
  const mealChips = document.getElementById("chip-food-meals");
  if (mealChips) {
    mealChips.addEventListener("click", (e) => {
      const chip = e.target.closest(".dh-chip");
      if (!chip) return;
      mealChips.querySelectorAll(".dh-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      foodFilter.meal = chip.getAttribute("data-meal");
      renderFoodResults();
    });
  }

  // Chip tiêu chí
  const criteriaChips = document.getElementById("chip-food-criterias");
  if (criteriaChips) {
    criteriaChips.addEventListener("click", (e) => {
      const chip = e.target.closest(".dh-chip");
      if (!chip) return;
      chip.classList.toggle("active");
      const p = chip.getAttribute("data-price");
      const prep = chip.getAttribute("data-prep");
      const diet = chip.getAttribute("data-diet");

      if (p) foodFilter.maxPrice = chip.classList.contains("active") ? Number(p) : null;
      if (prep) foodFilter.maxPrep = chip.classList.contains("active") ? Number(prep) : null;
      if (diet) foodFilter.diet = chip.classList.contains("active") ? diet : null;

      renderFoodResults();
    });
  }

  const resetAll = () => {
    foodFilter = { keyword: "", meal: "all", maxPrice: null, maxPrep: null, diet: null };
    if (searchInput) searchInput.value = "";
    if (mealChips) mealChips.querySelectorAll(".dh-chip").forEach((c, i) => c.classList.toggle("active", i === 0));
    if (criteriaChips) criteriaChips.querySelectorAll(".dh-chip").forEach(c => c.classList.remove("active"));
    renderFoodResults();
  };

  if (resetBtn) resetBtn.addEventListener("click", resetAll);
  if (emptyResetBtn) emptyResetBtn.addEventListener("click", resetAll);
});

