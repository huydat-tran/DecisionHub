// ==========================================================
// Module: Decision History (Lịch sử quyết định)
// Tích hợp trực tiếp với Backend API:
//   - GET /decisions/history?limit=...&offset=...
//   - GET /decisions/history/{decision_id}
// Yêu cầu đăng nhập (JWT Bearer token qua api.get với authMode: "required").
// ==========================================================

(function (global) {
  const DEFAULT_PAGE_LIMIT = 10;

  const DOMAIN_CONFIG = {
    food: {
      icon: "🍲",
      label: "Gợi ý Món ăn",
      shortLabel: "Món ăn (Food)",
      badgeClass: "history-badge-food",
    },
    travel: {
      icon: "✈️",
      label: "Gợi ý Du lịch",
      shortLabel: "Du lịch (Travel)",
      badgeClass: "history-badge-travel",
    },
  };

  const MEAL_TYPE_LABELS = {
    breakfast: "Bữa sáng",
    lunch: "Bữa trưa",
    dinner: "Bữa tối",
    snack: "Bữa phụ / Ăn vặt",
  };

  const CRITERION_LABELS = {
    price: "Giá / Ngân sách",
    preference: "Phù hợp nhu cầu / khẩu vị",
    prep_time: "Thời gian chuẩn bị",
    estimated_cost: "Chi phí ước tính",
    estimated_duration: "Thời lượng trải nghiệm",
    activities: "Hoạt động & Trải nghiệm",
  };

  const state = {
    items: [],
    total: 0,
    limit: DEFAULT_PAGE_LIMIT,
    offset: 0,
    currentFilter: "all",
    currentView: "list", // "list" | "detail"
    activeDecisionId: null,
    activeDecision: null,
  };

  // ---------- Helpers an toàn & định dạng ----------

  function safeHtml(value) {
    if (typeof escapeHtml === "function") return escapeHtml(value);
    if (value === null || value === undefined) return "";
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatVnd(value) {
    if (value === null || value === undefined || value === "" || Number.isNaN(Number(value))) {
      return "–";
    }
    if (typeof formatMoney === "function") return formatMoney(Number(value));
    return Number(value).toLocaleString("vi-VN") + " ₫";
  }

  function formatTime(value) {
    if (!value) return "–";
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    if (typeof formatDateTime === "function") return formatDateTime(value);
    return (
      d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }) +
      " " +
      d.toLocaleDateString("vi-VN")
    );
  }

  function formatScore(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "–";
    return Number(value).toLocaleString("vi-VN", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    });
  }

  function formatPercent(weight) {
    if (weight === null || weight === undefined || Number.isNaN(Number(weight))) return "–";
    return Math.round(Number(weight) * 100) + "%";
  }

  function getDomainMeta(domain) {
    const key = String(domain || "food").toLowerCase();
    return (
      DOMAIN_CONFIG[key] || {
        icon: "📋",
        label: `Quyết định (${domain || "Khác"})`,
        shortLabel: String(domain || "Khác"),
        badgeClass: "history-badge-food",
      }
    );
  }

  function getMealLabel(mealType) {
    if (!mealType) return "Tất cả bữa ăn";
    return MEAL_TYPE_LABELS[mealType] || String(mealType);
  }

  // Trích xuất thông báo lỗi thân thiện từ ApiError của Backend
  function extractErrorMessage(error, fallbackMessage) {
    if (!error) return fallbackMessage;
    if (error.data && typeof error.data.message === "string" && error.data.message.trim()) {
      return error.data.message.trim();
    }
    if (error.data && typeof error.data.detail === "string" && error.data.detail.trim()) {
      return error.data.detail.trim();
    }
    if (typeof error.message === "string" && error.message.trim() && !/^Lỗi \d+$/.test(error.message.trim())) {
      return error.message.trim();
    }
    return fallbackMessage;
  }

  // ---------- Truy xuất phần tử DOM ----------

  function getEls() {
    return {
      pageTitle: document.getElementById("history-page-title"),
      pageDesc: document.getElementById("history-page-desc"),
      btnBackToList: document.getElementById("btn-back-to-list"),
      btnReload: document.getElementById("btn-reload-history"),

      authRequired: document.getElementById("history-auth-required"),

      listView: document.getElementById("history-list-view"),
      toolbar: document.getElementById("history-toolbar"),
      filterChips: document.getElementById("history-filter-chips"),
      countAll: document.getElementById("count-filter-all"),
      countFood: document.getElementById("count-filter-food"),
      countTravel: document.getElementById("count-filter-travel"),
      summaryCounter: document.getElementById("history-summary-counter"),

      loadingBox: document.getElementById("history-loading"),
      errorBox: document.getElementById("history-error"),
      errorMessage: document.getElementById("history-error-message"),
      btnRetryHistory: document.getElementById("btn-retry-history"),

      emptyBox: document.getElementById("history-empty"),
      emptyTitle: document.getElementById("history-empty-title"),
      emptyDesc: document.getElementById("history-empty-desc"),
      btnResetFilter: document.getElementById("btn-reset-history-filter"),

      cardsContainer: document.getElementById("history-cards-container"),
      paginationBar: document.getElementById("history-pagination"),
      pageInfo: document.getElementById("history-page-info"),
      btnPrevPage: document.getElementById("btn-prev-page"),
      btnNextPage: document.getElementById("btn-next-page"),

      detailView: document.getElementById("history-detail-view"),
      detailLoading: document.getElementById("history-detail-loading"),
      detailNotFound: document.getElementById("history-detail-not-found"),
      detailNotFoundText: document.getElementById("history-detail-not-found-text"),
      btnNotFoundBack: document.getElementById("btn-not-found-back"),
      detailError: document.getElementById("history-detail-error"),
      detailErrorText: document.getElementById("history-detail-error-text"),
      btnRetryDetail: document.getElementById("btn-retry-detail"),
      btnErrorBack: document.getElementById("btn-error-back"),
      detailContent: document.getElementById("history-detail-content"),
    };
  }

  // ---------- Gọi API Backend ----------

  async function fetchHistoryList(limit, offset) {
    return api.get(
      "/decisions/history",
      { limit, offset },
      { authMode: "required" },
    );
  }

  async function fetchHistoryDetail(decisionId) {
    return api.get(
      `/decisions/history/${encodeURIComponent(decisionId)}`,
      undefined,
      { authMode: "required" },
    );
  }

  // ---------- Xử lý dữ liệu Snapshot ----------

  function normalizeRecord(raw) {
    if (!raw || typeof raw !== "object") return null;
    const item = raw.data && typeof raw.data === "object" && !Array.isArray(raw.data) ? raw.data : raw;
    const input = item.input_snapshot && typeof item.input_snapshot === "object" ? item.input_snapshot : {};
    const result = item.result_snapshot && typeof item.result_snapshot === "object" ? item.result_snapshot : {};
    const rankedItems = Array.isArray(result.items) ? result.items : [];
    const excludedItems = Array.isArray(result.excluded_items) ? result.excluded_items : [];
    const topItem = rankedItems.length > 0 ? rankedItems[0] : null;

    return {
      id: item.id,
      user_id: item.user_id,
      domain: String(item.domain || "food").toLowerCase(),
      created_at: item.created_at,
      input_snapshot: input,
      result_snapshot: result,
      rankedItems,
      excludedItems,
      topItem,
      totalValid: result.total !== undefined ? Number(result.total) : rankedItems.length,
      totalExcluded: result.total_excluded !== undefined ? Number(result.total_excluded) : excludedItems.length,
    };
  }

  function buildInputSpecsPills(record) {
    const input = record.input_snapshot || {};
    const pills = [];

    if (input.budget_max !== undefined && input.budget_max !== null) {
      pills.push(
        `<span class="history-spec-pill">Ngân sách: <strong>≤ ${safeHtml(formatVnd(input.budget_max))}</strong></span>`,
      );
    }

    if (record.domain === "travel") {
      if (input.region) {
        pills.push(`<span class="history-spec-pill">Khu vực: <strong>${safeHtml(input.region)}</strong></span>`);
      }
      if (input.max_duration !== undefined && input.max_duration !== null) {
        pills.push(
          `<span class="history-spec-pill">Thời lượng: <strong>≤ ${safeHtml(input.max_duration)} giờ</strong></span>`,
        );
      }
      if (input.activity_type) {
        pills.push(
          `<span class="history-spec-pill">Loại hình: <strong>${safeHtml(input.activity_type)}</strong></span>`,
        );
      }
      if (Array.isArray(input.preferred_highlights) && input.preferred_highlights.length > 0) {
        pills.push(
          `<span class="history-spec-pill">Ưu tiên: <strong>${safeHtml(input.preferred_highlights.join(", "))}</strong></span>`,
        );
      }
    } else {
      pills.push(
        `<span class="history-spec-pill">Bữa ăn: <strong>${safeHtml(getMealLabel(input.meal_type))}</strong></span>`,
      );
      if (input.max_prep_time !== undefined && input.max_prep_time !== null) {
        pills.push(
          `<span class="history-spec-pill">Chuẩn bị: <strong>≤ ${safeHtml(input.max_prep_time)} phút</strong></span>`,
        );
      }
      if (Array.isArray(input.excluded_ingredients) && input.excluded_ingredients.length > 0) {
        pills.push(
          `<span class="history-spec-pill">Tránh: <strong>${safeHtml(input.excluded_ingredients.join(", "))}</strong></span>`,
        );
      }
      if (Array.isArray(input.preferred_tags) && input.preferred_tags.length > 0) {
        pills.push(
          `<span class="history-spec-pill">Khẩu vị: <strong>${safeHtml(input.preferred_tags.join(", "))}</strong></span>`,
        );
      }
    }

    return pills.join("");
  }

  // ---------- Render Danh sách lịch sử ----------

  function updateFilterCounts() {
    const els = getEls();
    const allCount = state.items.length;
    const foodCount = state.items.filter((item) => item.domain === "food").length;
    const travelCount = state.items.filter((item) => item.domain === "travel").length;

    if (els.countAll) els.countAll.textContent = String(allCount);
    if (els.countFood) els.countFood.textContent = String(foodCount);
    if (els.countTravel) els.countTravel.textContent = String(travelCount);
  }

  function getFilteredItems() {
    if (state.currentFilter === "all") return state.items;
    return state.items.filter((item) => item.domain === state.currentFilter);
  }

  function renderDecisionCard(record) {
    const meta = getDomainMeta(record.domain);
    const top = record.topItem;
    const topScore = top ? (top.total_score ?? top.score ?? 0) : null;
    const topCost = top ? (top.price ?? top.estimated_cost ?? null) : null;
    const topTime = top
      ? top.prep_time !== undefined && top.prep_time !== null
        ? `${top.prep_time} phút`
        : top.estimated_duration !== undefined && top.estimated_duration !== null
          ? `${top.estimated_duration} giờ`
          : null
      : null;

    const highlightSubParts = [];
    if (topCost !== null) highlightSubParts.push(`Chi phí: ${formatVnd(topCost)}`);
    if (topTime) highlightSubParts.push(`Thời gian: ${topTime}`);
    highlightSubParts.push(`${record.totalValid} phương án phù hợp`);

    const highlightHtml = top
      ? `
        <div class="history-highlight-box">
          <div>
            <div class="history-highlight-label">★ Đề xuất hạng #1</div>
            <h3 class="history-highlight-title">${safeHtml(top.name || "Phương án đề xuất")}</h3>
            <div class="history-highlight-sub">${safeHtml(highlightSubParts.join(" · "))}</div>
          </div>
          <div class="history-highlight-score" aria-label="Điểm WSM">
            <span class="history-highlight-score-val">${safeHtml(formatScore(topScore))}</span>
            <span class="history-highlight-score-unit">/ 100 WSM</span>
          </div>
        </div>`
      : `
        <div class="history-highlight-box is-empty">
          <div>
            <div class="history-highlight-label">⚠️ Không có phương án thỏa mãn</div>
            <h3 class="history-highlight-title">0 phương án hợp lệ</h3>
            <div class="history-highlight-sub">
              ${safeHtml(record.result_snapshot.message || `Đã loại ${record.totalExcluded} phương án do vi phạm điều kiện bắt buộc.`)}
            </div>
          </div>
        </div>`;

    return `
      <article class="dh-card history-decision-card" data-decision-card="${safeHtml(record.id)}">
        <div class="history-card-top">
          <div class="history-card-meta">
            <span class="history-domain-badge ${meta.badgeClass}">
              <span aria-hidden="true">${meta.icon}</span>
              <span>${safeHtml(meta.label)}</span>
            </span>
            <span class="history-decision-id"> Quyết định #${safeHtml(record.id)}</span>
          </div>
          <div class="history-decision-time">
            <span aria-hidden="true">🕒</span>
            <time datetime="${safeHtml(record.created_at)}">${safeHtml(formatTime(record.created_at))}</time>
          </div>
        </div>

        <div class="history-card-body">
          <div class="history-card-grid">
            ${highlightHtml}

            <div>
              <div class="history-criteria-summary-title">Tiêu chí đầu vào & Thống kê</div>
              <div class="history-specs-list">
                ${buildInputSpecsPills(record)}
                <span class="history-spec-pill">
                  Hợp lệ: <strong>${safeHtml(record.totalValid)}</strong> · Bị loại: <strong>${safeHtml(record.totalExcluded)}</strong>
                </span>
              </div>
            </div>

            <div class="history-card-actions">
              <button
                type="button"
                class="dh-btn dh-btn-primary dh-btn-sm"
                data-action="view-detail"
                data-decision-id="${safeHtml(record.id)}"
              >
                Xem chi tiết
              </button>
            </div>
          </div>
        </div>
      </article>
    `;
  }

  function renderPagination() {
    const els = getEls();
    if (!els.paginationBar) return;

    if (state.total <= 0 || (state.offset === 0 && state.total <= state.limit)) {
      els.paginationBar.classList.add("d-none");
      return;
    }

    const currentPage = Math.floor(state.offset / state.limit) + 1;
    const totalPages = Math.max(1, Math.ceil(state.total / state.limit));
    const startIdx = state.total === 0 ? 0 : state.offset + 1;
    const endIdx = Math.min(state.total, state.offset + state.items.length);

    if (els.pageInfo) {
      els.pageInfo.textContent = `Hiển thị ${startIdx}–${endIdx} trong tổng số ${state.total} quyết định (Trang ${currentPage}/${totalPages})`;
    }
    if (els.btnPrevPage) {
      els.btnPrevPage.disabled = state.offset <= 0;
    }
    if (els.btnNextPage) {
      els.btnNextPage.disabled = state.offset + state.limit >= state.total;
    }

    els.paginationBar.classList.remove("d-none");
  }

  function renderHistoryList() {
    const els = getEls();
    updateFilterCounts();

    if (els.loadingBox) els.loadingBox.classList.add("d-none");
    if (els.errorBox) els.errorBox.classList.add("d-none");
    if (els.authRequired) els.authRequired.classList.add("d-none");

    const filtered = getFilteredItems();

    if (els.summaryCounter) {
      els.summaryCounter.textContent =
        state.currentFilter === "all"
          ? `Tổng cộng ${state.total} quyết định đã lưu`
          : `Đang lọc: ${filtered.length} / ${state.items.length} quyết định trên trang này`;
    }

    if (state.items.length === 0) {
      if (els.cardsContainer) {
        els.cardsContainer.innerHTML = "";
        els.cardsContainer.classList.add("d-none");
      }
      if (els.paginationBar) els.paginationBar.classList.add("d-none");
      if (els.emptyTitle) els.emptyTitle.textContent = "Chưa có lịch sử quyết định";
      if (els.emptyDesc) {
        els.emptyDesc.textContent =
          "Tài khoản của bạn chưa có quyết định nào được lưu. Hãy thực hiện gợi ý món ăn hoặc du lịch để hệ thống lưu lại lịch sử.";
      }
      if (els.btnResetFilter) els.btnResetFilter.classList.add("d-none");
      if (els.emptyBox) els.emptyBox.classList.remove("d-none");
      return;
    }

    if (filtered.length === 0) {
      if (els.cardsContainer) {
        els.cardsContainer.innerHTML = "";
        els.cardsContainer.classList.add("d-none");
      }
      const meta = getDomainMeta(state.currentFilter);
      if (els.emptyTitle) {
        els.emptyTitle.textContent = `Không có quyết định thuộc phân hệ ${meta.shortLabel}`;
      }
      if (els.emptyDesc) {
        els.emptyDesc.textContent =
          "Không tìm thấy quyết định nào khớp với bộ lọc hiện tại. Bạn có thể chuyển về xem tất cả phân hệ.";
      }
      if (els.btnResetFilter) els.btnResetFilter.classList.remove("d-none");
      if (els.emptyBox) els.emptyBox.classList.remove("d-none");
      renderPagination();
      return;
    }

    if (els.emptyBox) els.emptyBox.classList.add("d-none");
    if (els.cardsContainer) {
      els.cardsContainer.innerHTML = filtered.map(renderDecisionCard).join("");
      els.cardsContainer.classList.remove("d-none");
    }
    renderPagination();
  }

  // ---------- Render Chi tiết quyết định ----------

  function extractWeightsMap(record) {
    const resScoring = record.result_snapshot && record.result_snapshot.scoring;
    if (resScoring && resScoring.weights && typeof resScoring.weights === "object") {
      return resScoring.weights;
    }
    const inWeights = record.input_snapshot && record.input_snapshot.weights;
    if (inWeights && typeof inWeights === "object") {
      return inWeights;
    }
    const inScoring = record.input_snapshot && record.input_snapshot.scoring;
    if (inScoring && inScoring.weights && typeof inScoring.weights === "object") {
      return inScoring.weights;
    }
    return null;
  }

  function renderDetailInputGrid(record) {
    const input = record.input_snapshot || {};
    const fields = [];

    fields.push({
      label: "Ngân sách tối đa",
      value: input.budget_max !== undefined ? formatVnd(input.budget_max) : "Không giới hạn",
    });

    if (record.domain === "travel") {
      fields.push({
        label: "Khu vực",
        value: input.region || "Tất cả khu vực",
      });
      fields.push({
        label: "Thời lượng tối đa",
        value:
          input.max_duration !== undefined && input.max_duration !== null
            ? `≤ ${input.max_duration} giờ`
            : "Không giới hạn",
      });
      fields.push({
        label: "Loại hình trải nghiệm",
        value: input.activity_type || "Tất cả loại hình",
      });
      fields.push({
        label: "Điểm nổi bật ưu tiên",
        value:
          Array.isArray(input.preferred_highlights) && input.preferred_highlights.length > 0
            ? input.preferred_highlights.join(", ")
            : "Không chọn",
      });
    } else {
      fields.push({
        label: "Loại bữa ăn",
        value: getMealLabel(input.meal_type),
      });
      fields.push({
        label: "Thời gian chuẩn bị tối đa",
        value:
          input.max_prep_time !== undefined && input.max_prep_time !== null
            ? `≤ ${input.max_prep_time} phút`
            : "Không giới hạn",
      });
      fields.push({
        label: "Nguyên liệu cần tránh",
        value:
          Array.isArray(input.excluded_ingredients) && input.excluded_ingredients.length > 0
            ? input.excluded_ingredients.join(", ")
            : "Không có",
      });
      fields.push({
        label: "Khẩu vị / Nhãn ưu tiên",
        value:
          Array.isArray(input.preferred_tags) && input.preferred_tags.length > 0
            ? input.preferred_tags.join(", ")
            : "Không chọn",
      });
    }

    fields.push({
      label: "Số lượng gợi ý tối đa (Limit)",
      value: `${input.limit || record.result_snapshot.limit || 5} phương án`,
    });

    const weights = extractWeightsMap(record);
    if (weights) {
      const weightParts = Object.entries(weights).map(
        ([k, v]) => `${CRITERION_LABELS[k] || k}: ${formatPercent(v)}`,
      );
      fields.push({
        label: "Trọng số tiêu chí (WSM)",
        value: weightParts.join(" · "),
      });
    }

    return fields
      .map(
        (f) => `
        <div class="history-input-item">
          <span class="history-input-label">${safeHtml(f.label)}</span>
          <div class="history-input-val">${safeHtml(f.value)}</div>
        </div>`,
      )
      .join("");
  }

  function renderRankedOptionCriteria(option, fallbackWeights) {
    const details = option.criteria_details && typeof option.criteria_details === "object"
      ? option.criteria_details
      : null;
    const scores = option.criteria_scores && typeof option.criteria_scores === "object"
      ? option.criteria_scores
      : null;

    const keys = details
      ? Object.keys(details)
      : scores
        ? Object.keys(scores)
        : [];

    if (keys.length === 0) return "";

    const bars = keys
      .map((key) => {
        const detailObj = details && details[key] ? details[key] : {};
        const scoreVal =
          detailObj.normalized_score !== undefined && detailObj.normalized_score !== null
            ? Number(detailObj.normalized_score)
            : scores && scores[key] !== undefined
              ? Number(scores[key])
              : 0;
        const weightVal =
          detailObj.weight !== undefined
            ? detailObj.weight
            : fallbackWeights && fallbackWeights[key] !== undefined
              ? fallbackWeights[key]
              : null;
        const contributionVal =
          detailObj.contribution !== undefined ? Number(detailObj.contribution) : null;

        const label = CRITERION_LABELS[key] || key;
        const weightText = weightVal !== null ? ` · trọng số ${formatPercent(weightVal)}` : "";
        const contribText =
          contributionVal !== null ? ` (đóng góp +${formatScore(contributionVal)}đ)` : "";

        return `
          <div class="dh-criteria-item">
            <div class="dh-criteria-header">
              <span>${safeHtml(label)}<span class="dh-muted">${safeHtml(weightText)}</span></span>
              <strong>${safeHtml(formatScore(scoreVal))}/100${safeHtml(contribText)}</strong>
            </div>
            <div class="dh-progress-track">
              <div class="dh-progress-bar" style="width: ${Math.min(100, Math.max(0, scoreVal))}%"></div>
            </div>
          </div>
        `;
      })
      .join("");

    return `
      <div class="mt-3">
        <div class="dh-small fw-bold dh-muted mb-2">Điểm thành phần theo từng tiêu chí</div>
        <div class="dh-criteria-group mb-0">${bars}</div>
      </div>
    `;
  }

  function renderRankedOptionCard(option, idx, fallbackWeights) {
    const rank = option.rank !== undefined ? Number(option.rank) : idx + 1;
    const isTop = rank === 1;
    const totalScore = option.total_score ?? option.score ?? 0;
    const reasons = Array.isArray(option.reasons) ? option.reasons : [];
    const tags = Array.isArray(option.tags) ? option.tags : [];

    const specs = [];
    if (option.price !== undefined && option.price !== null) {
      specs.push(`<span class="history-spec-pill">Giá: <strong>${safeHtml(formatVnd(option.price))}</strong></span>`);
    }
    if (option.estimated_cost !== undefined && option.estimated_cost !== null) {
      specs.push(
        `<span class="history-spec-pill">Chi phí: <strong>${safeHtml(formatVnd(option.estimated_cost))}</strong></span>`,
      );
    }
    if (option.prep_time !== undefined && option.prep_time !== null) {
      specs.push(
        `<span class="history-spec-pill">Chuẩn bị: <strong>${safeHtml(option.prep_time)} phút</strong></span>`,
      );
    }
    if (option.estimated_duration !== undefined && option.estimated_duration !== null) {
      specs.push(
        `<span class="history-spec-pill">Thời lượng: <strong>${safeHtml(option.estimated_duration)} giờ</strong></span>`,
      );
    }
    if (option.meal_type) {
      specs.push(
        `<span class="history-spec-pill">Bữa: <strong>${safeHtml(getMealLabel(option.meal_type))}</strong></span>`,
      );
    }
    if (option.province_city) {
      specs.push(
        `<span class="history-spec-pill">Địa điểm: <strong>${safeHtml(option.province_city)}</strong></span>`,
      );
    }
    if (tags.length > 0) {
      specs.push(
        `<span class="history-spec-pill">Nhãn: <strong>${safeHtml(tags.join(", "))}</strong></span>`,
      );
    }

    const reasonsHtml =
      reasons.length > 0
        ? `
          <div class="mt-3">
            <div class="dh-small fw-bold dh-muted mb-1">Giải thích lý do đề xuất</div>
            <ul class="dh-reason-list mt-1">
              ${reasons
                .map(
                  (reason) => `
                  <li class="dh-reason-item">
                    <span class="dh-reason-icon" aria-hidden="true">✓</span>
                    <span>${safeHtml(reason)}</span>
                  </li>`,
                )
                .join("")}
            </ul>
          </div>`
        : "";

    return `
      <article class="history-ranked-card${isTop ? " is-top-rank" : ""}">
        <div class="history-ranked-head">
          <div>
            <span class="history-rank-badge">
              ${isTop ? "★ Hạng #1 · Đề xuất tối ưu nhất" : `Hạng #${safeHtml(rank)}`}
            </span>
            <h3 class="history-ranked-title">${safeHtml(option.name || `Phương án #${idx + 1}`)}</h3>
            <div class="history-specs-list">${specs.join("")}</div>
          </div>

          <div class="dh-score-box">
            <span class="dh-score-value">${safeHtml(formatScore(totalScore))}</span>
            <span class="dh-score-label">Điểm WSM</span>
          </div>
        </div>

        ${renderRankedOptionCriteria(option, fallbackWeights)}
        ${reasonsHtml}
      </article>
    `;
  }

  function renderExcludedSection(record) {
    const excluded = record.excludedItems;
    if (!excluded || excluded.length === 0) return "";

    const rows = excluded
      .map((item, idx) => {
        const reasons =
          Array.isArray(item.exclusion_reasons) && item.exclusion_reasons.length > 0
            ? item.exclusion_reasons.join("; ")
            : item.exclusion_reason || "Vi phạm điều kiện bắt buộc";
        return `
          <tr>
            <td><strong>${safeHtml(item.name || `Phương án #${item.id || idx + 1}`)}</strong></td>
            <td><span class="dh-status dh-status-danger">Bị loại</span></td>
            <td class="text-danger">${safeHtml(reasons)}</td>
          </tr>
        `;
      })
      .join("");

    return `
      <section class="dh-card history-excluded-card mt-4">
        <div class="dh-card-header">
          <div>
            <h2 class="dh-section-title mb-0" style="font-size:16px;">
              Các phương án bị loại bởi điều kiện bắt buộc (${safeHtml(excluded.length)})
            </h2>
            <small class="dh-muted">Phương án không thỏa mãn ràng buộc cứng trước khi chấm điểm WSM</small>
          </div>
          <span class="dh-status dh-status-danger">${safeHtml(excluded.length)} bị loại</span>
        </div>
        <div class="dh-card-body p-0">
          <div class="table-responsive">
            <table class="table mb-0 history-table">
              <thead>
                <tr>
                  <th style="width: 30%;">Phương án</th>
                  <th style="width: 15%;">Trạng thái</th>
                  <th>Lý do loại trừ</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>
      </section>
    `;
  }

  function renderDecisionDetail(record) {
    const els = getEls();
    if (!els.detailContent) return;

    const meta = getDomainMeta(record.domain);
    const top = record.topItem;
    const topScore = top ? (top.total_score ?? top.score ?? 0) : null;
    const weights = extractWeightsMap(record);
    const inputJsonPretty = JSON.stringify(record.input_snapshot || {}, null, 2);

    const rankedListHtml =
      record.rankedItems.length > 0
        ? `<div class="history-ranked-list">
             ${record.rankedItems.map((opt, idx) => renderRankedOptionCard(opt, idx, weights)).join("")}
           </div>`
        : `<div class="dh-empty-state py-4">
             <div class="dh-empty-icon">⚠️</div>
             <div class="dh-empty-title">Không có phương án nào đạt điều kiện</div>
             <p class="dh-empty-desc mb-0">
               ${safeHtml(record.result_snapshot.message || "Tất cả ứng viên đều bị loại ở bước lọc điều kiện bắt buộc.")}
             </p>
           </div>`;

    els.detailContent.innerHTML = `
      <!-- 1. Thông tin chung của phiên quyết định -->
      <section class="dh-card history-detail-header-card mb-4">
        <div class="dh-card-body d-flex flex-wrap align-items-center justify-content-between gap-3">
          <div>
            <div class="d-flex flex-wrap align-items-center gap-2 mb-2">
              <span class="history-domain-badge ${meta.badgeClass}">
                <span aria-hidden="true">${meta.icon}</span>
                <span>${safeHtml(meta.label)}</span>
              </span>
              <span class="history-decision-id">Mã quyết định #${safeHtml(record.id)}</span>
              <span class="dh-status dh-status-success">Mô hình WSM</span>
            </div>
            <h2 class="dh-section-title mb-1">
              ${top ? `Đề xuất tối ưu: ${safeHtml(top.name)}` : "Phiên quyết định không có phương án thỏa mãn"}
            </h2>
            <div class="dh-muted dh-small">
              🕒 Thời gian thực hiện: <strong>${safeHtml(formatTime(record.created_at))}</strong>
              ${record.result_snapshot.message ? ` · ${safeHtml(record.result_snapshot.message)}` : ""}
            </div>
          </div>
        </div>
      </section>

      <!-- 2. Ba thẻ thống kê tổng quan -->
      <section class="row g-3 mb-4" aria-label="Tổng quan quyết định">
        <div class="col-12 col-md-4">
          <div class="dh-card history-stat-card h-100">
            <div class="dh-card-body">
              <div class="history-stat-label">Kết quả đứng đầu (Top 1)</div>
              <p class="history-stat-value">${safeHtml(top ? top.name : "Không có")}</p>
              <p class="history-stat-hint">
                ${top ? `Đạt ${safeHtml(formatScore(topScore))}/100 điểm WSM` : "Không có ứng viên vượt qua bộ lọc"}
              </p>
            </div>
          </div>
        </div>
        <div class="col-12 col-md-4">
          <div class="dh-card history-stat-card h-100">
            <div class="dh-card-body">
              <div class="history-stat-label">Số phương án được xếp hạng</div>
              <p class="history-stat-value">${safeHtml(record.totalValid)}</p>
              <p class="history-stat-hint">Thỏa mãn toàn bộ điều kiện bắt buộc</p>
            </div>
          </div>
        </div>
        <div class="col-12 col-md-4">
          <div class="dh-card history-stat-card h-100">
            <div class="dh-card-body">
              <div class="history-stat-label">Số phương án bị loại</div>
              <p class="history-stat-value">${safeHtml(record.totalExcluded)}</p>
              <p class="history-stat-hint">Vi phạm ngân sách hoặc ràng buộc cứng</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 3. Tiêu chí đầu vào & Input Snapshot -->
      <section class="dh-card mb-4" aria-labelledby="detail-input-title">
        <div class="dh-card-header">
          <div>
            <h2 class="dh-section-title mb-0" id="detail-input-title" style="font-size:16px;">
              Tiêu chí đầu vào đã sử dụng (Input Snapshot)
            </h2>
            <small class="dh-muted">Toàn bộ điều kiện lọc và trọng số tại thời điểm thực hiện đề xuất</small>
          </div>
        </div>
        <div class="dh-card-body">
          <div class="history-input-grid">
            ${renderDetailInputGrid(record)}
          </div>

          <details class="history-snapshot-details">
            <summary>Xem dữ liệu Input Snapshot gốc (JSON)</summary>
            <pre class="history-snapshot-pre"><code>${safeHtml(inputJsonPretty)}</code></pre>
          </details>
        </div>
      </section>

      <!-- 4. Danh sách kết quả được xếp hạng -->
      <section class="dh-card" aria-labelledby="detail-ranking-title">
        <div class="dh-card-header">
          <div>
            <h2 class="dh-section-title mb-0" id="detail-ranking-title" style="font-size:16px;">
              Bảng xếp hạng kết quả đề xuất (${safeHtml(record.rankedItems.length)})
            </h2>
            <small class="dh-muted">Xếp hạng theo điểm tổng WSM giảm dần kèm giải thích chi tiết</small>
          </div>
        </div>
        <div class="dh-card-body">
          ${rankedListHtml}
        </div>
      </section>

      <!-- 5. Danh sách phương án bị loại (nếu có) -->
      ${renderExcludedSection(record)}
    `;

    els.detailContent.classList.remove("d-none");
  }

  // ---------- Điều phối chuyển đổi View (List <-> Detail) ----------

  function switchViewMode(mode) {
    state.currentView = mode;
    const els = getEls();

    if (mode === "detail") {
      if (els.listView) els.listView.classList.add("d-none");
      if (els.detailView) els.detailView.classList.remove("d-none");
      if (els.btnBackToList) els.btnBackToList.classList.remove("d-none");
      if (els.pageTitle) els.pageTitle.textContent = "Chi tiết quyết định";
      if (els.pageDesc) {
        els.pageDesc.textContent =
          "Thông tin chi tiết tiêu chí đầu vào (Input Snapshot), điểm số WSM và lý do đề xuất của phiên quyết định.";
      }
    } else {
      if (els.detailView) els.detailView.classList.add("d-none");
      if (els.listView) els.listView.classList.remove("d-none");
      if (els.btnBackToList) els.btnBackToList.classList.add("d-none");
      if (els.pageTitle) els.pageTitle.textContent = "Lịch sử quyết định";
      if (els.pageDesc) {
        els.pageDesc.textContent =
          "Xem lại danh sách các phiên gợi ý đã lưu của tài khoản đang đăng nhập, tiêu chí đầu vào và bảng xếp hạng chi tiết.";
      }
    }
  }

  function showAuthRequiredState() {
    const els = getEls();
    if (els.loadingBox) els.loadingBox.classList.add("d-none");
    if (els.errorBox) els.errorBox.classList.add("d-none");
    if (els.emptyBox) els.emptyBox.classList.add("d-none");
    if (els.cardsContainer) els.cardsContainer.classList.add("d-none");
    if (els.paginationBar) els.paginationBar.classList.add("d-none");
    if (els.listView) els.listView.classList.add("d-none");
    if (els.detailView) els.detailView.classList.add("d-none");
    if (els.authRequired) els.authRequired.classList.remove("d-none");
  }

  // ---------- Luồng tải dữ liệu chính ----------

  async function loadHistoryList(options = {}) {
    const els = getEls();
    if (options.offset !== undefined) {
      state.offset = Math.max(0, Number(options.offset) || 0);
    }

    switchViewMode("list");

    if (!api.session.isLoggedIn()) {
      showAuthRequiredState();
      return;
    }

    if (els.authRequired) els.authRequired.classList.add("d-none");
    if (els.errorBox) els.errorBox.classList.add("d-none");
    if (els.emptyBox) els.emptyBox.classList.add("d-none");
    if (els.cardsContainer) els.cardsContainer.classList.add("d-none");
    if (els.paginationBar) els.paginationBar.classList.add("d-none");
    if (els.loadingBox) els.loadingBox.classList.remove("d-none");

    try {
      const response = await fetchHistoryList(state.limit, state.offset);
      const rawList = Array.isArray(response.data)
        ? response.data
        : Array.isArray(response.items)
          ? response.items
          : [];

      state.items = rawList.map(normalizeRecord).filter(Boolean);
      state.total =
        response.total !== undefined && response.total !== null
          ? Number(response.total)
          : state.items.length;

      renderHistoryList();
    } catch (error) {
      if (els.loadingBox) els.loadingBox.classList.add("d-none");

      if (error && error.status === 401) {
        showAuthRequiredState();
        return;
      }

      const msg = extractErrorMessage(
        error,
        "Không thể tải danh sách lịch sử quyết định từ máy chủ. Vui lòng thử lại.",
      );
      if (els.errorMessage) els.errorMessage.textContent = msg;
      if (els.errorBox) els.errorBox.classList.remove("d-none");
    }
  }

  async function openDecisionDetail(decisionId, pushUrl = true) {
    const els = getEls();
    const numericId = Number(decisionId);
    state.activeDecisionId = decisionId;

    if (pushUrl && window.history && typeof window.history.pushState === "function") {
      const url = new URL(window.location.href);
      url.searchParams.set("id", String(decisionId));
      window.history.pushState({ decisionId }, "", url.toString());
    }

    switchViewMode("detail");

    if (!api.session.isLoggedIn()) {
      showAuthRequiredState();
      return;
    }

    if (els.authRequired) els.authRequired.classList.add("d-none");
    if (els.detailNotFound) els.detailNotFound.classList.add("d-none");
    if (els.detailError) els.detailError.classList.add("d-none");
    if (els.detailContent) {
      els.detailContent.innerHTML = "";
      els.detailContent.classList.add("d-none");
    }

    if (!decisionId || Number.isNaN(numericId) || numericId <= 0) {
      if (els.detailNotFoundText) {
        els.detailNotFoundText.textContent = `Mã quyết định "${decisionId}" không hợp lệ hoặc không tồn tại.`;
      }
      if (els.detailNotFound) els.detailNotFound.classList.remove("d-none");
      return;
    }

    if (els.detailLoading) els.detailLoading.classList.remove("d-none");

    try {
      const response = await fetchHistoryDetail(numericId);
      const record = normalizeRecord(response);
      if (els.detailLoading) els.detailLoading.classList.add("d-none");

      if (!record || !record.id) {
        if (els.detailNotFound) els.detailNotFound.classList.remove("d-none");
        return;
      }

      state.activeDecision = record;
      renderDecisionDetail(record);
    } catch (error) {
      if (els.detailLoading) els.detailLoading.classList.add("d-none");

      if (error && error.status === 401) {
        showAuthRequiredState();
        return;
      }

      if (error && error.status === 404) {
        const notFoundMsg = extractErrorMessage(
          error,
          `Quyết định với mã #${numericId} không tồn tại hoặc không thuộc về tài khoản của bạn.`,
        );
        if (els.detailNotFoundText) els.detailNotFoundText.textContent = notFoundMsg;
        if (els.detailNotFound) els.detailNotFound.classList.remove("d-none");
        return;
      }

      const errMsg = extractErrorMessage(
        error,
        "Không thể tải chi tiết quyết định. Vui lòng kiểm tra kết nối và thử lại.",
      );
      if (els.detailErrorText) els.detailErrorText.textContent = errMsg;
      if (els.detailError) els.detailError.classList.remove("d-none");
    }
  }

  function backToHistoryList(pushUrl = true) {
    state.activeDecisionId = null;
    state.activeDecision = null;

    if (pushUrl && window.history && typeof window.history.pushState === "function") {
      const url = new URL(window.location.href);
      url.searchParams.delete("id");
      window.history.pushState({}, "", url.toString());
    }

    if (state.items.length > 0) {
      switchViewMode("list");
      renderHistoryList();
    } else {
      loadHistoryList({ offset: 0 });
    }
  }

  // ---------- Gắn sự kiện giao diện ----------

  function setFilter(filterType) {
    state.currentFilter = filterType || "all";
    const els = getEls();
    if (els.filterChips) {
      els.filterChips.querySelectorAll(".dh-chip").forEach((chip) => {
        const isActive = (chip.dataset.type || "all") === state.currentFilter;
        chip.classList.toggle("active", isActive);
        chip.setAttribute("aria-pressed", String(isActive));
      });
    }
    renderHistoryList();
  }

  function initSidebarToggle() {
    const sidebar = document.querySelector(".dh-sidebar");
    const toggle = document.querySelector("[data-sidebar-toggle]");
    if (!sidebar || !toggle) return;

    toggle.addEventListener("click", () => {
      const isOpen = sidebar.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(isOpen));
    });

    document.addEventListener("click", (event) => {
      if (event.target.closest(".dh-sidebar, [data-sidebar-toggle]")) return;
      sidebar.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  }

  function bindEvents() {
    const els = getEls();

    if (els.filterChips) {
      els.filterChips.addEventListener("click", (event) => {
        const chip = event.target.closest(".dh-chip");
        if (!chip) return;
        setFilter(chip.dataset.type || "all");
      });
    }

    if (els.btnResetFilter) {
      els.btnResetFilter.addEventListener("click", () => setFilter("all"));
    }

    if (els.cardsContainer) {
      els.cardsContainer.addEventListener("click", (event) => {
        const btn = event.target.closest("[data-action='view-detail']");
        if (!btn) return;
        const decisionId = btn.dataset.decisionId;
        if (decisionId) {
          openDecisionDetail(decisionId, true);
        }
      });
    }

    if (els.btnReload) {
      els.btnReload.addEventListener("click", () => {
        if (state.currentView === "detail" && state.activeDecisionId) {
          openDecisionDetail(state.activeDecisionId, false);
        } else {
          loadHistoryList();
        }
      });
    }

    if (els.btnRetryHistory) {
      els.btnRetryHistory.addEventListener("click", () => loadHistoryList());
    }

    if (els.btnBackToList) {
      els.btnBackToList.addEventListener("click", () => backToHistoryList(true));
    }
    if (els.btnNotFoundBack) {
      els.btnNotFoundBack.addEventListener("click", () => backToHistoryList(true));
    }
    if (els.btnErrorBack) {
      els.btnErrorBack.addEventListener("click", () => backToHistoryList(true));
    }
    if (els.btnRetryDetail) {
      els.btnRetryDetail.addEventListener("click", () => {
        if (state.activeDecisionId) {
          openDecisionDetail(state.activeDecisionId, false);
        }
      });
    }

    if (els.btnPrevPage) {
      els.btnPrevPage.addEventListener("click", () => {
        if (state.offset >= state.limit) {
          loadHistoryList({ offset: state.offset - state.limit });
        }
      });
    }

    if (els.btnNextPage) {
      els.btnNextPage.addEventListener("click", () => {
        if (state.offset + state.limit < state.total) {
          loadHistoryList({ offset: state.offset + state.limit });
        }
      });
    }

    window.addEventListener("popstate", () => {
      const params = new URLSearchParams(window.location.search);
      const idParam = params.get("id");
      if (idParam) {
        openDecisionDetail(idParam, false);
      } else {
        backToHistoryList(false);
      }
    });
  }

  function initHistoryPage() {
    initSidebarToggle();
    bindEvents();

    const params = new URLSearchParams(window.location.search);
    const initialId = params.get("id");
    if (initialId) {
      openDecisionDetail(initialId, false);
    } else {
      loadHistoryList({ offset: 0 });
    }
  }

  global.DHHistory = {
    state,
    normalizeRecord,
    loadHistoryList,
    openDecisionDetail,
    backToHistoryList,
    setFilter,
    initHistoryPage,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initHistoryPage);
  } else {
    initHistoryPage();
  }
})(window);
