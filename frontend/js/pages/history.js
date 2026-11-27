// ==========================================================
// Module: Decision History (Lịch sử quyết định)
// Tích hợp trực tiếp với Backend API:
//   - GET /decisions/history?limit=...&offset=...
//   - GET /decisions/history/{decision_id}
// Hiển thị chi tiết quyết định trong Modal lớn căn giữa màn hình
// (Light Theme, overlay xám nhẹ + blur, khóa/khôi phục scroll nền).
// ==========================================================

(function (global) {
  const DEFAULT_PAGE_LIMIT = 10;

  const DOMAIN_CONFIG = {
    food: {
      icon: "🍲",
      label: "Gợi ý Món ăn",
      domainLabel: "Ẩm thực (Food)",
      shortLabel: "Món ăn (Food)",
      badgeClass: "history-badge-food",
    },
    travel: {
      icon: "✈️",
      label: "Gợi ý Du lịch",
      domainLabel: "Du lịch (Travel)",
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

  const EXTRA_INPUT_FIELD_LABELS = {
    cuisine: "Ẩm thực",
    category: "Danh mục",
    spicy_level: "Độ cay",
    calories_max: "Calo tối đa",
    distance_max: "Khoảng cách tối đa",
    occasion: "Dịp ăn uống",
  };

  const state = {
    items: [],
    total: 0,
    limit: DEFAULT_PAGE_LIMIT,
    offset: 0,
    currentFilter: "all",
    currentView: "list", // "list" | "detail"
    isModalOpen: false,
    savedScrollY: 0,
    detailRequestSeq: 0,
    lastFocusedTrigger: null,
    hasLoadedListOnce: false,
    activeListPromise: null,
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

  function hasValidNumber(value) {
    return (
      value !== null &&
      value !== undefined &&
      value !== "" &&
      typeof value !== "boolean" &&
      !Number.isNaN(Number(value))
    );
  }

  function formatVnd(value) {
    if (!hasValidNumber(value)) return "–";
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
    if (!hasValidNumber(value)) return null;
    return Number(value).toLocaleString("vi-VN", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    });
  }

  function formatPercent(weight) {
    if (!hasValidNumber(weight)) return "–";
    return Math.round(Number(weight) * 100) + "%";
  }

  function getDomainMeta(domain) {
    const key = String(domain || "food").toLowerCase();
    return (
      DOMAIN_CONFIG[key] || {
        icon: "📋",
        label: `Quyết định (${domain || "Khác"})`,
        domainLabel: String(domain || "Khác"),
        shortLabel: String(domain || "Khác"),
        badgeClass: "history-badge-food",
      }
    );
  }

  function getMealLabel(mealType) {
    if (!mealType) return "Tất cả bữa ăn";
    return MEAL_TYPE_LABELS[mealType] || String(mealType);
  }

  function extractErrorMessage(error, fallbackMessage) {
    if (!error) return fallbackMessage;
    if (error.data && typeof error.data.message === "string" && error.data.message.trim()) {
      return error.data.message.trim();
    }
    if (error.data && typeof error.data.detail === "string" && error.data.detail.trim()) {
      return error.data.detail.trim();
    }
    if (
      typeof error.message === "string" &&
      error.message.trim() &&
      !/^Lỗi \d+$/.test(error.message.trim())
    ) {
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

      // Modal Chi tiết quyết định
      detailModal: document.getElementById("history-detail-modal"),
      detailView: document.getElementById("history-detail-view"),
      modalSubtitle: document.getElementById("history-modal-subtitle"),
      modalBody: document.getElementById("history-modal-body"),
      btnCloseModal: document.getElementById("btn-close-detail-modal"),
      btnFooterCloseModal: document.getElementById("btn-footer-close-modal"),

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

  // ---------- Quản lý Khóa / Khôi phục Scroll của trang nền ----------

  function getCurrentScrollY() {
    if (typeof window.scrollY === "number") return window.scrollY;
    if (typeof window.pageYOffset === "number") return window.pageYOffset;
    if (document.documentElement && typeof document.documentElement.scrollTop === "number") {
      return document.documentElement.scrollTop;
    }
    return 0;
  }

  function lockBackgroundScroll() {
    if (!state.isModalOpen) {
      state.savedScrollY = getCurrentScrollY();
    }
    const body = document.body;
    if (!body) return;

    const docEl = document.documentElement;
    const scrollbarWidth =
      docEl && typeof window.innerWidth === "number" && typeof docEl.clientWidth === "number"
        ? Math.max(0, window.innerWidth - docEl.clientWidth)
        : 0;

    if (body.style && scrollbarWidth > 0) {
      body.style.paddingRight = `${scrollbarWidth}px`;
    }
    if (body.classList) {
      body.classList.add("history-modal-open");
    }
  }

  function unlockBackgroundScroll() {
    const body = document.body;
    if (body) {
      if (body.classList) {
        body.classList.remove("history-modal-open");
      }
      if (body.style) {
        body.style.paddingRight = "";
      }
    }
    if (typeof window.scrollTo === "function") {
      window.scrollTo(0, state.savedScrollY || 0);
    }
  }

  function showDetailModalShell() {
    const els = getEls();
    lockBackgroundScroll();
    state.isModalOpen = true;
    state.currentView = "detail";

    if (els.detailModal) {
      els.detailModal.classList.remove("d-none");
      els.detailModal.setAttribute("aria-hidden", "false");
      // Kích hoạt reflow để hiệu ứng CSS fade + scale mượt mà
      if (typeof els.detailModal.offsetWidth === "number") {
        void els.detailModal.offsetWidth;
      }
      els.detailModal.classList.add("is-open");
    }

    if (els.modalBody && typeof els.modalBody.scrollTop === "number") {
      els.modalBody.scrollTop = 0;
    }
  }

  function closeDecisionModal(options = {}) {
    const updateUrl = options.updateUrl !== false;
    const els = getEls();

    state.detailRequestSeq += 1;
    state.isModalOpen = false;
    state.currentView = "list";
    state.activeDecisionId = null;
    state.activeDecision = null;

    if (els.detailModal) {
      els.detailModal.classList.remove("is-open");
      els.detailModal.classList.add("d-none");
      els.detailModal.setAttribute("aria-hidden", "true");
    }

    unlockBackgroundScroll();

    if (updateUrl && window.history && typeof window.history.replaceState === "function") {
      try {
        const url = new URL(window.location.href);
        if (url.searchParams.has("id")) {
          url.searchParams.delete("id");
          window.history.replaceState({}, "", url.toString());
        }
      } catch (_err) {
        // Bỏ qua nếu môi trường test không dùng URL đầy đủ
      }
    }

    if (state.lastFocusedTrigger && typeof state.lastFocusedTrigger.focus === "function") {
      try {
        state.lastFocusedTrigger.focus({ preventScroll: true });
      } catch (_err) {
        state.lastFocusedTrigger.focus();
      }
    }
    state.lastFocusedTrigger = null;

    if (!state.hasLoadedListOnce && !state.activeListPromise) {
      loadHistoryList({ offset: state.offset });
    }
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

  function sortRankedItems(rawItems) {
    if (!Array.isArray(rawItems)) return [];
    return rawItems
      .map((item, idx) => ({ item, idx }))
      .sort((a, b) => {
        const rankA = hasValidNumber(a.item && a.item.rank) ? Number(a.item.rank) : a.idx + 1;
        const rankB = hasValidNumber(b.item && b.item.rank) ? Number(b.item.rank) : b.idx + 1;
        return rankA - rankB;
      })
      .map((entry) => entry.item);
  }

  function resolveSelectedOption(rankedItems, inputSnapshot, resultSnapshot) {
    if (!Array.isArray(rankedItems) || rankedItems.length === 0) {
      return { option: null, isExplicitChoice: false };
    }

    const explicitByFlag = rankedItems.find(
      (opt) => opt && (opt.is_selected === true || opt.selected === true || opt.chosen === true),
    );
    if (explicitByFlag) {
      return { option: explicitByFlag, isExplicitChoice: true };
    }

    const chosenId =
      (resultSnapshot &&
        (resultSnapshot.selected_food_id ??
          resultSnapshot.selected_item_id ??
          resultSnapshot.chosen_id)) ??
      (inputSnapshot &&
        (inputSnapshot.selected_food_id ?? inputSnapshot.selected_item_id));

    if (chosenId !== undefined && chosenId !== null && chosenId !== "") {
      const matched = rankedItems.find((opt) => {
        if (!opt) return false;
        const optId = opt.food_id ?? opt.destination_id ?? opt.id;
        return optId !== undefined && String(optId) === String(chosenId);
      });
      if (matched) {
        return { option: matched, isExplicitChoice: true };
      }
    }

    return { option: rankedItems[0], isExplicitChoice: false };
  }

  function normalizeRecord(raw) {
    if (!raw || typeof raw !== "object") return null;
    const item =
      raw.data && typeof raw.data === "object" && !Array.isArray(raw.data) ? raw.data : raw;
    const input =
      item.input_snapshot && typeof item.input_snapshot === "object" ? item.input_snapshot : {};
    const result =
      item.result_snapshot && typeof item.result_snapshot === "object" ? item.result_snapshot : {};
    const rankedItems = sortRankedItems(Array.isArray(result.items) ? result.items : []);
    const excludedItems = Array.isArray(result.excluded_items) ? result.excluded_items : [];
    const { option: featuredItem, isExplicitChoice } = resolveSelectedOption(
      rankedItems,
      input,
      result,
    );

    return {
      id: item.id,
      user_id: item.user_id,
      domain: String(item.domain || "food").toLowerCase(),
      created_at: item.created_at,
      input_snapshot: input,
      result_snapshot: result,
      rankedItems,
      excludedItems,
      topItem: featuredItem,
      featuredItem,
      isExplicitChoice,
      totalValid: result.total !== undefined ? Number(result.total) : rankedItems.length,
      totalExcluded:
        result.total_excluded !== undefined ? Number(result.total_excluded) : excludedItems.length,
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
        pills.push(
          `<span class="history-spec-pill">Khu vực: <strong>${safeHtml(input.region)}</strong></span>`,
        );
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

  // ---------- Render Danh sách lịch sử (Giữ nguyên bố cục danh sách) ----------

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
    const topScoreText = top ? formatScore(top.total_score ?? top.score) : null;
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
          ${
            topScoreText !== null
              ? `<div class="history-highlight-score" aria-label="Điểm WSM">
                   <span class="history-highlight-score-val">${safeHtml(topScoreText)}</span>
                   <span class="history-highlight-score-unit">/ 100 WSM</span>
                 </div>`
              : ""
          }
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
            <span class="history-decision-id">Quyết định #${safeHtml(record.id)}</span>
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
                aria-label="Xem lại chi tiết quyết định #${safeHtml(record.id)}"
              >
                Xem lại
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
    if (els.listView) els.listView.classList.remove("d-none");

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
        els.emptyTitle.textContent =
          state.currentFilter === "food"
            ? "Bạn chưa có quyết định món ăn nào."
            : `Không có quyết định thuộc phân hệ ${meta.shortLabel}`;
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

  // ---------- Render Nội dung Modal Chi tiết quyết định ----------

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

  function getOptionImageUrl(option) {
    if (!option || typeof option !== "object") return null;
    const rawUrl = option.image_url ?? option.image ?? option.thumbnail ?? null;
    if (typeof rawUrl === "string" && rawUrl.trim()) {
      return rawUrl.trim();
    }
    return null;
  }

  function renderOptionMedia(option, domain, wrapperClass) {
    const meta = getDomainMeta(domain);
    const imgUrl = getOptionImageUrl(option);
    if (imgUrl) {
      return `
        <div class="${wrapperClass}" data-fallback-icon="${safeHtml(meta.icon)}">
          <img
            src="${safeHtml(imgUrl)}"
            alt="${safeHtml((option && option.name) || "Hình ảnh đề xuất")}"
            class="history-dish-img"
            loading="lazy"
            data-dish-img="true"
          >
        </div>
      `;
    }
    return `
      <div class="${wrapperClass}">
        <span class="history-dish-fallback-icon" aria-hidden="true">${meta.icon}</span>
      </div>
    `;
  }

  function buildOptionSpecPills(option) {
    if (!option || typeof option !== "object") return "";
    const specs = [];
    const tags = Array.isArray(option.tags) ? option.tags.filter(Boolean) : [];

    if (hasValidNumber(option.price)) {
      specs.push(
        `<span class="history-spec-pill">Giá: <strong>${safeHtml(formatVnd(option.price))}</strong></span>`,
      );
    }
    if (hasValidNumber(option.estimated_cost)) {
      specs.push(
        `<span class="history-spec-pill">Chi phí: <strong>${safeHtml(formatVnd(option.estimated_cost))}</strong></span>`,
      );
    }
    if (hasValidNumber(option.prep_time)) {
      specs.push(
        `<span class="history-spec-pill">Chuẩn bị: <strong>${safeHtml(option.prep_time)} phút</strong></span>`,
      );
    }
    if (hasValidNumber(option.estimated_duration)) {
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
    return specs.join("");
  }

  function renderOptionCriteriaBreakdown(option, fallbackWeights) {
    if (!option || typeof option !== "object") return "";
    const details =
      option.criteria_details && typeof option.criteria_details === "object"
        ? option.criteria_details
        : null;
    const scores =
      option.criteria_scores && typeof option.criteria_scores === "object"
        ? option.criteria_scores
        : null;

    const keys = details ? Object.keys(details) : scores ? Object.keys(scores) : [];
    if (keys.length === 0) return "";

    const bars = keys
      .map((key) => {
        const detailObj = details && details[key] ? details[key] : {};
        const rawScore =
          detailObj.normalized_score !== undefined && detailObj.normalized_score !== null
            ? detailObj.normalized_score
            : scores && scores[key] !== undefined
              ? scores[key]
              : null;
        if (!hasValidNumber(rawScore)) return "";

        const scoreVal = Number(rawScore);
        const weightVal =
          detailObj.weight !== undefined
            ? detailObj.weight
            : fallbackWeights && fallbackWeights[key] !== undefined
              ? fallbackWeights[key]
              : null;
        const contributionVal = hasValidNumber(detailObj.contribution)
          ? Number(detailObj.contribution)
          : null;

        const label = CRITERION_LABELS[key] || key;
        const weightText = hasValidNumber(weightVal) ? ` · trọng số ${formatPercent(weightVal)}` : "";
        const contribText =
          contributionVal !== null ? ` (+${formatScore(contributionVal)}đ)` : "";

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
      .filter(Boolean)
      .join("");

    if (!bars) return "";

    return `
      <div class="history-criteria-breakdown">
        <div class="dh-small fw-bold dh-muted mb-2">Điểm đánh giá theo từng tiêu chí</div>
        <div class="dh-criteria-group mb-0">${bars}</div>
      </div>
    `;
  }

  function renderFeaturedSection(record) {
    const featured = record.featuredItem;
    const isFood = record.domain !== "travel";
    const sectionTitle = isFood ? "Món ăn đề xuất nổi bật" : "Địa điểm đề xuất nổi bật";

    if (!featured) {
      return `
        <section class="history-modal-section" aria-label="${safeHtml(sectionTitle)}">
          <div class="history-modal-section-head">
            <h3 class="history-modal-section-title">
              <span aria-hidden="true">🍽️</span>
              <span>${safeHtml(sectionTitle)}</span>
            </h3>
          </div>
          <div class="history-featured-card is-empty-result">
            <div class="history-featured-media">
              <span class="history-dish-fallback-icon" aria-hidden="true">⚠️</span>
            </div>
            <div class="history-featured-info">
              <h4 class="history-featured-name">Không có phương án phù hợp</h4>
              <p class="history-featured-desc mb-0">
                ${safeHtml(
                  record.result_snapshot.message ||
                    "Tất cả ứng viên đều bị loại do không đáp ứng các điều kiện lọc bắt buộc.",
                )}
              </p>
            </div>
          </div>
        </section>
      `;
    }

    const rank = hasValidNumber(featured.rank) ? Number(featured.rank) : 1;
    const scoreText = formatScore(featured.total_score ?? featured.score);
    const descText =
      typeof featured.description === "string" && featured.description.trim()
        ? featured.description.trim()
        : typeof featured.summary === "string" && featured.summary.trim()
          ? featured.summary.trim()
          : "";
    const specsHtml = buildOptionSpecPills(featured);

    const statusBadgeText = record.isExplicitChoice
      ? "✓ Món đã lựa chọn"
      : rank === 1
        ? "★ Đề xuất tối ưu nhất"
        : "★ Phương án nổi bật";

    return `
      <section class="history-modal-section" aria-label="${safeHtml(sectionTitle)}">
        <div class="history-modal-section-head">
          <h3 class="history-modal-section-title">
            <span aria-hidden="true">★</span>
            <span>${safeHtml(sectionTitle)}</span>
          </h3>
          <span class="history-modal-section-sub">Kết quả phù hợp nhất trong phiên đề xuất</span>
        </div>

        <div class="history-featured-card">
          ${renderOptionMedia(featured, record.domain, "history-featured-media")}

          <div class="history-featured-info">
            <div class="history-featured-badges">
              <span class="history-selected-pill">${safeHtml(statusBadgeText)}</span>
              <span class="history-rank-pill-soft">Hạng #${safeHtml(rank)}</span>
            </div>
            <h4 class="history-featured-name">${safeHtml(featured.name || "Món ăn đề xuất")}</h4>
            ${descText ? `<p class="history-featured-desc">${safeHtml(descText)}</p>` : ""}
            ${specsHtml ? `<div class="history-specs-list">${specsHtml}</div>` : ""}
          </div>

          ${
            scoreText !== null
              ? `<div class="history-featured-score" aria-label="Điểm phù hợp ${safeHtml(scoreText)} trên 100">
                   <span class="history-featured-score-num">${safeHtml(scoreText)}</span>
                   <span class="history-featured-score-label">/ 100 điểm WSM</span>
                 </div>`
              : ""
          }
        </div>
      </section>
    `;
  }

  function renderReasonsSection(record, weights) {
    const featured = record.featuredItem;
    if (!featured) return "";

    const reasons = Array.isArray(featured.reasons)
      ? featured.reasons.map((r) => String(r || "").trim()).filter(Boolean)
      : [];
    const criteriaHtml = renderOptionCriteriaBreakdown(featured, weights);

    if (reasons.length === 0 && !criteriaHtml) {
      return "";
    }

    const reasonsListHtml =
      reasons.length > 0
        ? `<ul class="history-reasons-list">
             ${reasons
               .map(
                 (reason) => `
                   <li class="history-reasons-item">
                     <span class="history-reasons-bullet" aria-hidden="true">✓</span>
                     <span>${safeHtml(reason)}</span>
                   </li>`,
               )
               .join("")}
           </ul>`
        : `<p class="dh-muted dh-small mb-0">
             Món ăn đạt điểm tổng hợp cao nhất dựa trên các tiêu chí đầu vào của phiên đề xuất.
           </p>`;

    return `
      <section class="history-modal-section" aria-label="Lý do đề xuất">
        <div class="history-modal-section-head">
          <h3 class="history-modal-section-title">
            <span aria-hidden="true">💡</span>
            <span>Lý do đề xuất</span>
          </h3>
          <span class="history-modal-section-sub">Các yếu tố giúp phương án phù hợp với yêu cầu của bạn</span>
        </div>

        <div class="history-reasons-panel">
          ${reasonsListHtml}
          ${criteriaHtml}
        </div>
      </section>
    `;
  }

  function renderDetailInputGrid(record) {
    const input = record.input_snapshot || {};
    const handledKeys = new Set([
      "budget_max",
      "budget",
      "people_count",
      "num_people",
      "servings",
      "party_size",
      "meal_type",
      "max_prep_time",
      "excluded_ingredients",
      "preferred_tags",
      "special_requirements",
      "special_request",
      "dietary_restrictions",
      "notes",
      "note",
      "region",
      "max_duration",
      "activity_type",
      "preferred_highlights",
      "limit",
      "weights",
      "scoring",
      "selected_food_id",
      "selected_item_id",
    ]);

    const fields = [];

    const budgetVal = input.budget_max ?? input.budget;
    if (hasValidNumber(budgetVal)) {
      fields.push({
        label: "Ngân sách tối đa",
        value: formatVnd(budgetVal),
      });
    }

    const peopleVal =
      input.people_count ?? input.num_people ?? input.servings ?? input.party_size;
    if (hasValidNumber(peopleVal) && Number(peopleVal) > 0) {
      fields.push({
        label: "Số người ăn",
        value: `${Number(peopleVal)} người`,
      });
    }

    if (record.domain === "travel") {
      if (input.region) {
        fields.push({ label: "Khu vực", value: String(input.region) });
      }
      if (hasValidNumber(input.max_duration)) {
        fields.push({ label: "Thời lượng tối đa", value: `≤ ${input.max_duration} giờ` });
      }
      if (input.activity_type) {
        fields.push({ label: "Loại hình trải nghiệm", value: String(input.activity_type) });
      }
      if (Array.isArray(input.preferred_highlights) && input.preferred_highlights.length > 0) {
        fields.push({
          label: "Điểm nổi bật ưu tiên",
          value: input.preferred_highlights.join(", "),
        });
      }
    } else {
      if ("meal_type" in input) {
        fields.push({
          label: "Bữa ăn",
          value: getMealLabel(input.meal_type),
        });
      }
      if (hasValidNumber(input.max_prep_time)) {
        fields.push({
          label: "Thời gian chuẩn bị tối đa",
          value: `≤ ${input.max_prep_time} phút`,
        });
      }
      if (Array.isArray(input.preferred_tags) && input.preferred_tags.length > 0) {
        fields.push({
          label: "Tiêu chí / Khẩu vị lựa chọn",
          value: input.preferred_tags.join(", "),
        });
      }
      if (Array.isArray(input.excluded_ingredients) && input.excluded_ingredients.length > 0) {
        fields.push({
          label: "Nguyên liệu kiêng / tránh",
          value: input.excluded_ingredients.join(", "),
        });
      }
    }

    const specialReq =
      input.special_requirements ??
      input.special_request ??
      input.dietary_restrictions ??
      input.notes ??
      input.note;
    if (Array.isArray(specialReq) && specialReq.length > 0) {
      fields.push({
        label: "Yêu cầu đặc biệt",
        value: specialReq.join(", "),
      });
    } else if (typeof specialReq === "string" && specialReq.trim()) {
      fields.push({
        label: "Yêu cầu đặc biệt",
        value: specialReq.trim(),
      });
    }

    const limitVal = input.limit ?? record.result_snapshot.limit;
    if (hasValidNumber(limitVal)) {
      fields.push({
        label: "Số lượng gợi ý tối đa",
        value: `${Number(limitVal)} phương án`,
      });
    }

    const weights = extractWeightsMap(record);
    if (weights) {
      const weightParts = Object.entries(weights)
        .filter(([, v]) => hasValidNumber(v))
        .map(([k, v]) => `${CRITERION_LABELS[k] || k}: ${formatPercent(v)}`);
      if (weightParts.length > 0) {
        fields.push({
          label: "Trọng số chấm điểm (WSM)",
          value: weightParts.join(" · "),
        });
      }
    }

    // Hiển thị an toàn các trường đầu vào bổ sung khác nếu lịch sử có lưu
    Object.entries(input).forEach(([key, val]) => {
      if (handledKeys.has(key) || val === null || val === undefined || val === "") return;
      if (Array.isArray(val)) {
        if (val.length === 0) return;
        fields.push({
          label: EXTRA_INPUT_FIELD_LABELS[key] || key,
          value: val.join(", "),
        });
      } else if (typeof val === "string" || typeof val === "number" || typeof val === "boolean") {
        fields.push({
          label: EXTRA_INPUT_FIELD_LABELS[key] || key,
          value: typeof val === "boolean" ? (val ? "Có" : "Không") : String(val),
        });
      }
    });

    if (fields.length === 0) {
      return `
        <div class="history-input-item">
          <span class="history-input-label">Tiêu chí đầu vào</span>
          <div class="history-input-val">Sử dụng cấu hình đề xuất mặc định</div>
        </div>
      `;
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

  function isSameOption(optA, optB) {
    if (!optA || !optB) return false;
    if (optA === optB) return true;
    const idA = optA.food_id ?? optA.destination_id ?? optA.id;
    const idB = optB.food_id ?? optB.destination_id ?? optB.id;
    if (idA !== undefined && idB !== undefined && idA !== null && idB !== null) {
      return String(idA) === String(idB);
    }
    return Boolean(optA.name && optA.name === optB.name);
  }

  function renderRankedOptionCard(option, idx, record) {
    const rank = hasValidNumber(option.rank) ? Number(option.rank) : idx + 1;
    const isFeatured = isSameOption(option, record.featuredItem);
    const isTop = isFeatured || rank === 1;
    const scoreText = formatScore(option.total_score ?? option.score);
    const specsHtml = buildOptionSpecPills(option);
    const reasons = Array.isArray(option.reasons)
      ? option.reasons.map((r) => String(r || "").trim()).filter(Boolean)
      : [];

    const chosenBadge = isFeatured
      ? `<span class="history-chosen-tag">${
          record.isExplicitChoice ? "✓ Món đã chọn" : "★ Đề xuất nổi bật"
        }</span>`
      : "";

    const secondaryReasonHtml =
      !isFeatured && reasons.length > 0
        ? `<p class="history-ranked-subreason">✓ ${safeHtml(reasons[0])}</p>`
        : "";

    return `
      <article class="history-ranked-card${isTop ? " is-top-rank" : ""}">
        <div class="history-ranked-row">
          <span class="history-rank-number" aria-label="Hạng ${safeHtml(rank)}">#${safeHtml(rank)}</span>
          ${renderOptionMedia(option, record.domain, "history-ranked-thumb")}

          <div class="history-ranked-main">
            <div class="history-ranked-title-row">
              <h4 class="history-ranked-title">${safeHtml(option.name || `Phương án #${idx + 1}`)}</h4>
              ${chosenBadge}
            </div>
            ${specsHtml ? `<div class="history-specs-list">${specsHtml}</div>` : ""}
          </div>

          ${
            scoreText !== null
              ? `<div class="history-ranked-score" aria-label="Điểm ${safeHtml(scoreText)}">
                   <span class="history-ranked-score-val">${safeHtml(scoreText)}</span>
                   <span class="history-ranked-score-unit">Điểm WSM</span>
                 </div>`
              : ""
          }
        </div>
        ${secondaryReasonHtml}
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
      <section class="history-modal-section" aria-label="Các phương án bị loại">
        <div class="history-excluded-card">
          <div class="history-excluded-header">
            <div>
              <h3 class="history-modal-section-title">
                <span>Phương án không thỏa điều kiện bắt buộc (${safeHtml(excluded.length)})</span>
              </h3>
            </div>
            <span class="dh-status dh-status-danger">${safeHtml(excluded.length)} bị loại</span>
          </div>
          <div class="table-responsive">
            <table class="table mb-0 history-table">
              <thead>
                <tr>
                  <th style="width: 32%;">Phương án</th>
                  <th style="width: 16%;">Trạng thái</th>
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
    const weights = extractWeightsMap(record);
    const inputJsonPretty = JSON.stringify(record.input_snapshot || {}, null, 2);
    const listSectionTitle =
      record.domain === "travel" ? "Danh sách địa điểm được đề xuất" : "Danh sách món được đề xuất";

    if (els.modalSubtitle) {
      els.modalSubtitle.textContent = `Quyết định #${record.id} · ${meta.domainLabel} · ${formatTime(record.created_at)}`;
    }

    const rankedSectionHtml =
      record.rankedItems.length > 0
        ? `
          <section class="history-modal-section" aria-label="${safeHtml(listSectionTitle)}">
            <div class="history-modal-section-head">
              <h3 class="history-modal-section-title">
                <span aria-hidden="true">📋</span>
                <span>${safeHtml(listSectionTitle)} (${safeHtml(record.rankedItems.length)})</span>
              </h3>
              <span class="history-modal-section-sub">Sắp xếp theo đúng thứ tự xếp hạng ban đầu</span>
            </div>
            <div class="history-ranked-list">
              ${record.rankedItems.map((opt, idx) => renderRankedOptionCard(opt, idx, record)).join("")}
            </div>
          </section>
        `
        : "";

    els.detailContent.innerHTML = `
      <!-- 1. Thông tin lần quyết định -->
      <div class="history-modal-meta-bar" aria-label="Thông tin lần quyết định">
        <div class="history-modal-meta-group">
          <span class="history-domain-badge ${meta.badgeClass}">
            <span aria-hidden="true">${meta.icon}</span>
            <span>${safeHtml(meta.domainLabel)}</span>
          </span>
          <span class="history-decision-id">Mã quyết định #${safeHtml(record.id)}</span>
          <span class="dh-status dh-status-success">${safeHtml(record.totalValid)} phù hợp</span>
          ${
            record.totalExcluded > 0
              ? `<span class="dh-status dh-status-danger">${safeHtml(record.totalExcluded)} bị loại</span>`
              : ""
          }
        </div>
        <div class="history-modal-meta-time">
          <span aria-hidden="true">🕒</span>
          <time datetime="${safeHtml(record.created_at)}">${safeHtml(formatTime(record.created_at))}</time>
        </div>
      </div>

      <!-- 2. Khu vực món ăn / phương án được lựa chọn nổi bật -->
      ${renderFeaturedSection(record)}

      <!-- 3. Lý do đề xuất -->
      ${renderReasonsSection(record, weights)}

      <!-- 4. Thông tin đầu vào -->
      <section class="history-modal-section" aria-label="Thông tin đầu vào">
        <div class="history-modal-section-head">
          <h3 class="history-modal-section-title">
            <span aria-hidden="true">🎯</span>
            <span>Thông tin đầu vào</span>
          </h3>
          <span class="history-modal-section-sub">Các tiêu chí đã sử dụng trong lần đề xuất này</span>
        </div>

        <div class="history-input-grid">
          ${renderDetailInputGrid(record)}
        </div>

        <details class="history-snapshot-details">
          <summary>Xem dữ liệu Input Snapshot gốc (JSON)</summary>
          <pre class="history-snapshot-pre"><code>${safeHtml(inputJsonPretty)}</code></pre>
        </details>
      </section>

      <!-- 5. Danh sách món được đề xuất -->
      ${rankedSectionHtml}

      <!-- 6. Phương án bị loại bởi ràng buộc cứng (nếu có) -->
      ${renderExcludedSection(record)}
    `;

    els.detailContent.classList.remove("d-none");
  }

  // ---------- Trạng thái chưa đăng nhập ----------

  function showAuthRequiredState() {
    const els = getEls();
    if (state.isModalOpen) {
      closeDecisionModal({ updateUrl: false });
    }
    if (els.loadingBox) els.loadingBox.classList.add("d-none");
    if (els.errorBox) els.errorBox.classList.add("d-none");
    if (els.emptyBox) els.emptyBox.classList.add("d-none");
    if (els.cardsContainer) els.cardsContainer.classList.add("d-none");
    if (els.paginationBar) els.paginationBar.classList.add("d-none");
    if (els.listView) els.listView.classList.add("d-none");
    if (els.authRequired) els.authRequired.classList.remove("d-none");
  }

  // ---------- Luồng tải dữ liệu Danh sách & Modal Chi tiết ----------

  function loadHistoryList(options = {}) {
    if (state.activeListPromise) {
      return state.activeListPromise;
    }

    const els = getEls();
    if (options.offset !== undefined) {
      state.offset = Math.max(0, Number(options.offset) || 0);
    }

    if (!api.session.isLoggedIn()) {
      showAuthRequiredState();
      return Promise.resolve();
    }

    if (els.listView) els.listView.classList.remove("d-none");
    if (els.authRequired) els.authRequired.classList.add("d-none");
    if (els.errorBox) els.errorBox.classList.add("d-none");
    if (els.emptyBox) els.emptyBox.classList.add("d-none");
    if (els.cardsContainer) els.cardsContainer.classList.add("d-none");
    if (els.paginationBar) els.paginationBar.classList.add("d-none");
    if (els.loadingBox) els.loadingBox.classList.remove("d-none");

    const runPromise = (async () => {
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
        state.hasLoadedListOnce = true;

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
      } finally {
        state.activeListPromise = null;
      }
    })();

    state.activeListPromise = runPromise;
    return runPromise;
  }

  async function openDecisionDetail(decisionId, triggerEl = null) {
    const els = getEls();
    const numericId = Number(decisionId);
    const reqSeq = ++state.detailRequestSeq;
    state.activeDecisionId = decisionId;

    if (triggerEl && typeof triggerEl.focus === "function") {
      state.lastFocusedTrigger = triggerEl;
    }

    if (!api.session.isLoggedIn()) {
      showAuthRequiredState();
      return;
    }

    // Mở Modal ở giữa màn hình, giữ nguyên giao diện danh sách phía sau
    showDetailModalShell();

    if (els.modalSubtitle) {
      els.modalSubtitle.textContent =
        !Number.isNaN(numericId) && numericId > 0
          ? `Đang tải thông tin quyết định #${numericId}...`
          : "Xem lại thông tin đề xuất đã lưu";
    }
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
      if (reqSeq !== state.detailRequestSeq) return;

      const record = normalizeRecord(response);
      if (els.detailLoading) els.detailLoading.classList.add("d-none");

      if (!record || !record.id) {
        if (els.detailNotFound) els.detailNotFound.classList.remove("d-none");
        return;
      }

      state.activeDecision = record;
      renderDecisionDetail(record);
    } catch (error) {
      if (reqSeq !== state.detailRequestSeq) return;
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

  function backToHistoryList(updateUrl = true) {
    closeDecisionModal({ updateUrl: Boolean(updateUrl) });
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
      if (!event.target || typeof event.target.closest !== "function") return;
      if (event.target.closest(".dh-sidebar, [data-sidebar-toggle]")) return;
      sidebar.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    });
  }

  function bindEvents() {
    const els = getEls();

    if (els.filterChips) {
      els.filterChips.addEventListener("click", (event) => {
        if (!event.target || typeof event.target.closest !== "function") return;
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
        if (!event.target || typeof event.target.closest !== "function") return;
        const btn = event.target.closest("[data-action='view-detail']");
        if (!btn) return;
        const decisionId = btn.dataset.decisionId;
        if (decisionId) {
          openDecisionDetail(decisionId, btn);
        }
      });
    }

    if (els.btnReload) {
      els.btnReload.addEventListener("click", () => {
        loadHistoryList();
      });
    }

    if (els.btnRetryHistory) {
      els.btnRetryHistory.addEventListener("click", () => loadHistoryList());
    }

    // Các hành động đóng Modal: nút X, nút Đóng footer, nút Đóng trên trạng thái lỗi/404
    if (els.btnCloseModal) {
      els.btnCloseModal.addEventListener("click", () => closeDecisionModal());
    }
    if (els.btnFooterCloseModal) {
      els.btnFooterCloseModal.addEventListener("click", () => closeDecisionModal());
    }
    if (els.btnBackToList) {
      els.btnBackToList.addEventListener("click", () => closeDecisionModal());
    }
    if (els.btnNotFoundBack) {
      els.btnNotFoundBack.addEventListener("click", () => closeDecisionModal());
    }
    if (els.btnErrorBack) {
      els.btnErrorBack.addEventListener("click", () => closeDecisionModal());
    }

    if (els.btnRetryDetail) {
      els.btnRetryDetail.addEventListener("click", () => {
        if (state.activeDecisionId) {
          openDecisionDetail(state.activeDecisionId);
        }
      });
    }

    // Bấm ra vùng overlay bên ngoài khung Modal để đóng
    if (els.detailModal) {
      els.detailModal.addEventListener("click", (event) => {
        if (event.target === els.detailModal && state.isModalOpen) {
          closeDecisionModal();
        }
      });
    }

    // Nhấn phím ESC để đóng Modal
    document.addEventListener("keydown", (event) => {
      if ((event.key === "Escape" || event.key === "Esc") && state.isModalOpen) {
        event.preventDefault();
        closeDecisionModal();
      }
    });

    // Fallback an toàn khi ảnh món ăn bị lỗi đường dẫn (không dùng inline onerror)
    if (els.modalBody) {
      els.modalBody.addEventListener(
        "error",
        (event) => {
          const target = event.target;
          if (!target || !target.dataset || target.dataset.dishImg !== "true") return;
          const wrapper = target.parentElement;
          if (!wrapper) return;
          const fallbackIcon = wrapper.getAttribute("data-fallback-icon") || "🍲";
          wrapper.innerHTML = `<span class="history-dish-fallback-icon" aria-hidden="true">${safeHtml(fallbackIcon)}</span>`;
        },
        true,
      );
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
  }

  function initHistoryPage() {
    initSidebarToggle();
    bindEvents();

    const params = new URLSearchParams(window.location.search);
    const initialId = params.get("id");

    // Luôn tải danh sách lịch sử làm nền; nếu URL có ?id=... thì mở luôn Modal chi tiết
    loadHistoryList({ offset: 0 });
    if (initialId) {
      openDecisionDetail(initialId);
    }
  }

  global.DHHistory = {
    state,
    normalizeRecord,
    loadHistoryList,
    openDecisionDetail,
    closeDecisionModal,
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
