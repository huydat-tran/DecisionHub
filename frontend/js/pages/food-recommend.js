// ==========================================================
// Module: Food Recommendation (Đề xuất món ăn thông minh)
// Nối form → API/Engine → Bảng xếp hạng WSM → Giải thích chi tiết
// ==========================================================

(function () {
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
  const submitBtn = form.querySelector('button[type="submit"]');

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

  // Helper an toàn tiền tệ
  function moneyStr(val) {
    if (typeof formatMoney === "function") return formatMoney(val);
    return Number(val || 0).toLocaleString("vi-VN") + " ₫";
  }

  // Quản lý lỗi form
  function setFieldError(inputEl, errorEl, message) {
    if (errorEl) errorEl.textContent = message;
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
    return String(rawMessage || "")
      .trim()
      .replace(/^(?:Value error,\s*)+/i, "");
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

  function applyApiErrors(apiErr) {
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

    if (generalErrors.length > 0) {
      showStatus(
        generalErrors.map((msg) => escapeHtml(msg)).join("<br>"),
        "error",
      );
    } else if (firstInvalidInput) {
      showStatus(
        escapeHtml(
          summaryMessage ||
            "Dữ liệu đầu vào không hợp lệ. Vui lòng kiểm tra các ô được đánh dấu.",
        ),
        "error",
      );
    } else {
      showStatus(
        escapeHtml("Dữ liệu đầu vào không hợp lệ. Vui lòng kiểm tra lại."),
        "error",
      );
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

  function getMealLabel(mealType) {
    return mealType ? (ALLOWED_MEAL_TYPES[mealType] || mealType) : "tất cả bữa ăn";
  }

  function validateMealType() {
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
    return raw
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

  function clearStatus() {
    if (statusBox) {
      statusBox.classList.add("d-none");
      statusBox.className = "food-form-status d-none mt-3";
      statusBox.innerHTML = "";
    }
  }

  function showStatus(html, type = "info") {
    if (!statusBox) return;
    statusBox.className = `food-form-status mt-3 alert alert-${type === "error" ? "danger" : type === "success" ? "success" : "info"} py-2 px-3`;
    statusBox.innerHTML = html;
    statusBox.classList.remove("d-none");
  }

  // Quản lý trạng thái loading
  function setLoading(isLoading) {
    if (!submitBtn) return;
    const excludedBodyEl = document.getElementById("results-excluded-body");

    if (isLoading) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `
        <span class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
        Đang phân tích WSM...
      `;
      if (rankingListEl) {
        rankingListEl.innerHTML = `
          <li class="p-4 text-center">
            <div class="spinner-border text-success mb-2" role="status"></div>
            <div class="dh-muted dh-small">Đang lọc điều kiện và tính toán điểm số WSM...</div>
          </li>
        `;
      }
      if (explanationBodyEl) {
        explanationBodyEl.innerHTML = `
          <div class="p-4 text-center dh-muted dh-small">
            Đang tải dữ liệu chi tiết phương án...
          </div>
        `;
      }
      if (excludedBodyEl) {
        excludedBodyEl.innerHTML = `
          <div class="p-4 text-center dh-muted dh-small">
            <div class="spinner-border spinner-border-sm text-secondary me-1" role="status"></div>
            Đang phân tích điều kiện loại trừ...
          </div>
        `;
      }
    } else {
      submitBtn.disabled = false;
      submitBtn.innerHTML = "Gợi ý món ăn";
    }
  }

  // Lưu lịch sử vào LocalStorage
  function saveToDecisionHistory(data) {
    try {
      const STORAGE_KEY = "dh_decision_history";
      const raw = localStorage.getItem(STORAGE_KEY);
      const list = raw ? JSON.parse(raw) : [];

      const summaryParts = [
        `Ngân sách ≤ ${moneyStr(data.budget_max)}`,
        getMealLabel(data.meal_type),
      ];
      if (data.max_prep_time) {
        summaryParts.push(`≤ ${data.max_prep_time} phút`);
      }
      if (data.avoid_ingredients && data.avoid_ingredients.length) {
        summaryParts.push(`tránh: ${data.avoid_ingredients.join(", ")}`);
      }
      if (data.preferred_tags && data.preferred_tags.length) {
        summaryParts.push(`ưu tiên: ${data.preferred_tags.join(", ")}`);
      }

      const record = {
        id: "hist_" + Date.now(),
        createdAt: new Date().toISOString(),
        module: "food",
        moduleLabel: "Gợi ý Món ăn",
        criteriaSummary: summaryParts.join(", "),
        resultSummary: data.top_name ? `Top 1: ${data.top_name} (${Number(data.top_score).toFixed(1)}đ)` : "Không có kết quả",
        total: data.total,
        budget_max: data.budget_max,
        meal_type: data.meal_type,
        max_prep_time: data.max_prep_time ?? null,
        avoid_ingredients: data.avoid_ingredients,
        preferred_tags: data.preferred_tags || [],
        limit: data.limit || DEFAULT_LIMIT,
      };

      list.unshift(record);
      const trimmed = list.slice(0, 30);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
    } catch (err) {
      console.warn("Không thể lưu lịch sử quyết định:", err);
    }
  }

  // Ánh xạ ảnh
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

  // Định dạng dữ liệu từ API Backend sang cấu trúc UI
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
        const scoreVal = detailObj.normalized_score !== undefined
          ? detailObj.normalized_score
          : (criteriaScores[key] !== undefined ? criteriaScores[key] : null);
        const weightVal = detailObj.weight !== undefined
          ? detailObj.weight
          : (weightsMap && weightsMap[key] !== undefined ? weightsMap[key] : crit.weight);
        const contribVal = detailObj.contribution !== undefined
          ? detailObj.contribution
          : (scoreVal !== null ? Math.round(weightVal * scoreVal * 100) / 100 : 0);

        details[key] = {
          label: crit.label,
          normalized_score: scoreVal !== null ? Number(scoreVal) : null,
          weight: Number(weightVal),
          contribution: Number(contribVal),
        };
      });

      const reasons = Array.isArray(item.reasons) ? [...item.reasons] : [];
      if (reasons.length === 0) {
        if (item.price) reasons.push(`Mức giá ${moneyStr(item.price)} phù hợp với ngân sách của bạn`);
        if (item.prep_time) reasons.push(`Thời gian chuẩn bị ${item.prep_time} phút nhanh chóng`);
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
        cons.push(isTop ? "Là lựa chọn hài hòa nhất trong tầm giá" : "Điểm tổng hợp thấp hơn phương án đứng đầu");
      }

      return {
        id: item.food_id || item.id || (index + 1),
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
    const shouldSaveHistory = options && options.saveHistory !== false;
    const reqOptions = { authMode: shouldSaveHistory ? "optional" : "none" };
    const excludedBodyEl = document.getElementById("results-excluded-body");
    const prevRankingHtml = rankingListEl ? rankingListEl.innerHTML : null;
    const prevExplanationHtml = explanationBodyEl ? explanationBodyEl.innerHTML : null;
    const prevExcludedHtml = excludedBodyEl ? excludedBodyEl.innerHTML : null;

    setLoading(true);
    clearStatus();

    const criteriaList = window.FOOD_CRITERIA || [
      { key: "price", label: "Giá", weight: 0.4 },
      { key: "preference", label: "Mức phù hợp nhu cầu/khẩu vị", weight: 0.35 },
      { key: "prep_time", label: "Thời gian chuẩn bị", weight: 0.25 },
    ];

    let finalResults = [];
    let excludedItems = [];
    let isFromBackend = false;
    let backendMessage = "";

    // 1. Thử gọi API Backend trước nếu có server chạy
    if (typeof api !== "undefined" && typeof api.post === "function") {
      try {
        const res = await api.post("/decisions/food/recommend", payload, reqOptions);

        const data = res && res.data ? res.data : res;
        if (data) {
          if (Array.isArray(data.items)) {
            finalResults = formatApiResults(data.items, criteriaList, data.scoring?.weights);
          }
          if (Array.isArray(data.excluded_items)) {
            excludedItems = data.excluded_items;
          }
          backendMessage = data.message || "";
          isFromBackend = true;
        }
      } catch (apiErr) {
        if (apiErr && (apiErr.status === 422 || apiErr.status === 400)) {
          if (rankingListEl && prevRankingHtml !== null) {
            rankingListEl.innerHTML = prevRankingHtml;
          }
          if (explanationBodyEl && prevExplanationHtml !== null) {
            explanationBodyEl.innerHTML = prevExplanationHtml;
          }
          if (excludedBodyEl && prevExcludedHtml !== null) {
            excludedBodyEl.innerHTML = prevExcludedHtml;
          }
          applyApiErrors(apiErr);
          setLoading(false);
          return;
        }
        console.info("Backend chưa sẵn sàng hoặc gặp lỗi, sử dụng Client-Side Decision Engine:", apiErr.message);
      }
    }

    // 2. Nếu Backend offline hoặc chưa có kết quả: dùng Engine lọc động thông minh của Frontend
    if (!isFromBackend) {
      if (typeof window.filterAndScoreFoods === "function") {
        const fallback = window.filterAndScoreFoods(payload);
        finalResults = fallback.items || [];
        excludedItems = fallback.excluded_items || [];
        backendMessage = fallback.message || "";
      }
    }

    // 3. Render kết quả lên giao diện
    const mealText = getMealLabel(payload.meal_type);
    const historyBase = {
      budget_max: payload.budget_max,
      meal_type: payload.meal_type,
      max_prep_time: payload.max_prep_time,
      avoid_ingredients: payload.excluded_ingredients,
      preferred_tags: payload.preferred_tags,
      limit: payload.limit,
    };

    if (!finalResults || finalResults.length === 0) {
      // Trạng thái Không có món thỏa mãn
      if (typeof DHResults !== "undefined") {
        if (excludedItems.length > 0 && typeof DHResults.renderAllExcludedState === "function") {
          DHResults.renderAllExcludedState(
            excludedItems,
            `Không tìm thấy món ăn nào phù hợp với ngân sách ≤ ${moneyStr(payload.budget_max)} cho ${mealText}. Tất cả ${excludedItems.length} phương án đều đã bị loại bởi điều kiện bắt buộc.`,
          );
        } else if (typeof DHResults.renderEmptyState === "function") {
          DHResults.renderEmptyState(
            `Không tìm thấy món ăn nào phù hợp với ngân sách ≤ ${moneyStr(payload.budget_max)} cho ${mealText}. Hãy thử tăng ngân sách hoặc nới bớt điều kiện lọc!`,
          );
          if (typeof DHResults.renderExcludedCandidates === "function") {
            DHResults.renderExcludedCandidates([]);
          }
        }
      }

      if (resultsTotalEl) resultsTotalEl.textContent = "0";
      if (resultsTopNameEl) resultsTopNameEl.textContent = "Không có phương án";
      if (resultsTopScoreEl) resultsTopScoreEl.textContent = "";

      const msgHtml = excludedItems.length > 0
        ? `<strong>Không có món ăn phù hợp:</strong> Tất cả <strong>${excludedItems.length}</strong> món ăn đều đã bị loại bởi điều kiện bắt buộc (ngân sách <strong>${escapeHtml(moneyStr(payload.budget_max))}</strong>, <strong>${escapeHtml(mealText)}</strong>). Vui lòng xem lý do chi tiết ở bảng phía dưới để nới lỏng điều kiện!`
        : `<strong>Không có món ăn phù hợp:</strong> Với ngân sách <strong>${escapeHtml(moneyStr(payload.budget_max))}</strong> cho <strong>${escapeHtml(mealText)}</strong>, không có món nào thỏa mãn. Bạn hãy thử nới lỏng điều kiện nhé!`;

      showStatus(msgHtml, "warning");

      saveToDecisionHistory({
        ...historyBase,
        top_name: "",
        top_score: 0,
        total: 0,
      });

      if (typeof showToast === "function") {
        showToast("Không tìm thấy món ăn phù hợp với tiêu chí.", "warning");
      }
    } else {
      // Có kết quả -> Render bảng xếp hạng, giải thích chi tiết và danh sách bị loại
      if (typeof DHResults !== "undefined" && typeof DHResults.initResultsPage === "function") {
        DHResults.initResultsPage({
          results: finalResults,
          criteria: criteriaList,
          excluded: excludedItems,
          message: backendMessage,
        });
      }

      const topOption = finalResults[0];
      if (resultsTotalEl) resultsTotalEl.textContent = finalResults.length;
      if (resultsTopNameEl) resultsTopNameEl.textContent = topOption.name;
      if (resultsTopScoreEl) {
        resultsTopScoreEl.textContent = `${Number(topOption.score).toFixed(1)}/100 điểm (WSM)`;
      }

      const excludedNotice = excludedItems.length > 0
        ? ` (và <strong>${excludedItems.length}</strong> phương án bị loại bởi điều kiện bắt buộc)`
        : "";

      showStatus(
        `✓ Đã tìm thấy <strong>${finalResults.length}</strong> món ăn tối ưu nhất${excludedNotice}. Lựa chọn số 1: <strong>${escapeHtml(topOption.name)}</strong> (${Number(topOption.score).toFixed(1)} điểm WSM).`,
        "success",
      );

      saveToDecisionHistory({
        ...historyBase,
        top_name: topOption.name,
        top_score: topOption.score,
        total: finalResults.length,
      });

      if (typeof showToast === "function") {
        showToast(`Đã đề xuất ${finalResults.length} món ăn phù hợp!`, "success");
      }

      // Cuộn mượt màn hình tới bảng xếp hạng nếu đang trên màn hình nhỏ
      if (window.matchMedia("(max-width: 991.98px)").matches) {
        const rankingHeader = document.getElementById("results-ranking-title");
        if (rankingHeader) {
          rankingHeader.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    }

    setLoading(false);
  }

  // ---------- GẮN SỰ KIỆN FORM ----------
  maxBudgetInput.addEventListener("input", () => {
    setFieldError(maxBudgetInput, maxBudgetError, "");
    clearStatus();
  });

  mealTypeSelect.addEventListener("change", () => {
    setFieldError(mealTypeSelect, mealTypeError, "");
    clearStatus();
  });

  if (maxPrepTimeInput) {
    maxPrepTimeInput.addEventListener("input", () => {
      setFieldError(maxPrepTimeInput, maxPrepTimeError, "");
      clearStatus();
    });
  }

  avoidInput.addEventListener("input", () => {
    setFieldError(avoidInput, avoidError, "");
    clearStatus();
  });

  if (preferredTagsInput) {
    preferredTagsInput.addEventListener("input", () => {
      setFieldError(preferredTagsInput, preferredTagsError, "");
      clearStatus();
      syncTagChips();
    });
  }

  if (preferredTagChips && preferredTagsInput) {
    preferredTagChips.addEventListener("click", (event) => {
      const btn = event.target.closest(".dh-chip[data-tag]");
      if (!btn) return;
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
      clearStatus();
    });
  }

  form.addEventListener("reset", () => {
    setFieldError(maxBudgetInput, maxBudgetError, "");
    setFieldError(mealTypeSelect, mealTypeError, "");
    setFieldError(maxPrepTimeInput, maxPrepTimeError, "");
    setFieldError(avoidInput, avoidError, "");
    setFieldError(preferredTagsInput, preferredTagsError, "");
    setFieldError(limitInput, limitError, "");
    clearStatus();

    setTimeout(() => {
      if (limitInput) limitInput.value = String(DEFAULT_LIMIT);
      syncTagChips();
    }, 0);
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearStatus();

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
      if (firstFailure[1]) firstFailure[1].focus();
      return;
    }

    const payload = {
      budget_max: budgetResult.value,
      meal_type: mealResult.value,
      max_prep_time: prepTimeResult.value,
      excluded_ingredients: avoidResult.value,
      preferred_tags: tagsResult.value,
      limit: limitResult.value,
    };

    executeRecommendation(payload);
  });

  // ---------- Khởi tạo lần đầu khi nạp trang ----------
  function initPage() {
    const params = new URLSearchParams(window.location.search);
    const qBudget = params.get("budget_max") || params.get("max_budget") || params.get("budget");
    const qMeal = params.get("meal_type");
    const qPrepTime = params.get("max_prep_time");
    const qAvoid = params.get("avoid") || params.get("excluded_ingredients");
    const qTags = params.get("preferred_tags") || params.get("tags");
    const qLimit = params.get("limit");

    if (qBudget) {
      maxBudgetInput.value = qBudget;
    } else if (!maxBudgetInput.value) {
      maxBudgetInput.value = "50000";
    }

    if (qMeal && Object.prototype.hasOwnProperty.call(ALLOWED_MEAL_TYPES, qMeal)) {
      mealTypeSelect.value = qMeal;
    } else {
      mealTypeSelect.value = "";
    }

    if (maxPrepTimeInput && qPrepTime) {
      maxPrepTimeInput.value = qPrepTime;
    }

    if (qAvoid) {
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

    const budgetCheck = validateMaxBudget();
    const mealCheck = validateMealType();
    const prepTimeCheck = validateMaxPrepTime();
    const avoidCheck = validateCommaList(avoidInput, {
      maxItems: MAX_LIST_ITEMS,
      itemNoun: "nguyên liệu cần tránh",
    });
    const tagsCheck = validateCommaList(preferredTagsInput, {
      maxItems: MAX_LIST_ITEMS,
      itemNoun: "khẩu vị/nhãn ưu tiên",
    });
    const limitCheck = validateLimit();

    const hasQueryParams = Array.from(params.keys()).length > 0;

    executeRecommendation(
      {
        budget_max: budgetCheck.valid ? budgetCheck.value : 50000,
        meal_type: mealCheck.valid ? mealCheck.value : null,
        max_prep_time: prepTimeCheck.valid ? prepTimeCheck.value : null,
        excluded_ingredients: avoidCheck.valid ? avoidCheck.value : [],
        preferred_tags: tagsCheck.valid ? tagsCheck.value : [],
        limit: limitCheck.valid ? limitCheck.value : DEFAULT_LIMIT,
      },
      { saveHistory: hasQueryParams },
    );
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPage);
  } else {
    initPage();
  }
})();
