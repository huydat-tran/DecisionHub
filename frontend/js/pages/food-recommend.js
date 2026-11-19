// ==========================================================
// Module: Food Recommendation (Đề xuất món ăn thông minh)
// Nối form → API (/api/v1/food/recommend) → Xếp hạng WSM → Giải thích chi tiết
// Tuân thủ UI Guidelines & Clean Code
// ==========================================================

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
  const submitBtn = form.querySelector('button[type="submit"]');
  const resetBtn = document.getElementById("btn-food-recommend-reset");

  const rankingListEl = document.getElementById("results-ranking-list");
  const explanationBodyEl = document.getElementById("results-explanation-body");
  const resultsTotalEl = document.getElementById("results-total");
  const resultsTopNameEl = document.getElementById("results-top-name");
  const resultsTopScoreEl = document.getElementById("results-top-score");

  // ---------- Quản lý trạng thái lỗi form ----------
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

    const parts = raw
      .split(",")
      .map((item) => item.trim())
      .filter((item) => item.length > 0);

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

    // Loại bỏ trùng lặp
    const uniqueParts = Array.from(new Set(parts.map((p) => p.toLowerCase())));
    return { valid: true, value: uniqueParts };
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

  // ---------- Ánh xạ hình ảnh món ăn ----------
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

  // ---------- Xây dựng Ưu điểm & Hạn chế từ tiêu chí WSM ----------
  function buildProsAndCons(item, rank) {
    const pros = [];
    const cons = [];

    // Ưu điểm từ reasons do Decision Engine cung cấp
    if (Array.isArray(item.reasons) && item.reasons.length > 0) {
      pros.push(...item.reasons);
    }

    const scores = item.criteria_scores || {};
    const priceScore = Number(scores.price ?? 0);
    const prefScore = Number(scores.preference ?? 0);
    const prepScore = Number(scores.prep_time ?? 0);

    if (priceScore >= 70 && !pros.some((p) => p.includes("ngân sách") || p.includes("Giá"))) {
      pros.push(`Mức giá ${formatMoney(item.price)} rất tiết kiệm trong tầm ngân sách.`);
    }
    if (prepScore >= 70 && item.prep_time) {
      pros.push(`Thời gian chuẩn bị nhanh (${item.prep_time} phút), không phải chờ lâu.`);
    }
    if (prefScore >= 70 && item.tags && item.tags.length > 0) {
      pros.push(`Đặc trưng món phù hợp sở thích: ${item.tags.join(", ")}.`);
    }

    if (pros.length === 0) {
      pros.push(`Giá ${formatMoney(item.price)} nằm trong giới hạn ngân sách.`);
    }

    // Hạn chế
    if (priceScore < 50) {
      cons.push(`Giá ${formatMoney(item.price)} tiệm cận mức ngân sách tối đa.`);
    }
    if (prepScore < 50 && item.prep_time) {
      cons.push(`Thời gian chế biến (${item.prep_time} phút) lâu hơn các món ăn nhanh khác.`);
    }
    if (prefScore < 40) {
      cons.push("Chưa tối ưu cao cho các sở thích ẩm thực đặc thù.");
    }

    if (cons.length === 0) {
      if (rank > 1) {
        cons.push("Điểm tổng hợp WSM thấp hơn một chút so với phương án đứng đầu.");
      } else {
        cons.push("Không có hạn chế đáng kể trong các tiêu chí đã chọn.");
      }
    }

    return {
      advantages: pros.slice(0, 3),
      disadvantages: cons.slice(0, 2),
    };
  }

  // ---------- Xây dựng câu giải thích xếp hạng ----------
  function buildExplanation(item, rank, total) {
    const reasonsText = Array.isArray(item.reasons) && item.reasons.length > 0
      ? item.reasons.join(". ") + "."
      : "";

    if (rank === 1) {
      return `Đứng đầu với ${Number(item.score).toFixed(1)}/100 điểm tổng hợp WSM. ${reasonsText} Đây là phương án tối ưu và cân bằng nhất giữa ngân sách, loại bữa ăn và thời gian chuẩn bị.`;
    }
    return `Xếp hạng ${rank}/${total} với ${Number(item.score).toFixed(1)}/100 điểm. ${reasonsText}`;
  }

  // ---------- Chuyển đổi dữ liệu API sang format UI ----------
  function formatApiResults(items) {
    return items.map((item, index) => {
      const rank = index + 1;
      const { advantages, disadvantages } = buildProsAndCons(item, rank);
      return {
        id: item.food_id || item.id || (index + 1),
        name: item.name,
        price: item.price,
        prep_time: item.prep_time,
        meal_type: item.meal_type,
        tags: item.tags || [],
        image: resolveFoodImage(item.name, item.image_url),
        score: Number(item.score || 0),
        ranking: rank,
        criteria: {
          price: Math.round(item.criteria_scores?.price ?? 0),
          preference: Math.round(item.criteria_scores?.preference ?? 0),
          prep_time: Math.round(item.criteria_scores?.prep_time ?? 0),
        },
        explanation: buildExplanation(item, rank, items.length),
        advantages,
        disadvantages,
      };
    });
  }

  // ---------- Lưu phiên vào Lịch sử (LocalStorage) ----------
  function saveToDecisionHistory(data) {
    try {
      const STORAGE_KEY = "dh_decision_history";
      const raw = localStorage.getItem(STORAGE_KEY);
      const list = raw ? JSON.parse(raw) : [];

      const record = {
        id: "hist_" + Date.now(),
        createdAt: new Date().toISOString(),
        module: "food",
        moduleLabel: "Gợi ý Món ăn",
        criteriaSummary: `Ngân sách ≤ ${formatMoney(data.budget_max)}, ${ALLOWED_MEAL_TYPES[data.meal_type] || data.meal_type}${data.avoid_ingredients && data.avoid_ingredients.length ? `, tránh: ${data.avoid_ingredients.join(", ")}` : ""}`,
        resultSummary: data.top_name ? `Top 1: ${data.top_name} (${Number(data.top_score).toFixed(1)}đ)` : "Không có kết quả",
        total: data.total,
        budget_max: data.budget_max,
        meal_type: data.meal_type,
        avoid_ingredients: data.avoid_ingredients,
      };

      list.unshift(record);
      // Giữ tối đa 30 bản ghi gần nhất
      const trimmed = list.slice(0, 30);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
    } catch (err) {
      console.warn("Không thể lưu lịch sử quyết định:", err);
    }
  }

  // ---------- Quản lý UI Loading State ----------
  function setLoading(isLoading) {
    if (!submitBtn) return;
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
    } else {
      submitBtn.disabled = false;
      submitBtn.innerHTML = "Gợi ý món ăn";
    }
  }

  // ---------- Luồng chính: Gọi API và hiển thị kết quả ----------
  async function executeRecommendation(payload) {
    setLoading(true);
    clearStatus();

    try {
      showStatus(
        `Đang phân tích tiêu chí: Ngân sách <strong>${escapeHtml(formatMoney(payload.budget_max))}</strong> · Bữa: <strong>${escapeHtml(ALLOWED_MEAL_TYPES[payload.meal_type] || payload.meal_type)}</strong>...`,
        "info",
      );

      // 1. Gọi API Backend (Endpoint chính: /api/v1/food/recommend; fallback: /api/v1/decisions/recommend)
      let res;
      try {
        res = await api.post("/api/v1/food/recommend", payload);
      } catch (primaryError) {
        console.warn("Lỗi gọi /api/v1/food/recommend, thử fallback /api/v1/decisions/recommend:", primaryError);
        res = await api.post("/api/v1/decisions/recommend", payload);
      }

      // Chuẩn hóa cấu trúc dữ liệu trả về từ backend
      const data = res && res.data ? res.data : res;
      const rawItems = (data && data.items) || [];
      const total = typeof data.total === "number" ? data.total : rawItems.length;

      // 2. Xử lý trường hợp không có món nào thỏa mãn (Empty State)
      if (!rawItems || rawItems.length === 0) {
        if (typeof DHResults !== "undefined" && typeof DHResults.renderEmptyState === "function") {
          DHResults.renderEmptyState(
            `Không tìm thấy món ăn nào thỏa mãn ngân sách ≤ ${formatMoney(payload.budget_max)} và các điều kiện đã chọn. Hãy thử tăng ngân sách hoặc giảm bớt nguyên liệu cần tránh!`,
          );
        }
        if (resultsTotalEl) resultsTotalEl.textContent = "0";
        if (resultsTopNameEl) resultsTopNameEl.textContent = "Không có phương án";
        if (resultsTopScoreEl) resultsTopScoreEl.textContent = "";

        showStatus(
          `<strong>Không có kết quả phù hợp:</strong> Không có món ăn nào trong tầm giá <strong>${escapeHtml(formatMoney(payload.budget_max))}</strong>. Vui lòng nới lỏng ngân sách!`,
          "error",
        );

        saveToDecisionHistory({
          budget_max: payload.budget_max,
          meal_type: payload.meal_type,
          avoid_ingredients: payload.excluded_ingredients,
          top_name: "",
          top_score: 0,
          total: 0,
        });

        if (typeof showToast === "function") {
          showToast("Không tìm thấy món ăn phù hợp với tiêu chí.", "error");
        }
        return;
      }

      // 3. Có kết quả -> Chuyển đổi và hiển thị qua DHResults
      const formattedResults = formatApiResults(rawItems);
      const criteriaList = window.FOOD_CRITERIA || [
        { key: "price", label: "Giá", weight: 0.4 },
        { key: "preference", label: "Mức phù hợp nhu cầu/khẩu vị", weight: 0.35 },
        { key: "prep_time", label: "Thời gian chuẩn bị", weight: 0.25 },
      ];

      if (typeof DHResults !== "undefined" && typeof DHResults.initResultsPage === "function") {
        DHResults.initResultsPage({
          results: formattedResults,
          criteria: criteriaList,
        });
      }

      // Cập nhật thông tin tóm tắt
      const topOption = formattedResults[0];
      if (resultsTotalEl) resultsTotalEl.textContent = total;
      if (resultsTopNameEl) resultsTopNameEl.textContent = topOption.name;
      if (resultsTopScoreEl) {
        resultsTopScoreEl.textContent = `${Number(topOption.score).toFixed(1)}/100 điểm (WSM)`;
      }

      showStatus(
        `✓ Đã tìm thấy <strong>${formattedResults.length}</strong> phương án món ăn tối ưu nhất cho bạn. Lựa chọn số 1: <strong>${escapeHtml(topOption.name)}</strong> (${Number(topOption.score).toFixed(1)} điểm).`,
        "success",
      );

      // Lưu lại vào Lịch sử
      saveToDecisionHistory({
        budget_max: payload.budget_max,
        meal_type: payload.meal_type,
        avoid_ingredients: payload.excluded_ingredients,
        top_name: topOption.name,
        top_score: topOption.score,
        total: formattedResults.length,
      });

      if (typeof showToast === "function") {
        showToast(`Đã đề xuất ${formattedResults.length} món ăn phù hợp!`, "success");
      }

      // Tự động cuộn đến danh sách kết quả nếu trên màn hình nhỏ
      if (window.matchMedia("(max-width: 991.98px)").matches) {
        const rankingHeader = document.getElementById("results-ranking-title");
        if (rankingHeader) {
          rankingHeader.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    } catch (error) {
      console.error("Lỗi khi gọi API gợi ý món ăn:", error);
      const errMsg = error.message || "Không thể kết nối đến máy chủ API. Vui lòng kiểm tra backend!";

      showStatus(`<strong>Lỗi xử lý:</strong> ${escapeHtml(errMsg)}`, "error");

      // Fallback hiển thị dữ liệu mẫu nếu mất kết nối server hoàn toàn
      if (window.FOOD_MOCK_RESULTS && window.FOOD_CRITERIA && typeof DHResults !== "undefined") {
        DHResults.initResultsPage({
          results: window.FOOD_MOCK_RESULTS,
          criteria: window.FOOD_CRITERIA,
        });
        showStatus(
          `<strong>Lưu ý:</strong> Đang hiển thị kết quả giả lập mẫu do máy chủ chưa phản hồi (${escapeHtml(errMsg)}).`,
          "error",
        );
      } else if (typeof DHResults !== "undefined") {
        DHResults.renderEmptyState("Đã xảy ra lỗi khi kết nối máy chủ: " + errMsg);
      }

      if (typeof showToast === "function") {
        showToast(errMsg, "error");
      }
    } finally {
      setLoading(false);
    }
  }

  // ---------- Lắng nghe sự kiện người dùng ----------
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

  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      setFieldError(maxBudgetInput, maxBudgetError, "");
      setFieldError(mealTypeSelect, mealTypeError, "");
      setFieldError(avoidInput, avoidError, "");
      clearStatus();
    });
  }

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
      budget_max: budgetResult.value,
      meal_type: mealResult.value,
      excluded_ingredients: avoidResult.value,
      limit: 5,
    };

    executeRecommendation(payload);
  });

  // ---------- Khởi tạo lần đầu khi nạp trang (URL Params hoặc Dữ liệu mặc định) ----------
  function initPage() {
    const params = new URLSearchParams(window.location.search);
    const qBudget = params.get("budget_max") || params.get("max_budget") || params.get("budget");
    const qMeal = params.get("meal_type");
    const qAvoid = params.get("avoid") || params.get("excluded_ingredients");

    if (qBudget) {
      maxBudgetInput.value = qBudget;
    } else if (!maxBudgetInput.value) {
      maxBudgetInput.value = "50000"; // Mặc định 50.000đ
    }

    if (qMeal && Object.prototype.hasOwnProperty.call(ALLOWED_MEAL_TYPES, qMeal)) {
      mealTypeSelect.value = qMeal;
    } else if (!mealTypeSelect.value) {
      mealTypeSelect.value = "lunch"; // Mặc định Bữa trưa
    }

    if (qAvoid) {
      avoidInput.value = qAvoid;
    }

    // Tự động chạy lần đầu từ API để hiển thị kết quả thực tế từ DB ngay
    const initBudget = Number(maxBudgetInput.value) || 50000;
    const initMeal = mealTypeSelect.value || "lunch";
    const initAvoid = avoidInput.value
      ? avoidInput.value.split(",").map((s) => s.trim()).filter(Boolean)
      : [];

    executeRecommendation({
      budget_max: initBudget,
      meal_type: initMeal,
      excluded_ingredients: initAvoid,
      limit: 5,
    });
  }

  // Chạy khi DOM sẵn sàng
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPage);
  } else {
    initPage();
  }
})();
