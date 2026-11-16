// Hiển thị kết quả dùng chung cho các trang Đề xuất (Food / Travel).
//
// Trang sử dụng truyền vào danh sách phương án + tiêu chí của phân hệ đó qua
// initResultsPage({ results, criteria }); các hàm bên dưới không biết trước
// dữ liệu riêng của Food hay Travel.
//
// Mô hình WSM: Frontend KHÔNG tự tính điểm, chỉ hiển thị và giải thích
// kết quả nhận được từ Backend.

(function (global) {
  const state = { results: [], criteria: [], els: null };

  // Lấy các phần tử DOM dùng chung (có mặt trên cả hai trang).
  function getElements() {
    if (!state.els) {
      state.els = {
        total: document.getElementById("results-total"),
        topName: document.getElementById("results-top-name"),
        topScore: document.getElementById("results-top-score"),
        rankingList: document.getElementById("results-ranking-list"),
        explanationCard: document.getElementById("results-explanation"),
        explanationBody: document.getElementById("results-explanation-body"),
      };
    }
    return state.els;
  }

  // ---------- Hàm định dạng ----------

  // 87.3 -> "87,3"
  function formatScore(value) {
    return Number(value).toLocaleString("vi-VN", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    });
  }

  // 0.4 -> "40%"
  function formatWeight(weight) {
    return Math.round(weight * 100) + "%";
  }

  // Điểm giảm dần; bằng điểm thì theo thứ hạng backend trả về
  function sortResults(results) {
    return [...results].sort(
      (a, b) => b.score - a.score || a.ranking - b.ranking,
    );
  }

  // ---------- Hàm hiển thị ----------

  function renderSummary(sortedResults) {
    const el = getElements();
    const top = sortedResults[0];
    if (el.total) el.total.textContent = sortedResults.length;
    if (el.topName) el.topName.textContent = top ? top.name : "–";
    if (el.topScore) {
      el.topScore.textContent = top ? `${formatScore(top.score)}/100 điểm` : "";
    }
  }

  function renderRanking(sortedResults) {
    const el = getElements();
    if (!el.rankingList) return;

    el.rankingList.innerHTML = sortedResults
      .map((option, index) => {
        const isTop = index === 0;
        const thumbHtml = option.image
          ? `<img class="results-rank-thumb" src="${option.image}" alt="${escapeHtml(option.name)}" loading="lazy">`
          : "";
        return `
        <li>
          <button type="button" class="results-rank-item${isTop ? " is-top" : ""}"
                  data-option-id="${option.id}" aria-pressed="false">
            <span class="results-rank-number">${option.ranking}</span>
            ${thumbHtml}
            <span class="results-rank-main">
              <span class="results-rank-head">
                <span class="results-rank-name">
                  ${escapeHtml(option.name)}
                  ${isTop ? '<span class="dh-status dh-status-success">★ Đứng đầu</span>' : ""}
                </span>
                <span class="results-rank-score">${formatScore(option.score)}<small>/100</small></span>
              </span>
              <span class="dh-progress-track" aria-hidden="true">
                <span class="dh-progress-bar" style="width: ${option.score}%"></span>
              </span>
            </span>
          </button>
        </li>`;
      })
      .join("");
  }

  function renderCriteria(option, criteria) {
    return criteria
      .map((criterion) => {
        const value = option.criteria[criterion.key] || 0;
        return `
      <div class="dh-criteria-item">
        <div class="dh-criteria-header">
          <span>${escapeHtml(criterion.label)}
            <span class="results-criteria-weight">· trọng số ${formatWeight(criterion.weight)}</span>
          </span>
          <strong>${value}/100</strong>
        </div>
        <div class="dh-progress-track">
          <div class="dh-progress-bar" style="width: ${value}%"></div>
        </div>
      </div>`;
      })
      .join("");
  }

  function renderReasonItems(items, icon) {
    return items
      .map(
        (text) => `
        <li class="dh-reason-item">
          <span class="dh-reason-icon" aria-hidden="true">${icon}</span>
          <span>${escapeHtml(text)}</span>
        </li>`,
      )
      .join("");
  }

  function renderExplanation(option, criteria) {
    const el = getElements();
    if (!el.explanationBody) return;

    const isTop = option.ranking === 1;
    const imageHtml = option.image
      ? `<div class="results-explain-image">
        <img src="${option.image}" alt="${escapeHtml(option.name)}" loading="lazy">
       </div>`
      : "";

    el.explanationBody.innerHTML = `
    <div class="results-explain-head">
      <div class="results-explain-title-group">
        ${imageHtml}
        <div>
          <span class="dh-status ${isTop ? "dh-status-success" : "dh-status-info"}">
            Hạng ${option.ranking}${isTop ? " · Đứng đầu" : ""}
          </span>
          <h3 class="results-explain-name">${escapeHtml(option.name)}</h3>
        </div>
      </div>
      <div class="dh-score-box">
        <span class="dh-score-value">${formatScore(option.score)}</span>
        <span class="dh-score-label">Điểm tổng</span>
      </div>
    </div>

    <h4 class="results-subtitle">Điểm theo từng tiêu chí</h4>
    <div class="dh-criteria-group">${renderCriteria(option, criteria)}</div>

    <h4 class="results-subtitle">Vì sao phương án này đạt hạng ${option.ranking}?</h4>
    <p class="results-reason-text">${escapeHtml(option.explanation)}</p>

    <div class="results-pros-cons">
      <div class="results-note-box results-pros">
        <h4 class="results-note-title">Ưu điểm</h4>
        <ul class="dh-reason-list">${renderReasonItems(option.advantages, "✓")}</ul>
      </div>
      <div class="results-note-box results-cons">
        <h4 class="results-note-title">Hạn chế</h4>
        <ul class="dh-reason-list">${renderReasonItems(option.disadvantages, "!")}</ul>
      </div>
    </div>`;
  }

  function renderEmptyState() {
    const el = getElements();
    if (el.total) el.total.textContent = "0";
    if (el.rankingList) {
      el.rankingList.innerHTML = `
    <li class="dh-empty-state">
      <div class="dh-empty-icon">📋</div>
      <div class="dh-empty-title">Chưa có phương án phù hợp</div>
      <p class="dh-empty-desc">Hãy thử nới lỏng điều kiện để nhận thêm kết quả.</p>
    </li>`;
    }
    if (el.explanationBody) {
      el.explanationBody.innerHTML =
        '<p class="dh-muted mb-0">Chưa có phương án nào để giải thích.</p>';
    }
  }

  // ---------- Chọn phương án ----------

  function selectOption(optionId, results, criteria) {
    const el = getElements();
    const option = results.find((item) => item.id === optionId);
    if (!option || !el.rankingList) return;

    el.rankingList.querySelectorAll(".results-rank-item").forEach((button) => {
      const isSelected = Number(button.dataset.optionId) === optionId;
      button.classList.toggle("is-selected", isSelected);
      button.setAttribute("aria-pressed", String(isSelected));
    });
    renderExplanation(option, criteria);
  }

  // ---------- Menu mobile (dùng chung) ----------

  function initSidebar() {
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

  // ---------- Khởi tạo trang kết quả ----------

  // config: { results: [...], criteria: [...] }
  function initResultsPage(config) {
    state.results = config.results || [];
    state.criteria = config.criteria || [];

    initSidebar();

    const el = getElements();
    const sorted = sortResults(state.results);

    if (sorted.length === 0) {
      renderEmptyState();
    } else {
      renderSummary(sorted);
      renderRanking(sorted);
      selectOption(sorted[0].id, state.results, state.criteria);
    }

    if (el.rankingList && !el.rankingList.dataset.bound) {
      el.rankingList.dataset.bound = "true";
      el.rankingList.addEventListener("click", (event) => {
        const button = event.target.closest(".results-rank-item");
        if (!button) return;

        selectOption(Number(button.dataset.optionId), state.results, state.criteria);

        if (
          el.explanationCard &&
          window.matchMedia("(max-width: 991.98px)").matches
        ) {
          el.explanationCard.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    }
  }

  global.DHResults = {
    formatScore,
    formatWeight,
    sortResults,
    renderSummary,
    renderRanking,
    renderCriteria,
    renderReasonItems,
    renderExplanation,
    renderEmptyState,
    selectOption,
    initSidebar,
    initResultsPage,
  };
})(window);
