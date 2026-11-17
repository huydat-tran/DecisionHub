// Trang Khám phá món ăn (Food)
// - Lấy danh sách món ăn từ GET /api/v1/food
// - Khi bấm nút "detal", truyền thẳng item.id vào hàm xử lý để gọi GET /api/v1/food/{id}
//   và hiển thị khối chi tiết món ăn (#detall_food) ở giữa màn hình.

const DEFAULT_FOOD_IMAGE = "../assets/images/foods/hihi.png";

const MEAL_LABELS = {
  breakfast: "Bữa sáng",
  lunch: "Bữa trưa",
  dinner: "Bữa tối",
  snack: "Bữa nhẹ",
};

const gridEl = document.getElementById("food-results-grid");
const emptyEl = document.getElementById("food-empty");
const countEl = document.getElementById("food-results-count");
const detailOverlayEl = document.getElementById("detall_food");
const btnCloseDetailEl = document.getElementById("btnCloseDetail");

function renderFoods(foods) {
  if (!gridEl) return;

  if (countEl) {
    countEl.textContent = `Hiển thị ${foods.length} phương án phù hợp`;
  }

  if (!foods.length) {
    gridEl.innerHTML = "";
    if (emptyEl) emptyEl.classList.remove("d-none");
    return;
  }

  if (emptyEl) emptyEl.classList.add("d-none");

  gridEl.innerHTML = foods
    .map((item) => {
      const name = escapeHtml(item.name);
      const description = escapeHtml(item.description || "");
      const imageSrc = escapeHtml(item.image_url || DEFAULT_FOOD_IMAGE);

      return `
        <div class="card" style="width: 12rem" data-food-id="${item.id}">
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

async function loadAllFoods() {
  if (!gridEl) return;

  try {
    const response = await api.get("/api/v1/food");
    const foods = Array.isArray(response.data) ? response.data : [];
    renderFoods(foods);
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

loadAllFoods();
