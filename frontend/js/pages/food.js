// Xử lý form gợi ý món ăn theo tiêu chí trên trang Food.

(function () {
  const ALLOWED_MEAL_TYPES = {
    breakfast: "Bữa sáng",
    lunch: "Bữa trưa",
    dinner: "Bữa tối",
    snack: "Bữa phụ / Ăn vặt",
  };

  const MAX_BUDGET_LIMIT = 100000000;
  const MAX_AVOID_ITEMS = 10;
  const INGREDIENT_PATTERN = /^[\p{L}\p{N}\s-]+$/u;
  const HAS_LETTER_PATTERN = /\p{L}/u;

  const form = document.getElementById("food-recommend-form");
  if (!form) return;

  const maxBudgetInput = document.getElementById("food-max-budget");
  const mealTypeSelect = document.getElementById("food-meal-type");
  const avoidInput = document.getElementById("food-avoid-ingredients");

  const maxBudgetError = document.getElementById("food-max-budget-error");
  const mealTypeError = document.getElementById("food-meal-type-error");
  const avoidError = document.getElementById("food-avoid-ingredients-error");
  const statusBox = document.getElementById("food-recommend-status");

  function setFieldError(inputEl, errorEl, message) {
    errorEl.textContent = message;
    if (message) {
      inputEl.classList.add("food-input-invalid");
      inputEl.setAttribute("aria-invalid", "true");
    } else {
      inputEl.classList.remove("food-input-invalid");
      inputEl.removeAttribute("aria-invalid");
    }
  }

  function validateMaxBudget() {
    const raw = maxBudgetInput.value.trim();
    if (!raw) {
      return { valid: false, message: "Vui lòng nhập ngân sách tối đa." };
    }

    const value = Number(raw);
    if (!Number.isFinite(value) || value <= 0) {
      return { valid: false, message: "Ngân sách tối đa phải lớn hơn 0." };
    }

    if (!Number.isInteger(value)) {
      return { valid: false, message: "Ngân sách tối đa phải là số nguyên (VNĐ)." };
    }

    if (value > MAX_BUDGET_LIMIT) {
      return { valid: false, message: "Ngân sách tối đa không vượt quá 100.000.000 VNĐ." };
    }

    return { valid: true, value };
  }

  function validateMealType() {
    const value = mealTypeSelect.value.trim();
    if (!value) {
      return { valid: false, message: "Vui lòng chọn loại bữa ăn." };
    }

    if (!Object.prototype.hasOwnProperty.call(ALLOWED_MEAL_TYPES, value)) {
      return { valid: false, message: "Loại bữa ăn không hợp lệ." };
    }

    return { valid: true, value };
  }

  function validateAvoidIngredients() {
    const raw = avoidInput.value.trim();
    if (!raw) {
      return { valid: true, value: [] };
    }

    if (raw.length > 200) {
      return { valid: false, message: "Danh sách nguyên liệu không quá 200 ký tự." };
    }

    const parts = raw.split(",").map((item) => item.trim());
    if (parts.some((item) => item.length === 0)) {
      return {
        valid: false,
        message: "Không để trống nguyên liệu giữa các dấu phẩy.",
      };
    }

    if (parts.length > MAX_AVOID_ITEMS) {
      return {
        valid: false,
        message: `Chỉ nhập tối đa ${MAX_AVOID_ITEMS} nguyên liệu cần tránh.`,
      };
    }

    const invalidItem = parts.find(
      (item) => !INGREDIENT_PATTERN.test(item) || !HAS_LETTER_PATTERN.test(item),
    );
    if (invalidItem) {
      return {
        valid: false,
        message: "Tên nguyên liệu chỉ gồm chữ, số, khoảng trắng hoặc dấu gạch ngang.",
      };
    }

    return { valid: true, value: parts };
  }

  function clearStatus() {
    statusBox.classList.add("d-none");
    statusBox.innerHTML = "";
  }

  function showValidatedSummary(payload) {
    const mealLabel = ALLOWED_MEAL_TYPES[payload.meal_type];
    const avoidText = payload.avoid_ingredients.length > 0
      ? escapeHtml(payload.avoid_ingredients.join(", "))
      : "Không có";

    statusBox.innerHTML = `
      <strong>Đã nhận tiêu chí hợp lệ:</strong>
      Ngân sách tối đa <strong>${escapeHtml(formatMoney(payload.max_budget))}</strong> ·
      Bữa ăn: <strong>${escapeHtml(mealLabel)}</strong> ·
      Nguyên liệu tránh: <strong>${avoidText}</strong>.
    `;
    statusBox.classList.remove("d-none");
  }

  maxBudgetInput.addEventListener("input", () => {
    setFieldError(maxBudgetInput, maxBudgetError, "");
    clearStatus();
  });

  mealTypeSelect.addEventListener("change", () => {
    setFieldError(mealTypeSelect, mealTypeError, "");
    clearStatus();
  });

  avoidInput.addEventListener("input", () => {
    setFieldError(avoidInput, avoidError, "");
    clearStatus();
  });

  form.addEventListener("reset", () => {
    setFieldError(maxBudgetInput, maxBudgetError, "");
    setFieldError(mealTypeSelect, mealTypeError, "");
    setFieldError(avoidInput, avoidError, "");
    clearStatus();
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearStatus();

    const budgetResult = validateMaxBudget();
    const mealResult = validateMealType();
    const avoidResult = validateAvoidIngredients();

    setFieldError(maxBudgetInput, maxBudgetError, budgetResult.valid ? "" : budgetResult.message);
    setFieldError(mealTypeSelect, mealTypeError, mealResult.valid ? "" : mealResult.message);
    setFieldError(avoidInput, avoidError, avoidResult.valid ? "" : avoidResult.message);

    if (!budgetResult.valid) {
      maxBudgetInput.focus();
      return;
    }
    if (!mealResult.valid) {
      mealTypeSelect.focus();
      return;
    }
    if (!avoidResult.valid) {
      avoidInput.focus();
      return;
    }

    const payload = {
      max_budget: budgetResult.value,
      meal_type: mealResult.value,
      avoid_ingredients: avoidResult.value,
    };

    showValidatedSummary(payload);
    if (typeof showToast === "function") {
      showToast("Thông tin tìm kiếm hợp lệ.", "success");
    }
  });
})();
