// Trang Khám phá món ăn (Food)
// - Lấy danh sách món ăn từ GET /api/v1/food
// - Khi bấm nút "detal", truyền thẳng item.id vào hàm xử lý để gọi GET /api/v1/food/{id}
//   và hiển thị khối chi tiết món ăn (#detall_food) ở giữa màn hình.

// shortcut: phân trang phía client trên dữ liệu GET /api/v1/food; chuyển sang limit/offset ở backend khi bảng foods vượt vài trăm món.
const DEFAULT_FOOD_IMAGE = "../assets/images/foods/hihi.png";
const FOODS_PER_PAGE = 10;

const MEAL_LABELS = {
  breakfast: "Bữa sáng",
  lunch: "Bữa trưa",
  dinner: "Bữa tối",
  snack: "Bữa nhẹ",
};

const gridEl = document.getElementById("food-results-grid");
const emptyEl = document.getElementById("food-empty");
const countEl = document.getElementById("food-results-count");
const paginationEl = document.getElementById("food-pagination");
const detailOverlayEl = document.getElementById("detall_food");
const btnCloseDetailEl = document.getElementById("btnCloseDetail");

let allFoods = [];
let currentPage = 1;

function renderFoodCards(foods) {
  if (!gridEl) return;

  gridEl.innerHTML = foods
    .map((item) => {
      const name = escapeHtml(item.name);
      const description = escapeHtml(item.description || "");
      const imageSrc = escapeHtml(item.image_url || DEFAULT_FOOD_IMAGE);

      return `
        <div class="card" data-food-id="${item.id}">
          <img
            src="${imageSrc}"
            class="card-img-top"
            alt="${name}"
          />
          <div class="card-body">
            <h5 class="card-title">${name}</h5>
            <p class="card-text">${description}</p>
            <div class="card-detail-book">
              <a
                href="#"
                class="btn-food-detail"
                data-food-id="${item.id}"
                data-action="detail"
                onclick="handleDetailClick(event, ${item.id})"
              >Chi tiết</a>
            </div>
          </div>
        </div>`;
    })
    .join("");
}

function renderPagination(totalPages) {
  if (!paginationEl) return;

  const pageButtons = Array.from({ length: totalPages }, (_, index) => {
    const p = index + 1;
    const isActive = p === currentPage;
    return `<button type="button" class="dh-btn dh-btn-sm food-page-btn ${isActive ? "dh-btn-primary" : "dh-btn-outline"}" data-page="${p}" ${isActive ? 'aria-current="page"' : ""}>${p}</button>`;
  }).join("");

  paginationEl.innerHTML = `
    <button type="button" class="dh-btn dh-btn-sm dh-btn-outline" data-page="${currentPage - 1}" ${currentPage <= 1 ? "disabled" : ""}>← Trước</button>
    ${pageButtons}
    <button type="button" class="dh-btn dh-btn-sm dh-btn-outline" data-page="${currentPage + 1}" ${currentPage >= totalPages ? "disabled" : ""}>Sau →</button>
  `;
  paginationEl.classList.remove("d-none");
}

function renderPage(page) {
  if (!gridEl) return;

  if (!allFoods.length) {
    gridEl.innerHTML = "";
    if (emptyEl) emptyEl.classList.remove("d-none");
    if (paginationEl) {
      paginationEl.innerHTML = "";
      paginationEl.classList.add("d-none");
    }
    if (countEl) countEl.textContent = "Hiển thị 0 phương án phù hợp";
    return;
  }

  if (emptyEl) emptyEl.classList.add("d-none");

  const totalPages = Math.ceil(allFoods.length / FOODS_PER_PAGE);
  currentPage = Math.min(Math.max(1, page), totalPages);
  const startIndex = (currentPage - 1) * FOODS_PER_PAGE;
  const endIndex = Math.min(startIndex + FOODS_PER_PAGE, allFoods.length);

  renderFoodCards(allFoods.slice(startIndex, endIndex));

  if (countEl) {
    countEl.textContent = `Hiển thị ${startIndex + 1}–${endIndex} / ${allFoods.length} món ăn (Trang ${currentPage}/${totalPages})`;
  }

  renderPagination(totalPages);
}

function renderFoodDetail(food) {
  if (!detailOverlayEl) return;

  const imgEl = document.getElementById("mainFoodImage");
  const mealBadgeEl = document.getElementById("detailMealBadge");
  const priceEl = document.getElementById("detailFoodPrice");
  const prepTimeEl = document.getElementById("detailFoodPrepTime");
  const titleEl = document.getElementById("detailFoodTitle");
  const descEl = document.getElementById("detailFoodDesc");
  const ingTitleEl = document.getElementById("detailIngredientTitle");
  const ingListEl = document.getElementById("ingredientList");
  const tagTitleEl = document.getElementById("detailTagTitle");
  const tagListEl = document.getElementById("detailTagList");

  if (imgEl) {
    imgEl.src = food.image_url || DEFAULT_FOOD_IMAGE;
    imgEl.alt = food.name || "Chi tiết món ăn";
  }
  if (mealBadgeEl) {
    mealBadgeEl.textContent =
      MEAL_LABELS[food.meal_type] || food.meal_type || "Món ăn";
  }
  if (priceEl) {
    priceEl.textContent =
      typeof formatMoney === "function"
        ? formatMoney(food.price)
        : `${Number(food.price || 0).toLocaleString("vi-VN")} ₫`;
  }
  if (prepTimeEl) {
    prepTimeEl.textContent =
      food.prep_time != null ? `⏱ ${food.prep_time} phút` : "";
  }
  if (titleEl) {
    titleEl.textContent = food.name || "";
  }
  if (descEl) {
    descEl.textContent = food.description || "Chưa có mô tả cho món ăn này.";
  }

  const ingredients = Array.isArray(food.ingredients) ? food.ingredients : [];
  if (ingTitleEl) {
    ingTitleEl.textContent = `Nguyên liệu chính (${ingredients.length})`;
  }
  if (ingListEl) {
    ingListEl.innerHTML = ingredients.length
      ? ingredients
          .map(
            (ing) => `
              <li class="ingredient-item d-flex align-items-center justify-content-between">
                <span class="d-flex align-items-center gap-2 ingredient-name">
                  • ${escapeHtml(ing.name)}
                </span>
              </li>`,
          )
          .join("")
      : `<li class="ingredient-item"><span class="ingredient-name">Chưa có thông tin nguyên liệu</span></li>`;
  }

  const tags = Array.isArray(food.tags) ? food.tags : [];
  if (tagTitleEl) {
    tagTitleEl.textContent = `Nhãn món ăn (${tags.length})`;
  }
  if (tagListEl) {
    tagListEl.innerHTML = tags.length
      ? tags
          .map((tag) => `<li class="detail-tag-item">#${escapeHtml(tag)}</li>`)
          .join("")
      : `<li class="detail-tag-item">Chưa có nhãn</li>`;
  }

  detailOverlayEl.classList.add("active");
}

async function showFoodDetail(foodId) {
  if (!foodId) return;

  try {
    const response = await api.get(`/api/v1/food/${foodId}`);
    if (response && response.data) {
      renderFoodDetail(response.data);
    }
  } catch (error) {
    if (typeof showToast === "function") {
      showToast(error.message || "Không tải được chi tiết món ăn.", "error");
    }
  }
}

function handleDetailClick(event, foodId) {
  if (event) event.preventDefault();
  showFoodDetail(foodId);
}

function closeFoodDetail() {
  if (detailOverlayEl) {
    detailOverlayEl.classList.remove("active");
  }
}

window.handleDetailClick = handleDetailClick;
window.showFoodDetail = showFoodDetail;

if (btnCloseDetailEl) {
  btnCloseDetailEl.addEventListener("click", closeFoodDetail);
}

if (detailOverlayEl) {
  detailOverlayEl.addEventListener("click", (event) => {
    if (event.target === detailOverlayEl) {
      closeFoodDetail();
    }
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeFoodDetail();
  }
});

if (paginationEl) {
  paginationEl.addEventListener("click", (event) => {
    const btn = event.target.closest("button[data-page]");
    if (!btn || btn.disabled) return;
    const targetPage = Number(btn.dataset.page);
    if (Number.isInteger(targetPage) && targetPage !== currentPage) {
      renderPage(targetPage);
      gridEl.closest(".dh-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
}

async function loadAllFoods() {
  if (!gridEl) return;

  try {
    const response = await api.get("/api/v1/food");
    allFoods = Array.isArray(response.data) ? response.data : [];
    renderPage(1);
  } catch (error) {
    if (countEl) {
      countEl.textContent = error.message || "Không tải được danh sách món ăn.";
    }
    if (typeof showToast === "function") {
      showToast(
        error.message || "Không tải được chi tiết danh sách món ăn.",
        "error",
      );
    }
  }
}

// ---------- Menu mobile ----------
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

loadAllFoods();
