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

  // Quản lý trạng thái loading
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

  // Lưu lịch sử vào LocalStorage
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
        criteriaSummary: `Ngân sách ≤ ${moneyStr(data.budget_max)}, ${ALLOWED_MEAL_TYPES[data.meal_type] || data.meal_type}${data.avoid_ingredients && data.avoid_ingredients.length ? `, tránh: ${data.avoid_ingredients.join(", ")}` : ""}`,
        resultSummary: data.top_name ? `Top 1: ${data.top_name} (${Number(data.top_score).toFixed(1)}đ)` : "Không có kết quả",
        total: data.total,
        budget_max: data.budget_max,
        meal_type: data.meal_type,
        avoid_ingredients: data.avoid_ingredients,
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
  function formatApiResults(items) {
    return items.map((item, index) => {
      const rank = index + 1;
      const isTop = rank === 1;

      const reasons = Array.isArray(item.reasons) ? [...item.reasons] : [];
      if (reasons.length === 0) {
        if (item.price) reasons.push(`Mức giá ${moneyStr(item.price)} phù hợp với ngân sách của bạn`);
        if (item.prep_time) reasons.push(`Thời gian chuẩn bị ${item.prep_time} phút nhanh chóng`);
      }

      const pros = [...reasons];
      const cons = [];
      const pScore = item.criteria_scores?.price ?? 70;
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
        image: resolveFoodImage(item.name, item.image_url),
        score: Number(item.score || 0),
        ranking: rank,
        criteria: {
          price: Math.round(item.criteria_scores?.price ?? 0),
          preference: Math.round(item.criteria_scores?.preference ?? 0),
          prep_time: Math.round(item.criteria_scores?.prep_time ?? 0),
        },
        explanation: isTop
          ? `Đứng đầu với ${Number(item.score).toFixed(1)}/100 điểm WSM. Món ăn cân bằng tối ưu giữa ngân sách, loại bữa ăn và thời gian chuẩn bị.`
          : `Xếp hạng ${rank} với ${Number(item.score).toFixed(1)}/100 điểm WSM. ${reasons[0] || ""}`,
        advantages: pros.slice(0, 3),
        disadvantages: cons.slice(0, 2),
      };
    });
  }

  // ---------- HÀM THỰC THI GỢI Ý MÓN ĂN CHÍNH ----------
  async function executeRecommendation(payload) {
    setLoading(true);
    clearStatus();

    const criteriaList = window.FOOD_CRITERIA || [
      { key: "price", label: "Giá", weight: 0.4 },
      { key: "preference", label: "Mức phù hợp nhu cầu/khẩu vị", weight: 0.35 },
      { key: "prep_time", label: "Thời gian chuẩn bị", weight: 0.25 },
    ];

    let finalResults = [];
    let isFromBackend = false;

    // 1. Thử gọi API Backend trước nếu có server chạy
    if (typeof api !== "undefined" && typeof api.post === "function") {
      try {
        let res;
        try {
          res = await api.post("/api/v1/decisions/recommend", payload);
        } catch {
          res = await api.post("/api/v1/food/recommend", payload);
        }

        const data = res && res.data ? res.data : res;
        const rawItems = (data && data.items) || [];
        if (Array.isArray(rawItems) && rawItems.length > 0) {
          finalResults = formatApiResults(rawItems);
          isFromBackend = true;
        }
      } catch (apiErr) {
        console.info("Backend chưa sẵn sàng hoặc gặp lỗi, sử dụng Client-Side Decision Engine:", apiErr.message);
      }
    }

    // 2. Nếu Backend offline hoặc chưa có kết quả: dùng Engine lọc động thông minh của Frontend
    if (!isFromBackend) {
      if (typeof window.filterAndScoreFoods === "function") {
        finalResults = window.filterAndScoreFoods(payload);
      }
    }

    // 3. Render kết quả lên giao diện
    if (!finalResults || finalResults.length === 0) {
      // Trạng thái Empty State (Không có món thỏa mãn)
      if (typeof DHResults !== "undefined" && typeof DHResults.renderEmptyState === "function") {
        DHResults.renderEmptyState(
          `Không tìm thấy món ăn nào phù hợp với ngân sách ≤ ${moneyStr(payload.budget_max)} cho ${ALLOWED_MEAL_TYPES[payload.meal_type] || payload.meal_type}. Hãy thử tăng ngân sách hoặc bỏ bớt nguyên liệu cần tránh!`,
        );
      }
      if (resultsTotalEl) resultsTotalEl.textContent = "0";
      if (resultsTopNameEl) resultsTopNameEl.textContent = "Không có phương án";
      if (resultsTopScoreEl) resultsTopScoreEl.textContent = "";

      showStatus(
        `<strong>Không có món ăn phù hợp:</strong> Với ngân sách <strong>${escapeHtml(moneyStr(payload.budget_max))}</strong> cho <strong>${ALLOWED_MEAL_TYPES[payload.meal_type] || payload.meal_type}</strong>, không có món nào thỏa mãn. Bạn hãy thử nới lỏng ngân sách nhé!`,
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
    } else {
      // Có kết quả -> Render bảng xếp hạng và giải thích chi tiết
      if (typeof DHResults !== "undefined" && typeof DHResults.initResultsPage === "function") {
        DHResults.initResultsPage({
          results: finalResults,
          criteria: criteriaList,
        });
      }

      const topOption = finalResults[0];
      if (resultsTotalEl) resultsTotalEl.textContent = finalResults.length;
      if (resultsTopNameEl) resultsTopNameEl.textContent = topOption.name;
      if (resultsTopScoreEl) {
        resultsTopScoreEl.textContent = `${Number(topOption.score).toFixed(1)}/100 điểm (WSM)`;
      }

      showStatus(
        `✓ Đã tìm thấy <strong>${finalResults.length}</strong> món ăn tối ưu nhất cho bạn. Lựa chọn số 1: <strong>${escapeHtml(topOption.name)}</strong> (${Number(topOption.score).toFixed(1)} điểm WSM).`,
        "success",
      );

      saveToDecisionHistory({
        budget_max: payload.budget_max,
        meal_type: payload.meal_type,
        avoid_ingredients: payload.excluded_ingredients,
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

  // ---------- Khởi tạo lần đầu khi nạp trang ----------
  function initPage() {
    const params = new URLSearchParams(window.location.search);
    const qBudget = params.get("budget_max") || params.get("max_budget") || params.get("budget");
    const qMeal = params.get("meal_type");
    const qAvoid = params.get("avoid") || params.get("excluded_ingredients");

    if (qBudget) {
      maxBudgetInput.value = qBudget;
    } else if (!maxBudgetInput.value) {
      maxBudgetInput.value = "50000";
    }

    if (qMeal && Object.prototype.hasOwnProperty.call(ALLOWED_MEAL_TYPES, qMeal)) {
      mealTypeSelect.value = qMeal;
    } else if (!mealTypeSelect.value) {
      mealTypeSelect.value = "lunch";
    }

    if (qAvoid) {
      avoidInput.value = qAvoid;
    }

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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPage);
  } else {
    initPage();
  }
})();
