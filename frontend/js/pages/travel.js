// =============================================================================
// Travel – nối API POST /api/v1/travel/recommend
// Lọc ngân sách/thời lượng/vùng/sở thích ở backend, hiển thị kết quả WSM.
// =============================================================================

(function () {
  "use strict";

  // ── Map giá trị chip/select → tham số API ──────────────────────────────────

  // duration select value → max_duration (giờ) gửi lên API
  const DURATION_TO_HOURS = {
    "1":   12,   // đi trong ngày
    "2-3": 48,   // 2–3 ngày
    "4-5": null, // không giới hạn
    "all": null,
  };

  // region chip → enum backend (TravelRegion)
  const REGION_MAP = {
    "bac":       "Bắc",
    "trung":     "Trung",
    "nam":       "Nam",
    "tay-nguyen":"Tây Nguyên",
    "tay-nam-bo":"Tây Nam Bộ",
    "all":       null,
  };

  // preference select → preferred_activities gửi lên API
  const PREF_MAP = {
    "bien":       ["biển", "nghỉ dưỡng biển", "du thuyền"],
    "thien-nhien":["thiên nhiên", "khám phá", "sinh thái"],
    "van-hoa":    ["văn hóa", "lịch sử", "di sản"],
    "giai-tri":   ["vui chơi", "giải trí", "check-in"],
    "chua-lanh":  ["nghỉ dưỡng", "chữa lành", "chăm sóc"],
    "all":        [],
  };

  // ── DOM ───────────────────────────────────────────────────────────────────
  const maxBudgetInput  = document.getElementById("travel-max-budget");
  const durationSelect  = document.getElementById("travel-duration-select");
  const preferenceSelect= document.getElementById("travel-preference-select");
  const sortSelect      = document.getElementById("travel-sort-select");
  const btnSearch       = document.getElementById("btn-travel-search");
  const btnReset        = document.getElementById("btn-travel-reset");
  const btnEmptyReset   = document.getElementById("btn-travel-empty-reset");

  const regionChips     = document.querySelectorAll("#chip-travel-regions .dh-chip");
  const budgetChips     = document.querySelectorAll("#chip-travel-budgets .dh-chip");

  const resultsGrid     = document.getElementById("travel-results-grid");
  const resultsCount    = document.getElementById("travel-results-count");
  const emptyState      = document.getElementById("travel-empty");

  // ── Trạng thái UI ─────────────────────────────────────────────────────────
  const state = {
    region:     "all",
    budgetMax:  null,   // số nguyên VND hoặc null
    duration:   "all",
    preference: "all",
    sortBy:     "wsm",
    lastItems:  [],     // cache kết quả để sort lại client-side
  };

  // ── Render helpers ─────────────────────────────────────────────────────────
  function esc(str) {
    return typeof escapeHtml === "function" ? escapeHtml(str) : String(str ?? "");
  }

  function fmtVnd(amount) {
    if (typeof formatMoney === "function") return formatMoney(amount);
    return Number(amount).toLocaleString("vi-VN") + " ₫";
  }

  function setLoading(on) {
    if (!btnSearch) return;
    btnSearch.disabled = on;
    btnSearch.textContent = on ? "⏳ Đang tìm kiếm..." : "🔍 Tìm kiếm & Gợi ý điểm đến";
  }

  function showState(mode) {
    // mode: "loading" | "empty" | "results" | "error"
    if (!resultsGrid || !emptyState) return;
    resultsGrid.innerHTML = "";
    emptyState.classList.add("d-none");

    if (mode === "loading") {
      resultsGrid.innerHTML = `
        <div class="col-12 text-center py-5">
          <div class="spinner-border text-success" role="status" style="width:2.5rem;height:2.5rem;">
            <span class="visually-hidden">Đang tải...</span>
          </div>
          <p class="dh-muted mt-3 mb-0">Đang phân tích và xếp hạng địa điểm...</p>
        </div>`;
    } else if (mode === "error") {
      resultsGrid.innerHTML = `
        <div class="col-12">
          <div class="alert alert-danger d-flex align-items-center gap-2 mb-0" role="alert">
            <span style="font-size:1.4rem;">⚠️</span>
            <div id="travel-error-msg">Không thể kết nối backend. Vui lòng thử lại.</div>
          </div>
        </div>`;
    }
  }

  // ── Build payload ──────────────────────────────────────────────────────────
  function buildPayload() {
    const payload = { limit: 20 };

    if (state.budgetMax && state.budgetMax > 0) {
      payload.budget_max = state.budgetMax;
    }

    const maxDur = DURATION_TO_HOURS[state.duration];
    if (maxDur !== null && maxDur !== undefined) {
      payload.max_duration = maxDur;
    }

    const regionVal = REGION_MAP[state.region];
    if (regionVal) payload.region = regionVal;

    const acts = PREF_MAP[state.preference] || [];
    if (acts.length) payload.preferred_activities = acts;

    return payload;
  }

  // ── Sort client-side (trên kết quả đã có từ API) ──────────────────────────
  function sortItems(items) {
    return [...items].sort((a, b) => {
      if (state.sortBy === "cost-asc")    return a.estimated_cost - b.estimated_cost;
      if (state.sortBy === "cost-desc")   return b.estimated_cost - a.estimated_cost;
      if (state.sortBy === "rating-desc") return (b.rating ?? 0) - (a.rating ?? 0);
      // wsm mặc định: theo rank từ backend
      return a.rank - b.rank;
    });
  }

  // ── Render cards ───────────────────────────────────────────────────────────
  function renderCard(item, rank) {
    const rankClass = rank === 1 ? "rank-1" : rank === 2 ? "rank-2" : rank === 3 ? "rank-3" : "";
    const rankText  = rank === 1 ? "🥇 #1 Top đề xuất" : rank === 2 ? "🥈 #2" : rank === 3 ? "🥉 #3" : `#${rank}`;

    const imgSrc = item.image_url || "../assets/images/travel/halong.jpg";
    const score  = typeof item.score === "number" ? item.score.toFixed(1) : (item.total_score ?? 0).toFixed(1);

    // Lý do gợi ý
    const reasonsHtml = (item.reasons || []).length
      ? `<ul class="travel-reasons-list">
           ${item.reasons.map(r => `<li>${esc(r)}</li>`).join("")}
         </ul>`
      : "";

    // Điểm 3 tiêu chí
    const cs = item.criteria_scores || {};
    const cCost = cs.estimated_cost != null ? Math.round(cs.estimated_cost) : "–";
    const cDur  = cs.estimated_duration != null ? Math.round(cs.estimated_duration) : "–";
    const cAct  = cs.activities != null ? Math.round(cs.activities) : "–";

    const highlights = (item.highlights || []).slice(0, 3)
      .map(h => `<span class="travel-tag-pill">${esc(h)}</span>`).join("");

    return `
      <div class="col-12 col-md-6 col-xl-4">
        <article class="travel-item-card" aria-label="${esc(item.name)}">
          <div class="travel-card-media">
            <img src="${esc(imgSrc)}" alt="${esc(item.name)}" class="travel-card-img" loading="lazy"
                 onerror="this.src='../assets/images/travel/halong.jpg'">
            <span class="travel-rank-pill ${rankClass}">${rankText}</span>
            <span class="travel-floating-badge">★ ${score} WSM</span>
            <span class="travel-region-pill">${esc(item.region)}</span>
          </div>

          <div class="travel-card-body">
            <h3 class="travel-card-title">${esc(item.name)}</h3>
            <div class="travel-card-location">
              <span>📍</span><span>${esc(item.province_city)}</span>
            </div>

            <!-- Điểm 3 tiêu chí WSM -->
            <div class="travel-criteria-scores">
              <span class="travel-criteria-item" title="Điểm chi phí">💰 Giá: <strong>${cCost}</strong></span>
              <span class="travel-criteria-item" title="Điểm thời lượng">⏱️ Thời lượng: <strong>${cDur}</strong></span>
              <span class="travel-criteria-item" title="Điểm hoạt động">🎯 Trải nghiệm: <strong>${cAct}</strong></span>
            </div>

            <!-- Ngân sách & thời lượng -->
            <div class="travel-card-specs">
              <div>
                <div class="travel-cost-lbl">Ngân sách ước tính</div>
                <div class="travel-cost-val">${fmtVnd(item.estimated_cost)}</div>
              </div>
              <div class="text-end">
                <div class="travel-cost-lbl">Thời lượng</div>
                <div class="travel-duration-val">⏱️ ${esc(String(item.estimated_duration))} giờ</div>
              </div>
            </div>

            <!-- Highlights -->
            ${highlights ? `<div class="travel-tags-wrap">${highlights}</div>` : ""}

            <!-- Lý do gợi ý -->
            ${reasonsHtml
              ? `<div class="travel-reasons">${reasonsHtml}</div>`
              : ""}

            <!-- Mô tả -->
            ${item.description
              ? `<p class="travel-card-desc">${esc(item.description)}</p>`
              : ""}

            <div class="travel-card-footer">
              <div class="travel-rating-box">
                <span class="travel-rating-star">⭐</span>
                <span>${item.rating != null ? Number(item.rating).toFixed(1) : "–"} / 5.0</span>
              </div>
              <span class="dh-label mb-0" style="font-size:11px;color:var(--dh-text-muted);">
                Loại: ${esc(item.activity_type || "–")}
              </span>
            </div>
          </div>
        </article>
      </div>`;
  }

  function renderResults(items) {
    if (!resultsGrid || !emptyState || !resultsCount) return;

    if (!items || items.length === 0) {
      resultsGrid.innerHTML = "";
      emptyState.classList.remove("d-none");
      resultsCount.textContent = "Không tìm thấy địa điểm nào phù hợp";
      return;
    }

    emptyState.classList.add("d-none");
    resultsCount.textContent = `Tìm thấy ${items.length} địa điểm gợi ý (đã xếp hạng WSM)`;
    resultsGrid.innerHTML = items.map((item, i) => renderCard(item, i + 1)).join("");
  }

  // ── Gọi API ────────────────────────────────────────────────────────────────
  async function fetchRecommend() {
    setLoading(true);
    showState("loading");
    if (resultsCount) resultsCount.textContent = "Đang tải...";

    try {
      const payload  = buildPayload();
      const response = await api.post("/v1/travel/recommend", payload);

      state.lastItems = (response.data && response.data.items) ? response.data.items : [];
      const sorted = sortItems(state.lastItems);
      renderResults(sorted);

      // Thông báo kết quả
      const msg = response.message || "";
      if (state.lastItems.length === 0 && typeof showToast === "function") {
        showToast(msg || "Không có địa điểm phù hợp. Hãy nới điều kiện.", "warning");
      } else if (typeof showToast === "function") {
        showToast(msg || `Đề xuất ${state.lastItems.length} địa điểm phù hợp.`, "success");
      }
    } catch (err) {
      showState("error");
      const errEl = document.getElementById("travel-error-msg");
      if (errEl) errEl.textContent = err.message || "Lỗi không xác định.";
      if (resultsCount) resultsCount.textContent = "Có lỗi xảy ra";
      if (typeof showToast === "function") {
        showToast(err.message || "Không thể kết nối backend.", "error");
      }
    } finally {
      setLoading(false);
    }
  }

  // ── Reset ──────────────────────────────────────────────────────────────────
  function resetAll() {
    state.region     = "all";
    state.budgetMax  = null;
    state.duration   = "all";
    state.preference = "all";
    state.sortBy     = "wsm";
    state.lastItems  = [];

    if (maxBudgetInput)   maxBudgetInput.value   = "";
    if (durationSelect)   durationSelect.value   = "all";
    if (preferenceSelect) preferenceSelect.value = "all";
    if (sortSelect)       sortSelect.value       = "wsm";

    regionChips.forEach(c => c.classList.toggle("active", c.dataset.region === "all"));
    budgetChips.forEach(c => c.classList.toggle("active", c.dataset.budget === "all"));

    fetchRecommend();
    if (typeof showToast === "function") showToast("Đã đặt lại bộ lọc", "success");
  }

  // ── Events ─────────────────────────────────────────────────────────────────
  function initEvents() {
    // Chip ngân sách nhanh
    budgetChips.forEach(chip => {
      chip.addEventListener("click", () => {
        budgetChips.forEach(c => c.classList.remove("active"));
        chip.classList.add("active");
        const val = chip.dataset.budget;
        state.budgetMax = (val && val !== "all") ? Number(val) : null;
        if (maxBudgetInput) maxBudgetInput.value = "";
        fetchRecommend();
      });
    });

    // Input ngân sách tay
    if (maxBudgetInput) {
      maxBudgetInput.addEventListener("input", e => {
        const val = e.target.value.trim();
        state.budgetMax = val ? Number(val) : null;
        budgetChips.forEach(c => c.classList.toggle("active", !val && c.dataset.budget === "all"));
      });
      maxBudgetInput.addEventListener("change", () => fetchRecommend());
    }

    // Chip vùng miền
    regionChips.forEach(chip => {
      chip.addEventListener("click", () => {
        regionChips.forEach(c => c.classList.remove("active"));
        chip.classList.add("active");
        state.region = chip.dataset.region;
        fetchRecommend();
      });
    });

    // Select thời lượng
    if (durationSelect) {
      durationSelect.addEventListener("change", e => {
        state.duration = e.target.value;
        fetchRecommend();
      });
    }

    // Select sở thích
    if (preferenceSelect) {
      preferenceSelect.addEventListener("change", e => {
        state.preference = e.target.value;
        fetchRecommend();
      });
    }

    // Select sắp xếp – sort client-side, không gọi lại API
    if (sortSelect) {
      sortSelect.addEventListener("change", e => {
        state.sortBy = e.target.value;
        renderResults(sortItems(state.lastItems));
      });
    }

    // Nút tìm kiếm
    if (btnSearch) {
      btnSearch.addEventListener("click", fetchRecommend);
    }

    // Nút đặt lại
    if (btnReset) btnReset.addEventListener("click", resetAll);
    if (btnEmptyReset) btnEmptyReset.addEventListener("click", resetAll);

    // Sidebar mobile
    const sidebarEl      = document.querySelector(".dh-sidebar");
    const sidebarToggle  = document.querySelector("[data-sidebar-toggle]");
    if (sidebarToggle && sidebarEl) {
      sidebarToggle.addEventListener("click", () => {
        const open = sidebarEl.classList.toggle("is-open");
        sidebarToggle.setAttribute("aria-expanded", String(open));
      });
      document.addEventListener("click", e => {
        if (e.target.closest(".dh-sidebar, [data-sidebar-toggle]")) return;
        sidebarEl.classList.remove("is-open");
        sidebarToggle.setAttribute("aria-expanded", "false");
      });
    }
  }

  // ── CSS cho lý do gợi ý (thêm inline nếu travel.css chưa có) ─────────────
  const style = document.createElement("style");
  style.textContent = `
    .travel-reasons { margin: 6px 0 4px; }
    .travel-reasons-list {
      margin: 0; padding-left: 16px;
      font-size: 12px; color: var(--dh-text-muted);
    }
    .travel-reasons-list li { margin-bottom: 2px; }
  `;
  document.head.appendChild(style);

  // ── Init ───────────────────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", () => {
    initEvents();
    fetchRecommend(); // load ngay khi mở trang
  });
})();
