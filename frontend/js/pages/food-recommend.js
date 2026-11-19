// Form gợi ý món ăn theo tiêu chí (Food Recommendation).
// Chỉ nạp và chạy trên trang có form #food-recommend-form.
// Giữ nguyên validation và cách xử lý dữ liệu hiện tại.

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
  const WEIGHT_TOLERANCE = 0.001;

  const CRITERIA_CONFIG = [
    {
      key: "price",
      label: "Giá",
      defaultWeight: 40,
      checkboxId: "food-criterion-price",
      inputId: "food-weight-price",
      errorId: "food-weight-price-error",
    },
    {
      key: "preference",
      label: "Phù hợp khẩu vị",
      defaultWeight: 35,
      checkboxId: "food-criterion-preference",
      inputId: "food-weight-preference",
      errorId: "food-weight-preference-error",
    },
    {
      key: "prep_time",
      label: "Thời gian chuẩn bị",
      defaultWeight: 25,
      checkboxId: "food-criterion-prep-time",
      inputId: "food-weight-prep-time",
      errorId: "food-weight-prep-time-error",
    },
  ];

  const form = document.getElementById("food-recommend-form");
  if (!form) return;

  const maxBudgetInput = document.getElementById("food-max-budget");
  const mealTypeSelect = document.getElementById("food-meal-type");
  const avoidInput = document.getElementById("food-avoid-ingredients");

  const maxBudgetError = document.getElementById("food-max-budget-error");
  const mealTypeError = document.getElementById("food-meal-type-error");
  const avoidError = document.getElementById("food-avoid-ingredients-error");
  const statusBox = document.getElementById("food-recommend-status");

  const weightTotalBadge = document.getElementById("food-weight-total-badge");
  const weightTotalValue = document.getElementById("food-weight-total-value");
  const weightWarningBox = document.getElementById("food-weight-warning");

  const criteriaItems = CRITERIA_CONFIG.map((cfg) => {
    const checkbox = document.getElementById(cfg.checkboxId);
    const input = document.getElementById(cfg.inputId);
    const error = document.getElementById(cfg.errorId);
    const row = form.querySelector(`[data-criterion-row="${cfg.key}"]`);
    return { ...cfg, checkbox, input, error, row };
  });

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
        message: "Không để trống nguyên liệu giữa các dấu phẩm.",
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

  function formatWeightPercent(value) {
    const rounded = Math.round(value * 100) / 100;
    return Number.isInteger(rounded) ? String(rounded) : String(rounded);
  }

  function validateSingleWeight(inputEl) {
    const raw = inputEl.value.trim();
    if (!raw) {
      return { valid: false, message: "Vui lòng nhập weight." };
    }

    const value = Number(raw);
    if (!Number.isFinite(value)) {
      return { valid: false, message: "Weight phải là số hợp lệ." };
    }

    if (value < 0) {
      return { valid: false, message: "Weight không được âm." };
    }

    if (value > 100) {
      return { valid: false, message: "Weight không vượt quá 100%." };
    }

    return { valid: true, value };
  }

  function setWeightWarning(message) {
    if (!weightWarningBox) return;
    if (message) {
      weightWarningBox.textContent = message;
      weightWarningBox.classList.remove("d-none");
    } else {
      weightWarningBox.textContent = "";
      weightWarningBox.classList.add("d-none");
    }
  }

  function validateCriteriaAndWeights() {
    let selectedCount = 0;
    let totalPercent = 0;
    let firstInvalidEl = null;
    let hasFieldError = false;
    const weights = {};
    const selectedLabels = [];

    criteriaItems.forEach((item) => {
      if (!item.checkbox || !item.input || !item.error) return;

      const isChecked = item.checkbox.checked;
      item.input.disabled = !isChecked;
      if (item.row) {
        item.row.classList.toggle("is-disabled", !isChecked);
      }

      if (!isChecked) {
        setFieldError(item.input, item.error, "");
        return;
      }

      selectedCount += 1;
      const result = validateSingleWeight(item.input);
      if (!result.valid) {
        hasFieldError = true;
        setFieldError(item.input, item.error, result.message);
        if (!firstInvalidEl) firstInvalidEl = item.input;
        return;
      }

      setFieldError(item.input, item.error, "");
      totalPercent += result.value;
      weights[item.key] = Number((result.value / 100).toFixed(4));
      selectedLabels.push(`${item.label} (${formatWeightPercent(result.value)}%)`);
    });

    const roundedTotal = Math.round(totalPercent * 100) / 100;
    if (weightTotalValue) {
      weightTotalValue.textContent = `${formatWeightPercent(roundedTotal)}%`;
    }

    const isTotalExact = Math.abs(roundedTotal - 100) <= WEIGHT_TOLERANCE;
    const isValid = selectedCount > 0 && !hasFieldError && isTotalExact;

    if (weightTotalBadge) {
      weightTotalBadge.classList.toggle("is-valid", isValid);
      weightTotalBadge.classList.toggle("is-invalid", !isValid);
    }

    if (selectedCount === 0) {
      setWeightWarning("Cảnh báo: Vui lòng chọn ít nhất 1 tiêu chí đánh giá.");
      if (!firstInvalidEl && criteriaItems[0]?.checkbox) {
        firstInvalidEl = criteriaItems[0].checkbox;
      }
    } else if (hasFieldError) {
      setWeightWarning("Cảnh báo: Có tiêu chí chứa weight âm hoặc không hợp lệ.");
    } else if (!isTotalExact) {
      setWeightWarning(
        `Cảnh báo: Tổng weight hiện tại là ${formatWeightPercent(roundedTotal)}%, cần bằng đúng 100% để hợp lệ.`,
      );
      if (!firstInvalidEl) {
        const firstChecked = criteriaItems.find((item) => item.checkbox?.checked);
        firstInvalidEl = firstChecked ? firstChecked.input : null;
      }
    } else {
      setWeightWarning("");
    }

    return {
      valid: isValid,
      firstInvalidEl,
      weights,
      selectedLabels,
    };
  }

  function clearStatus() {
    statusBox.classList.add("d-none");
    statusBox.innerHTML = "";
  }

  function showValidatedSummary(payload) {
    const mealLabel = ALLOWED_MEAL_TYPES[payload.meal_type];
    const avoidText = payload.excluded_ingredients.length > 0
      ? escapeHtml(payload.excluded_ingredients.join(", "))
      : "Không có";
    const criteriaText = payload.selected_criteria_labels.length > 0
      ? escapeHtml(payload.selected_criteria_labels.join(", "))
      : "Mặc định";

    statusBox.innerHTML = `
      <strong>Đã nhận tiêu chí hợp lệ:</strong>
      Ngân sách tối đa <strong>${escapeHtml(formatMoney(payload.max_budget))}</strong> ·
      Bữa ăn: <strong>${escapeHtml(mealLabel)}</strong> ·
      Nguyên liệu tránh: <strong>${avoidText}</strong> ·
      Trọng số: <strong>${criteriaText}</strong>.
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

  criteriaItems.forEach((item) => {
    if (item.checkbox) {
      item.checkbox.addEventListener("change", () => {
        clearStatus();
        validateCriteriaAndWeights();
      });
    }
    if (item.input) {
      item.input.addEventListener("input", () => {
        clearStatus();
        validateCriteriaAndWeights();
      });
    }
  });

  form.addEventListener("reset", () => {
    setFieldError(maxBudgetInput, maxBudgetError, "");
    setFieldError(mealTypeSelect, mealTypeError, "");
    setFieldError(avoidInput, avoidError, "");
    clearStatus();

    setTimeout(() => {
      criteriaItems.forEach((item) => {
        if (item.checkbox) item.checkbox.checked = true;
        if (item.input) {
          item.input.disabled = false;
          item.input.value = String(item.defaultWeight);
        }
        if (item.error) {
          setFieldError(item.input, item.error, "");
        }
      });
      validateCriteriaAndWeights();
    }, 0);
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearStatus();

    const budgetResult = validateMaxBudget();
    const mealResult = validateMealType();
    const avoidResult = validateAvoidIngredients();
    const criteriaResult = validateCriteriaAndWeights();

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
    if (!criteriaResult.valid) {
      if (criteriaResult.firstInvalidEl) {
        criteriaResult.firstInvalidEl.focus();
      }
      return;
    }

    const payload = {
      max_budget: budgetResult.value,
      meal_type: mealResult.value,
      excluded_ingredients: avoidResult.value,
      weights: criteriaResult.weights,
      selected_criteria_labels: criteriaResult.selectedLabels,
    };

    showValidatedSummary(payload);
    if (typeof showToast === "function") {
      showToast("Thông tin tìm kiếm hợp lệ.", "success");
    }
  });

  validateCriteriaAndWeights();
})();
