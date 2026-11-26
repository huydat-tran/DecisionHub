// ==========================================================
// Module: Food Recommendation (Đề xuất món ăn thông minh)
// Quản lý trọn vẹn vòng đời giao diện Form & Kết quả:
//   Initial -> Loading -> Success | Empty | Error (kèm Retry & Chống gửi trùng)
// ==========================================================

(function (global) {
  const ALLOWED_MEAL_TYPES = {
    breakfast: "Bữa sáng",
    lunch: "Bữa trưa",
    dinner: "Bữa tối",
    snack: "Bữa phụ / Ăn vặt",
  };

  const MAX_BUDGET_LIMIT = 100000000;
  const MAX_PREP_TIME_LIMIT = 1440;
  const MAX_LIST_ITEMS = 10;
  const MIN_LIMIT = 1;
  const MAX_LIMIT = 20;
  const DEFAULT_LIMIT = 5;
  const INGREDIENT_PATTERN = /^[\p{L}\p{N}\s-]+$/u;
  const HAS_LETTER_PATTERN = /\p{L}/u;

  const form = document.getElementById("food-recommend-form");
  if (!form) return;

  const maxBudgetInput = document.getElementById("food-max-budget");
  const mealTypeSelect = document.getElementById("food-meal-type");
  const maxPrepTimeInput = document.getElementById("food-max-prep-time");
  const avoidInput = document.getElementById("food-avoid-ingredients");
  const preferredTagsInput = document.getElementById("food-preferred-tags");
  const preferredTagChips = document.getElementById("food-preferred-tag-chips");
  const limitInput = document.getElementById("food-limit");

  const maxBudgetError = document.getElementById("food-max-budget-error");
  const mealTypeError = document.getElementById("food-meal-type-error");
  const maxPrepTimeError = document.getElementById("food-max-prep-time-error");
  const avoidError = document.getElementById("food-avoid-ingredients-error");
  const preferredTagsError = document.getElementById("food-preferred-tags-error");
  const limitError = document.getElementById("food-limit-error");
  const statusBox = document.getElementById("food-recommend-status");

  const submitBtn =
    document.getElementById("btn-food-recommend-submit") ||
    form.querySelector('button[type="submit"]');
  const resetBtn = document.getElementById("btn-food-recommend-reset");

  // Các container trạng thái khu vực kết quả (đảm bảo loại trừ lẫn nhau, không chồng giao diện)
  const initialStateEl = document.getElementById("results-initial-state");
  const loadingStateEl = document.getElementById("results-loading-state");
  const emptyStateEl = document.getElementById("results-empty-state");
  const emptyTitleEl = document.getElementById("results-empty-title");
  const emptyDescEl = document.getElementById("results-empty-desc");
  const errorStateEl = document.getElementById("results-error-state");
  const errorTitleEl = document.getElementById("results-error-title");
  const errorDescEl = document.getElementById("results-error-desc");
  const successContentEl = document.getElementById("results-success-content");
  const excludedSectionEl = document.getElementById("results-excluded-section");

  const btnFocusForm = document.getElementById("btn-results-focus-form");
  const btnAdjustCriteria = document.getElementById("btn-results-adjust-criteria");
  const btnRetryEmpty = document.getElementById("btn-results-retry-empty");
  const btnRetryError = document.getElementById("btn-results-retry-error");
  const btnErrorAdjust = document.getElementById("btn-results-error-adjust");

  const rankingListEl = document.getElementById("results-ranking-list");
  const explanationBodyEl = document.getElementById("results-explanation-body");
  const resultsTotalEl = document.getElementById("results-total");
  const resultsTopNameEl = document.getElementById("results-top-name");
  const resultsTopScoreEl = document.getElementById("results-top-score");

  const API_FIELD_ORDER = [
    "budget_max",
    "meal_type",
    "max_prep_time",
    "excluded_ingredients",
    "preferred_tags",
    "limit",
  ];

  const API_FIELD_MAP = {
    budget_max: { input: maxBudgetInput, error: maxBudgetError },
    meal_type: { input: mealTypeSelect, error: mealTypeError },
    max_prep_time: { input: maxPrepTimeInput, error: maxPrepTimeError },
    excluded_ingredients: { input: avoidInput, error: avoidError },
    preferred_tags: { input: preferredTagsInput, error: preferredTagsError },
    limit: { input: limitInput, error: limitError },
  };

  // Trạng thái điều phối request (chống gửi trùng & race condition)
  const uiState = {
    view: "initial", // "initial" | "loading" | "success" | "empty" | "error"
    isSubmitting: false,
    requestSeq: 0,
    lastPayload: null,
    lastSaveHistory: true,
    hasPreviousSuccess: false,
  };

  // ---------- Helpers an toàn ----------
  function safeHtml(val) {
    if (typeof escapeHtml === "function") return escapeHtml(val);
    if (val === null || val === undefined) return "";
    return String(val)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function moneyStr(val) {
    if (typeof formatMoney === "function") return formatMoney(val);
    return Number(val || 0).toLocaleString("vi-VN") + " ₫";
  }

  function getMealLabel(mealType) {
    return mealType ? ALLOWED_MEAL_TYPES[mealType] || mealType : "tất cả bữa ăn";
  }

  function focusRecommendForm() {
    if (form && typeof form.scrollIntoView === "function") {
      form.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    if (maxBudgetInput && typeof maxBudgetInput.focus === "function") {
      maxBudgetInput.focus();
    }
  }

  // ---------- Quản lý lỗi trên từng trường của Form ----------
  function setFieldError(inputEl, errorEl, message) {
    if (errorEl) errorEl.textContent = message || "";
    if (inputEl) {
      if (message) {
        inputEl.classList.add("food-input-invalid");
        inputEl.setAttribute("aria-invalid", "true");
      } else {
        inputEl.classList.remove("food-input-invalid");
        inputEl.removeAttribute("aria-invalid");
      }
    }
  }

  function clearAllFieldErrors() {
    API_FIELD_ORDER.forEach((key) => {
      const entry = API_FIELD_MAP[key];
      if (entry) {
        setFieldError(entry.input, entry.error, "");
      }
    });
  }

  function normalizeApiFieldName(rawField) {
    const segments = Array.isArray(rawField)
      ? rawField.map((part) => String(part).trim()).filter(Boolean)
      : String(rawField || "")
          .split(".")
          .map((part) => part.trim())
          .filter(Boolean);

    if (
      segments.length > 0 &&
      ["body", "query", "path", "header", "cookie"].includes(segments[0])
    ) {
      segments.shift();
    }

    if (segments.length === 0) return "";
    if (Object.prototype.hasOwnProperty.call(API_FIELD_MAP, segments[0])) {
      return segments[0];
    }
    return segments.join(".");
  }

  function cleanApiErrorMessage(rawMessage) {
    const msg = String(rawMessage || "")
      .trim()
      .replace(/^(?:Value error,\s*)+/i, "");
    // Chặn các chuỗi lỗi kỹ thuật thô (stack trace / SQL / exception class)
    if (/traceback|sqlalchemy|pymysql|operationalerror|syntaxerror/i.test(msg)) {
      return "Hệ thống máy chủ đang gặp sự cố tạm thời. Vui lòng thử lại sau.";
    }
    return msg;
  }

  function pushUniqueMessage(list, message) {
    if (message && !list.includes(message)) {
      list.push(message);
    }
  }

  function extractApiErrors(apiErr) {
    const data = apiErr && apiErr.data ? apiErr.data : null;
    const fieldErrors = {};
    const generalErrors = [];

    const rawItems =
      data && Array.isArray(data.errors)
        ? data.errors
        : data && Array.isArray(data.detail)
          ? data.detail
          : [];

    rawItems.forEach((item) => {
      if (!item || typeof item !== "object") return;
      const fieldKey = normalizeApiFieldName(item.field ?? item.loc);
      const msg = cleanApiErrorMessage(item.message ?? item.msg);
      if (!msg) return;

      if (fieldKey && Object.prototype.hasOwnProperty.call(API_FIELD_MAP, fieldKey)) {
        if (!fieldErrors[fieldKey]) {
          fieldErrors[fieldKey] = [];
        }
        pushUniqueMessage(fieldErrors[fieldKey], msg);
      } else {
        pushUniqueMessage(generalErrors, msg);
      }
    });

    const summaryMessage = cleanApiErrorMessage(
      (data && typeof data.message === "string" && data.message) || "",
    );

    if (rawItems.length === 0) {
      const fallbackMessage = cleanApiErrorMessage(
        (data && typeof data.message === "string" && data.message) ||
          (data && typeof data.detail === "string" && data.detail) ||
          (apiErr && apiErr.message) ||
          "",
      );
      pushUniqueMessage(generalErrors, fallbackMessage);
    }

    return { fieldErrors, generalErrors, summaryMessage };
  }

  // Phân loại lỗi API sang thông báo thân thiện cho người dùng
  function classifyRecommendError(apiErr) {
    const status = apiErr && typeof apiErr.status === "number" ? apiErr.status : -1;

    if (apiErr && apiErr.isTimeout) {
      return {
        title: "Yêu cầu quá thời gian phản hồi",
        message:
          "Máy chủ phản hồi chậm hơn dự kiến. Vui lòng kiểm tra kết nối mạng và nhấn Thử lại.",
        canRetry: true,
      };
    }

    if (status === 0) {
      return {
        title: "Không thể kết nối tới máy chủ",
        message:
          "Không kết nối được với hệ thống DecisionHub. Vui lòng kiểm tra mạng hoặc đảm bảo máy chủ Backend đang hoạt động rồi thử lại.",
        canRetry: true,
      };
    }

    if (status === 401) {
      return {
        title: "Phiên đăng nhập đã hết hạn",
        message:
          "Phiên xác thực của bạn không còn hợp lệ. Bạn có thể nhấn Thử lại để tiếp tục tìm món ăn hoặc đăng nhập lại để lưu lịch sử quyết định.",
        canRetry: true,
        isAuthError: true,
      };
    }

    if (status === 403) {
      return {
        title: "Không có quyền truy cập",
        message: "Tài khoản hiện tại không có quyền thực hiện thao tác này.",
        canRetry: false,
      };
    }

    if (status === 422 || status === 400) {
      const { summaryMessage, generalErrors } = extractApiErrors(apiErr);
      return {
        title: "Dữ liệu tìm kiếm chưa hợp lệ",
        message:
          generalErrors[0] ||
          summaryMessage ||
          "Một số tiêu chí gửi lên chưa hợp lệ. Vui lòng kiểm tra lại các ô được đánh dấu trên biểu mẫu.",
        canRetry: false,
        isValidation: true,
      };
    }

    if (status >= 500) {
      return {
        title: "Máy chủ đang gặp sự cố tạm thời",
        message:
          "Hệ thống xử lý gợi ý món ăn đang bận hoặc gặp lỗi nội bộ. Vui lòng nhấn Thử lại sau giây lát.",
        canRetry: true,
      };
    }

    return {
      title: "Không thể hoàn tất gợi ý món ăn",
      message:
        cleanApiErrorMessage(apiErr && apiErr.message) ||
        "Đã xảy ra sự cố không mong muốn khi tìm món ăn phù hợp. Vui lòng thử lại.",
      canRetry: true,
    };
  }

  function applyApiValidationErrors(apiErr) {
    clearAllFieldErrors();

    const { fieldErrors, generalErrors, summaryMessage } = extractApiErrors(apiErr);
    let firstInvalidInput = null;

    API_FIELD_ORDER.forEach((key) => {
      const messages = fieldErrors[key];
      const entry = API_FIELD_MAP[key];
      if (!entry || !messages || messages.length === 0) return;

      setFieldError(entry.input, entry.error, messages.join(" "));
      if (!firstInvalidInput && entry.input) {
        firstInvalidInput = entry.input;
      }
    });

    if (firstInvalidInput && typeof firstInvalidInput.focus === "function") {
      firstInvalidInput.focus();
    }

    const displayMessage =
      generalErrors.length > 0
        ? generalErrors.map((msg) => safeHtml(msg)).join("<br>")
        : safeHtml(
            summaryMessage ||
              "Dữ liệu gửi lên không hợp lệ. Vui lòng kiểm tra và điều chỉnh các trường được đánh dấu.",
          );

    showStatus(`<strong>Dữ liệu chưa hợp lệ:</strong> ${displayMessage}`, "error");
  }

  // ---------- Validate dữ liệu Form phía Client ----------
  function validateMaxBudget() {
    if (!maxBudgetInput) return { valid: false, empty: true, message: "Vui lòng nhập ngân sách tối đa." };
    const raw = maxBudgetInput.value.trim();
    if (!raw) {
      return {
        valid: false,
        empty: true,
        message: "Vui lòng nhập ngân sách tối đa để bắt đầu tìm món ăn.",
      };
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
    if (!mealTypeSelect) return { valid: true, value: null };
    const value = mealTypeSelect.value.trim();
    if (!value) {
      return { valid: true, value: null };
    }

    if (!Object.prototype.hasOwnProperty.call(ALLOWED_MEAL_TYPES, value)) {
      return { valid: false, message: "Loại bữa ăn không hợp lệ." };
    }

    return { valid: true, value };
  }

  function validateMaxPrepTime() {
    if (!maxPrepTimeInput) return { valid: true, value: null };
    const raw = maxPrepTimeInput.value.trim();
    if (!raw) {
      return { valid: true, value: null };
    }

    const value = Number(raw);
    if (!Number.isFinite(value) || value <= 0) {
      return { valid: false, message: "Thời gian chuẩn bị tối đa phải lớn hơn 0." };
    }

    if (!Number.isInteger(value)) {
      return { valid: false, message: "Thời gian chuẩn bị phải là số nguyên (phút)." };
    }

    if (value > MAX_PREP_TIME_LIMIT) {
      return {
        valid: false,
        message: `Thời gian chuẩn bị không vượt quá ${MAX_PREP_TIME_LIMIT} phút.`,
      };
    }

    return { valid: true, value };
  }

  function parseCommaList(raw) {
    return String(raw || "")
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);
  }

  function validateCommaList(inputEl, { maxItems, itemNoun }) {
    if (!inputEl) return { valid: true, value: [] };
    const raw = inputEl.value.trim();
    if (!raw) {
      return { valid: true, value: [] };
    }

    if (raw.length > 200) {
      return { valid: false, message: `Danh sách ${itemNoun} không quá 200 ký tự.` };
    }

    const parts = parseCommaList(raw);
    if (parts.length > maxItems) {
      return {
        valid: false,
        message: `Chỉ nhập tối đa ${maxItems} ${itemNoun}.`,
      };
    }

    const invalidItem = parts.find(
      (item) => !INGREDIENT_PATTERN.test(item) || !HAS_LETTER_PATTERN.test(item),
    );
    if (invalidItem) {
      return {
        valid: false,
        message: `Tên ${itemNoun} chỉ gồm chữ, số, khoảng trắng hoặc dấu gạch ngang.`,
      };
    }

    const uniqueParts = Array.from(new Set(parts.map((p) => p.toLowerCase())));
    return { valid: true, value: uniqueParts };
  }

  function validateLimit() {
    if (!limitInput) return { valid: true, value: DEFAULT_LIMIT };
    const raw = limitInput.value.trim();
    if (!raw) {
      return { valid: true, value: DEFAULT_LIMIT };
    }

    const value = Number(raw);
    if (!Number.isFinite(value) || !Number.isInteger(value)) {
      return { valid: false, message: "Số món gợi ý phải là số nguyên." };
    }

    if (value < MIN_LIMIT || value > MAX_LIMIT) {
      return {
        valid: false,
        message: `Số món gợi ý phải từ ${MIN_LIMIT} đến ${MAX_LIMIT}.`,
      };
    }

    return { valid: true, value };
  }

  function validateAllFormFields() {
    const budgetResult = validateMaxBudget();
    const mealResult = validateMealType();
    const prepTimeResult = validateMaxPrepTime();
    const avoidResult = validateCommaList(avoidInput, {
      maxItems: MAX_LIST_ITEMS,
      itemNoun: "nguyên liệu cần tránh",
    });
    const tagsResult = validateCommaList(preferredTagsInput, {
      maxItems: MAX_LIST_ITEMS,
      itemNoun: "khẩu vị/nhãn ưu tiên",
    });
    const limitResult = validateLimit();

    setFieldError(maxBudgetInput, maxBudgetError, budgetResult.valid ? "" : budgetResult.message);
    setFieldError(mealTypeSelect, mealTypeError, mealResult.valid ? "" : mealResult.message);
    setFieldError(maxPrepTimeInput, maxPrepTimeError, prepTimeResult.valid ? "" : prepTimeResult.message);
    setFieldError(avoidInput, avoidError, avoidResult.valid ? "" : avoidResult.message);
    setFieldError(preferredTagsInput, preferredTagsError, tagsResult.valid ? "" : tagsResult.message);
    setFieldError(limitInput, limitError, limitResult.valid ? "" : limitResult.message);

    const orderedChecks = [
      [budgetResult, maxBudgetInput],
      [mealResult, mealTypeSelect],
      [prepTimeResult, maxPrepTimeInput],
      [avoidResult, avoidInput],
      [tagsResult, preferredTagsInput],
      [limitResult, limitInput],
    ];
    const firstFailure = orderedChecks.find(([result]) => !result.valid);

    if (firstFailure) {
      if (firstFailure[1] && typeof firstFailure[1].focus === "function") {
        firstFailure[1].focus();
      }
      if (budgetResult.empty) {
        showStatus(
          "<strong>Chưa nhập đủ thông tin:</strong> Vui lòng nhập <strong>Ngân sách tối đa (VNĐ)</strong> để hệ thống tìm món ăn phù hợp cho bạn.",
          "warning",
        );
      } else {
        showStatus(
          `<strong>Thông tin chưa hợp lệ:</strong> ${safeHtml(firstFailure[0].message)} Vui lòng điều chỉnh lại điều kiện trên biểu mẫu.`,
          "error",
        );
      }
      return { valid: false, isEmptyForm: Boolean(budgetResult.empty) };
    }

    return {
      valid: true,
      payload: {
        budget_max: budgetResult.value,
        meal_type: mealResult.value,
        max_prep_time: prepTimeResult.value,
        excluded_ingredients: avoidResult.value,
        preferred_tags: tagsResult.value,
        limit: limitResult.value,
      },
    };
  }

  function syncTagChips() {
    if (!preferredTagChips || !preferredTagsInput) return;
    const activeTags = new Set(
      parseCommaList(preferredTagsInput.value).map((item) => item.toLowerCase()),
    );
    preferredTagChips.querySelectorAll(".dh-chip[data-tag]").forEach((btn) => {
      const tag = (btn.dataset.tag || "").trim().toLowerCase();
      const isActive = activeTags.has(tag);
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  }

  // ---------- Quản lý thanh trạng thái Form & Chuyển đổi View Kết quả ----------
  function clearStatus() {
    if (statusBox) {
      statusBox.classList.add("d-none");
      statusBox.className = "food-form-status d-none mt-3";
      statusBox.innerHTML = "";
    }
  }

  function showStatus(html, type = "info") {
    if (!statusBox) return;
    const alertClass =
      type === "error"
        ? "danger"
        : type === "warning"
          ? "warning"
          : type === "success"
            ? "success"
            : "info";
    statusBox.className = `food-form-status mt-3 alert alert-${alertClass} py-2 px-3`;
    statusBox.innerHTML = html;
    statusBox.classList.remove("d-none");
  }

  // Khoá/mở các nút thao tác trên Form trong lúc chờ API (giữ nguyên dữ liệu người dùng đã nhập)
  function setFormLoading(isLoading) {
    form.setAttribute("aria-busy", isLoading ? "true" : "false");

    if (submitBtn) {
      submitBtn.disabled = isLoading;
      submitBtn.innerHTML = isLoading
        ? `<span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span> Đang tìm kiếm món ăn phù hợp...`
        : "Gợi ý món ăn";
    }

    if (resetBtn) {
      resetBtn.disabled = isLoading;
    }

    if (preferredTagChips) {
      preferredTagChips.querySelectorAll("button.dh-chip").forEach((chip) => {
        chip.disabled = isLoading;
      });
    }
  }

  // Đảm bảo tại mỗi thời điểm chỉ có ĐÚNG 1 trạng thái khu vực kết quả hiển thị (không chồng chéo)
  function switchResultsView(mode, options = {}) {
    uiState.view = mode;
    const showExcluded = Boolean(options.showExcluded);

    if (initialStateEl) initialStateEl.classList.toggle("d-none", mode !== "initial");
    if (loadingStateEl) loadingStateEl.classList.toggle("d-none", mode !== "loading");
    if (emptyStateEl) emptyStateEl.classList.toggle("d-none", mode !== "empty");
    if (errorStateEl) errorStateEl.classList.toggle("d-none", mode !== "error");
    if (successContentEl) successContentEl.classList.toggle("d-none", mode !== "success");
    if (excludedSectionEl) {
      excludedSectionEl.classList.toggle(
        "d-none",
        !(mode === "success" || (mode === "empty" && showExcluded)),
      );
    }

    // Khi bắt đầu loading, xóa nội dung kết quả cũ để tránh hiểu nhầm dữ liệu cũ là kết quả mới
    if (mode === "loading") {
      if (rankingListEl) rankingListEl.innerHTML = "";
      if (explanationBodyEl) explanationBodyEl.innerHTML = "";
      if (resultsTotalEl) resultsTotalEl.textContent = "–";
      if (resultsTopNameEl) resultsTopNameEl.textContent = "–";
      if (resultsTopScoreEl) resultsTopScoreEl.textContent = "";
    }
  }

  // ---------- Định dạng kết quả từ API Backend ----------
  function resolveFoodImage(foodName, imageUrl) {
    if (imageUrl && typeof imageUrl === "string" && imageUrl.trim()) {
      return imageUrl;
    }
    const lower = (foodName || "").toLowerCase();
    if (lower.includes("phở")) return "../assets/images/foods/phobo.jpg";
    if (lower.includes("bánh mì")) return "../assets/images/foods/banhmi.jpg";
    if (lower.includes("bún chả")) return "../assets/images/foods/buncha.jpg";
    if (lower.includes("cơm")) return "../assets/images/foods/comtam.jpg";
    if (lower.includes("lẩu")) return "../assets/images/foods/laumini.jpg";
    if (lower.includes("mì") || lower.includes("bún") || lower.includes("quảng")) {
      return "../assets/images/foods/buncha.jpg";
    }
    if (lower.includes("cuốn") || lower.includes("gỏi")) {
      return "../assets/images/foods/banhmi.jpg";
    }
    return "../assets/images/foods/phobo.jpg";
  }

  function formatApiResults(items, criteriaList, weightsMap) {
    const criteria = criteriaList || [
      { key: "price", label: "Giá / Ngân sách", weight: 0.4 },
      { key: "preference", label: "Mức phù hợp nhu cầu/khẩu vị", weight: 0.35 },
      { key: "prep_time", label: "Thời gian chuẩn bị", weight: 0.25 },
    ];

    return items.map((item, index) => {
      const rank = item.rank || index + 1;
      const isTop = rank === 1;
      const totalScore = Number(item.total_score ?? item.score ?? 0);

      const criteriaScores = item.criteria_scores || {};
      const rawDetails = item.criteria_details || {};
      const details = {};

      criteria.forEach((crit) => {
        const key = crit.key;
        const detailObj = rawDetails[key] || {};
        const scoreVal =
          detailObj.normalized_score !== undefined
            ? detailObj.normalized_score
            : criteriaScores[key] !== undefined
              ? criteriaScores[key]
              : null;
        const weightVal =
          detailObj.weight !== undefined
            ? detailObj.weight
            : weightsMap && weightsMap[key] !== undefined
              ? weightsMap[key]
              : crit.weight;
        const contribVal =
          detailObj.contribution !== undefined
            ? detailObj.contribution
            : scoreVal !== null
              ? Math.round(weightVal * scoreVal * 100) / 100
              : 0;

        details[key] = {
          label: crit.label,
          normalized_score: scoreVal !== null ? Number(scoreVal) : null,
          weight: Number(weightVal),
          contribution: Number(contribVal),
        };
      });

      const reasons = Array.isArray(item.reasons) ? [...item.reasons] : [];
      if (reasons.length === 0) {
        if (item.price) {
          reasons.push(`Mức giá ${moneyStr(item.price)} phù hợp với ngân sách của bạn`);
        }
        if (item.prep_time) {
          reasons.push(`Thời gian chuẩn bị ${item.prep_time} phút nhanh chóng`);
        }
      }

      const pros = [...reasons];
      const cons = [];
      const pScore = criteriaScores.price ?? 70;
      if (pScore < 60 && item.price) {
        cons.push(`Mức giá ${moneyStr(item.price)} tiệm cận mức ngân sách tối đa`);
      }
      if (item.prep_time && item.prep_time > 20) {
        cons.push(`Thời gian chuẩn bị (${item.prep_time} phút) cần đợi lâu hơn`);
      }
      if (cons.length === 0) {
        cons.push(
          isTop
            ? "Là lựa chọn hài hòa nhất trong tầm giá"
            : "Điểm tổng hợp thấp hơn phương án đứng đầu",
        );
      }

      return {
        id: item.food_id || item.id || index + 1,
        name: item.name,
        price: item.price,
        prep_time: item.prep_time,
        meal_type: item.meal_type || "",
        tags: item.tags || [],
        image: resolveFoodImage(item.name, item.image_url),
        score: totalScore,
        total_score: totalScore,
        ranking: rank,
        criteria_scores: {
          price: Math.round(criteriaScores.price ?? 0),
          preference: Math.round(criteriaScores.preference ?? 0),
          prep_time: Math.round(criteriaScores.prep_time ?? 0),
        },
        criteria: {
          price: Math.round(criteriaScores.price ?? 0),
          preference: Math.round(criteriaScores.preference ?? 0),
          prep_time: Math.round(criteriaScores.prep_time ?? 0),
        },
        criteria_details: details,
        reasons,
        explanation: isTop
          ? `Đứng đầu với ${totalScore.toFixed(1)}/100 điểm WSM. Món ăn cân bằng tối ưu giữa ngân sách, loại bữa ăn và thời gian chuẩn bị.`
          : `Xếp hạng ${rank} với ${totalScore.toFixed(1)}/100 điểm WSM. ${reasons[0] || ""}`,
        advantages: pros.slice(0, 3),
        disadvantages: cons.slice(0, 2),
      };
    });
  }

  // ---------- HÀM THỰC THI GỢI Ý MÓN ĂN CHÍNH ----------
  async function executeRecommendation(payload, options = { saveHistory: true }) {
    // Chặn gửi request trùng ngoài ý muốn khi người dùng bấm liên tục
    if (uiState.isSubmitting) {
      return;
    }

    const shouldSaveHistory = options && options.saveHistory !== false;
    const reqOptions = { authMode: shouldSaveHistory ? "optional" : "none" };
    const reqSeq = ++uiState.requestSeq;

    uiState.isSubmitting = true;
    uiState.lastPayload = { ...payload };
    uiState.lastSaveHistory = shouldSaveHistory;

    clearAllFieldErrors();
    setFormLoading(true);
    switchResultsView("loading");
    showStatus(
      `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Đang tìm kiếm món ăn phù hợp...`,
      "info",
    );

    const criteriaList = window.FOOD_CRITERIA || [
      { key: "price", label: "Giá", weight: 0.4 },
      { key: "preference", label: "Mức phù hợp nhu cầu/khẩu vị", weight: 0.35 },
      { key: "prep_time", label: "Thời gian chuẩn bị", weight: 0.25 },
    ];

    try {
      if (typeof api === "undefined" || typeof api.post !== "function") {
        throw new Error("Không tìm thấy module kết nối API.");
      }

      const res = await api.post("/decisions/food/recommend", payload, reqOptions);

      // Chống race condition nếu có phiên request mới hơn
      if (reqSeq !== uiState.requestSeq) return;

      const data = res && res.data ? res.data : res;
      const rawItems = data && Array.isArray(data.items) ? data.items : [];
      const excludedItems = data && Array.isArray(data.excluded_items) ? data.excluded_items : [];
      const backendMessage = (data && data.message) || "";
      const finalResults = formatApiResults(rawItems, criteriaList, data && data.scoring ? data.scoring.weights : null);
      const mealText = getMealLabel(payload.meal_type);

      // Trường hợp 1: Thành công nhưng KHÔNG có món ăn phù hợp (Empty State)
      if (finalResults.length === 0) {
        const hasExcluded = excludedItems.length > 0;
        if (emptyTitleEl) {
          emptyTitleEl.textContent = "Không tìm thấy món ăn phù hợp với tiêu chí hiện tại.";
        }
        if (emptyDescEl) {
          emptyDescEl.textContent = hasExcluded
            ? `Tất cả ${excludedItems.length} món ăn đều không đạt điều kiện lọc bắt buộc (ngân sách ≤ ${moneyStr(payload.budget_max)}, ${mealText}). Bạn có thể thử thay đổi ngân sách, khẩu vị hoặc bỏ bớt điều kiện lọc.`
            : "Bạn có thể thử thay đổi ngân sách, khẩu vị hoặc bỏ bớt điều kiện lọc.";
        }

        if (hasExcluded && typeof DHResults !== "undefined" && typeof DHResults.renderExcludedCandidates === "function") {
          DHResults.renderExcludedCandidates(excludedItems);
        }

        switchResultsView("empty", { showExcluded: hasExcluded });

        showStatus(
          `<strong>Không tìm thấy món ăn phù hợp:</strong> Chưa có phương án nào thỏa mãn ngân sách <strong>${safeHtml(moneyStr(payload.budget_max))}</strong> (${safeHtml(mealText)}). Hãy thử tăng ngân sách hoặc nới bớt điều kiện lọc.`,
          "warning",
        );

        if (typeof showToast === "function") {
          showToast("Không tìm thấy món ăn phù hợp với tiêu chí hiện tại.", "error");
        }
        return;
      }

      // Trường hợp 2: Thành công và CÓ dữ liệu gợi ý (Success State)
      uiState.hasPreviousSuccess = true;
      switchResultsView("success");

      if (typeof DHResults !== "undefined" && typeof DHResults.initResultsPage === "function") {
        DHResults.initResultsPage({
          results: finalResults,
          criteria: criteriaList,
          excluded: excludedItems,
          message: backendMessage,
        });
      }

      const topOption = finalResults[0];
      if (resultsTotalEl) resultsTotalEl.textContent = String(finalResults.length);
      if (resultsTopNameEl) resultsTopNameEl.textContent = topOption.name;
      if (resultsTopScoreEl) {
        resultsTopScoreEl.textContent = `${Number(topOption.score).toFixed(1)}/100 điểm (WSM)`;
      }

      const excludedNotice =
        excludedItems.length > 0
          ? ` (đã loại <strong>${excludedItems.length}</strong> món không thỏa điều kiện bắt buộc)`
          : "";

      showStatus(
        `✓ Đã tìm thấy <strong>${finalResults.length}</strong> món ăn phù hợp nhất${excludedNotice}. Đề xuất số 1: <strong>${safeHtml(topOption.name)}</strong> (${Number(topOption.score).toFixed(1)}/100 điểm WSM).`,
        "success",
      );

      if (typeof showToast === "function") {
        showToast(`Đã đề xuất ${finalResults.length} món ăn phù hợp!`, "success");
      }

      if (window.matchMedia && window.matchMedia("(max-width: 991.98px)").matches) {
        const summarySection = document.getElementById("results-summary-section");
        if (summarySection && typeof summarySection.scrollIntoView === "function") {
          summarySection.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    } catch (apiErr) {
      if (reqSeq !== uiState.requestSeq) return;

      const classified = classifyRecommendError(apiErr);

      // Lỗi validation 422 / 400 từ Backend: gắn lỗi vào từng ô input trên Form
      if (classified.isValidation) {
        applyApiValidationErrors(apiErr);
        switchResultsView("error");
        if (errorTitleEl) errorTitleEl.textContent = classified.title;
        if (errorDescEl) errorDescEl.textContent = classified.message;
        return;
      }

      // Các lỗi kết nối, timeout, 401, 403, 500+: hiển thị Error State kèm nút Thử lại
      if (errorTitleEl) errorTitleEl.textContent = classified.title;
      if (errorDescEl) errorDescEl.textContent = classified.message;
      if (btnRetryError) {
        btnRetryError.classList.toggle("d-none", !classified.canRetry);
      }
      switchResultsView("error");

      const retryActionHtml = classified.canRetry
        ? `<div class="food-status-actions">
             <button type="button" class="dh-btn dh-btn-sm dh-btn-outline" data-action="status-retry">↻ Thử lại</button>
             ${
               classified.isAuthError
                 ? `<a href="signup.html" class="dh-btn dh-btn-sm dh-btn-primary" style="text-decoration:none;">Đăng nhập lại</a>`
                 : ""
             }
           </div>`
        : "";

      showStatus(
        `<strong>${safeHtml(classified.title)}:</strong> ${safeHtml(classified.message)}${retryActionHtml}`,
        "error",
      );

      if (typeof showToast === "function") {
        showToast(classified.title, "error");
      }
    } finally {
      if (reqSeq === uiState.requestSeq) {
        uiState.isSubmitting = false;
        setFormLoading(false);
      }
    }
  }

  function retryLastRequest() {
    if (uiState.isSubmitting) return;

    if (uiState.lastPayload) {
      executeRecommendation(uiState.lastPayload, { saveHistory: uiState.lastSaveHistory });
      return;
    }

    const check = validateAllFormFields();
    if (check.valid) {
      executeRecommendation(check.payload, { saveHistory: true });
    }
  }

  // ---------- GẮN SỰ KIỆN FORM & NÚT HÀNH ĐỘNG ----------
  if (maxBudgetInput) {
    maxBudgetInput.addEventListener("input", () => {
      setFieldError(maxBudgetInput, maxBudgetError, "");
      if (!uiState.isSubmitting) clearStatus();
    });
  }

  if (mealTypeSelect) {
    mealTypeSelect.addEventListener("change", () => {
      setFieldError(mealTypeSelect, mealTypeError, "");
      if (!uiState.isSubmitting) clearStatus();
    });
  }

  if (maxPrepTimeInput) {
    maxPrepTimeInput.addEventListener("input", () => {
      setFieldError(maxPrepTimeInput, maxPrepTimeError, "");
      if (!uiState.isSubmitting) clearStatus();
    });
  }

  if (avoidInput) {
    avoidInput.addEventListener("input", () => {
      setFieldError(avoidInput, avoidError, "");
      if (!uiState.isSubmitting) clearStatus();
    });
  }

  if (preferredTagsInput) {
    preferredTagsInput.addEventListener("input", () => {
      setFieldError(preferredTagsInput, preferredTagsError, "");
      if (!uiState.isSubmitting) clearStatus();
      syncTagChips();
    });
  }

  if (preferredTagChips && preferredTagsInput) {
    preferredTagChips.addEventListener("click", (event) => {
      if (uiState.isSubmitting) return;
      const btn = event.target.closest(".dh-chip[data-tag]");
      if (!btn || btn.disabled) return;
      const clickedTag = (btn.dataset.tag || "").trim();
      if (!clickedTag) return;

      const currentTags = parseCommaList(preferredTagsInput.value);
      const clickedLower = clickedTag.toLowerCase();
      const exists = currentTags.some((item) => item.toLowerCase() === clickedLower);
      const nextTags = exists
        ? currentTags.filter((item) => item.toLowerCase() !== clickedLower)
        : [...currentTags, clickedTag];

      preferredTagsInput.value = nextTags.join(", ");
      setFieldError(preferredTagsInput, preferredTagsError, "");
      clearStatus();
      syncTagChips();
    });
  }

  if (limitInput) {
    limitInput.addEventListener("input", () => {
      setFieldError(limitInput, limitError, "");
      if (!uiState.isSubmitting) clearStatus();
    });
  }

  if (statusBox) {
    statusBox.addEventListener("click", (event) => {
      const retryBtn = event.target.closest("[data-action='status-retry']");
      if (retryBtn) {
        retryLastRequest();
      }
    });
  }

  if (btnFocusForm) {
    btnFocusForm.addEventListener("click", focusRecommendForm);
  }
  if (btnAdjustCriteria) {
    btnAdjustCriteria.addEventListener("click", focusRecommendForm);
  }
  if (btnErrorAdjust) {
    btnErrorAdjust.addEventListener("click", focusRecommendForm);
  }
  if (btnRetryEmpty) {
    btnRetryEmpty.addEventListener("click", () => {
      const check = validateAllFormFields();
      if (check.valid) {
        executeRecommendation(check.payload, { saveHistory: true });
      }
    });
  }
  if (btnRetryError) {
    btnRetryError.addEventListener("click", retryLastRequest);
  }

  form.addEventListener("reset", () => {
    if (uiState.isSubmitting) return;
    clearAllFieldErrors();
    clearStatus();
    switchResultsView("initial");

    setTimeout(() => {
      if (limitInput) limitInput.value = String(DEFAULT_LIMIT);
      syncTagChips();
    }, 0);
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (uiState.isSubmitting) return;

    clearStatus();
    const check = validateAllFormFields();
    if (!check.valid) {
      // Nếu người dùng chưa có kết quả thành công trước đó và form chưa nhập/chưa hợp lệ,
      // giữ khu vực kết quả ở trạng thái hướng dẫn nhập tiêu chí (không báo nhầm là Backend rỗng).
      if (uiState.view !== "success") {
        switchResultsView("initial");
      }
      return;
    }

    executeRecommendation(check.payload, { saveHistory: true });
  });

  // ---------- Khởi tạo lần đầu khi nạp trang ----------
  function initPage() {
    if (typeof DHResults !== "undefined" && typeof DHResults.initSidebar === "function") {
      DHResults.initSidebar();
    }

    const params = new URLSearchParams(window.location.search);
    const qBudget = params.get("budget_max") || params.get("max_budget") || params.get("budget");
    const qMeal = params.get("meal_type");
    const qPrepTime = params.get("max_prep_time");
    const qAvoid = params.get("avoid") || params.get("excluded_ingredients");
    const qTags = params.get("preferred_tags") || params.get("tags");
    const qLimit = params.get("limit");

    if (qBudget && maxBudgetInput) {
      maxBudgetInput.value = qBudget;
    }

    if (mealTypeSelect) {
      mealTypeSelect.value =
        qMeal && Object.prototype.hasOwnProperty.call(ALLOWED_MEAL_TYPES, qMeal) ? qMeal : "";
    }

    if (maxPrepTimeInput && qPrepTime) {
      maxPrepTimeInput.value = qPrepTime;
    }

    if (avoidInput && qAvoid) {
      avoidInput.value = qAvoid;
    }

    if (preferredTagsInput && qTags) {
      preferredTagsInput.value = qTags;
    }
    syncTagChips();

    if (limitInput) {
      const parsedLimit = Number(qLimit);
      limitInput.value =
        qLimit && Number.isInteger(parsedLimit) && parsedLimit >= MIN_LIMIT && parsedLimit <= MAX_LIMIT
          ? String(parsedLimit)
          : String(DEFAULT_LIMIT);
    }

    const hasQueryParams = Array.from(params.keys()).length > 0;
    if (hasQueryParams) {
      const check = validateAllFormFields();
      if (check.valid) {
        executeRecommendation(check.payload, { saveHistory: true });
        return;
      }
    }

    // Mặc định khi mở trang trực tiếp chưa submit form: hiển thị trạng thái Initial
    switchResultsView("initial");
  }

  global.DHFoodRecommend = {
    uiState,
    validateAllFormFields,
    executeRecommendation,
    retryLastRequest,
    switchResultsView,
    initPage,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPage);
  } else {
    initPage();
  }
})(window);
