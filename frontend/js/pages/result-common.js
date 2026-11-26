// Hiển thị kết quả dùng chung cho các trang Đề xuất (Food / Travel).
//
// Trang sử dụng truyền vào danh sách phương án + tiêu chí + danh sách bị loại:
// initResultsPage({ results, criteria, excluded, message });
//
// Mô hình WSM: Frontend KHÔNG tự tính điểm khi Backend đã trả về kết quả,
// chỉ hiển thị và giải thích kết quả chuẩn hóa (normalized_score, weight, contribution)
// nhận được từ Decision Engine Backend.

(function (global) {
  const state = {
    results: [],
    criteria: [],
    excluded: [],
    els: null,
    message: "",
    chartMode: "compare", // 'compare' | 'single'
  };

  // Helper escape HTML chống XSS
  function safeHtml(str) {
    if (typeof escapeHtml === "function") return escapeHtml(str);
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Lấy các phần tử DOM dùng chung
  function getElements() {
    if (!state.els) {
      state.els = {
        total: document.getElementById("results-total"),
        validHint: document.getElementById("results-valid-hint"),
        topName: document.getElementById("results-top-name"),
        topScore: document.getElementById("results-top-score"),
        rankingList: document.getElementById("results-ranking-list"),
        explanationCard: document.getElementById("results-explanation"),
        explanationBody: document.getElementById("results-explanation-body"),
        excludedSection: document.getElementById("results-excluded-section"),
        excludedBody: document.getElementById("results-excluded-body"),
        excludedBadge: document.getElementById("results-excluded-badge"),
        excludedCount: document.getElementById("results-excluded-count"),
        excludedHint: document.getElementById("results-excluded-hint"),
      };
    }
    return state.els;
  }

  // ---------- Hàm định dạng ----------

  // 87.3 -> "87,3"
  function formatScore(value) {
    if (value === null || value === undefined || isNaN(value)) return "–";
    return Number(value).toLocaleString("vi-VN", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    });
  }

  function formatWeight(weight) {
    return Math.round(Number(weight || 0) * 100) + "%";
  }

  // Điểm giảm dần; bằng điểm thì theo thứ hạng backend trả về
  function sortResults(results) {
    return [...results].sort(
      (a, b) => (b.total_score ?? b.score ?? 0) - (a.total_score ?? a.score ?? 0) || (a.ranking ?? a.rank ?? 0) - (b.ranking ?? b.rank ?? 0),
    );
  }

  // Ánh xạ nhãn tiêu chí thân thiện
  function getCriterionLabel(key, fallbackLabel) {
    if (fallbackLabel) return fallbackLabel;
    const labels = {
      price: "Giá / Ngân sách",
      preference: "Mức phù hợp nhu cầu/khẩu vị",
      prep_time: "Thời gian chuẩn bị",
      cost: "Chi phí tham khảo",
      estimated_cost: "Chi phí ước tính",
      experience: "Mức phù hợp trải nghiệm",
      duration: "Thời lượng & Tiếp cận",
      estimated_duration: "Thời gian di chuyển",
      activities: "Hoạt động trải nghiệm",
    };
    return labels[key] || key;
  }

  // ---------- Hàm hiển thị ----------

  function renderSummary(sortedResults, excludedList = []) {
    const el = getElements();
    const top = sortedResults[0];
    if (el.total) el.total.textContent = sortedResults.length;
    if (el.validHint) el.validHint.textContent = `Thỏa mãn toàn bộ điều kiện lọc`;

    if (el.topName) el.topName.textContent = top ? top.name : "–";
    if (el.topScore) {
      const scoreVal = top ? (top.total_score ?? top.score ?? 0) : 0;
      el.topScore.textContent = top ? `${formatScore(scoreVal)}/100 điểm (WSM)` : "";
    }

    if (el.excludedCount) el.excludedCount.textContent = excludedList.length;
    if (el.excludedHint) {
      el.excludedHint.textContent = excludedList.length > 0 ? "Vi phạm điều kiện bắt buộc" : "Không có phương án vi phạm";
    }
  }

  function renderRanking(sortedResults) {
    const el = getElements();
    if (!el.rankingList) return;

    el.rankingList.innerHTML = sortedResults
      .map((option, index) => {
        const rank = option.ranking ?? option.rank ?? (index + 1);
        const isTop = rank === 1;
        const scoreVal = option.total_score ?? option.score ?? 0;
        const thumbHtml = option.image
          ? `<img class="results-rank-thumb" src="${option.image}" alt="${safeHtml(option.name)}" loading="lazy">`
          : "";
        return `
        <li>
          <button type="button" class="results-rank-item${isTop ? " is-top" : ""}"
                  data-option-id="${option.id}" aria-pressed="false">
            <span class="results-rank-number">${rank}</span>
            ${thumbHtml}
            <span class="results-rank-main">
              <span class="results-rank-head">
                <span class="results-rank-name">
                  ${safeHtml(option.name)}
                  ${isTop ? '<span class="dh-status dh-status-success">★ Đứng đầu</span>' : ""}
                </span>
                <span class="results-rank-score">${formatScore(scoreVal)}<small>/100</small></span>
              </span>
              <span class="dh-progress-track" aria-hidden="true">
                <span class="dh-progress-bar" style="width: ${Math.min(100, Math.max(0, scoreVal))}%"></span>
              </span>
            </span>
          </button>
        </li>`;
      })
      .join("");
  }

  // Thanh tiến trình trực quan từng tiêu chí
  function renderCriteriaBars(option, criteria) {
    const details = option.criteria_details || {};
    const criteriaScores = option.criteria || option.criteria_scores || {};

    return criteria
      .map((criterion) => {
        const key = criterion.key || criterion.field_name;
        const detail = details[key] || {};
        const scoreVal = detail.normalized_score !== undefined
          ? detail.normalized_score
          : (criteriaScores[key] !== undefined ? criteriaScores[key] : 0);
        const weightVal = detail.weight !== undefined ? detail.weight : criterion.weight;
        const label = getCriterionLabel(key, criterion.label || detail.label);
        const displayScore = scoreVal !== null ? `${Math.round(scoreVal)}/100` : "Thiếu dữ liệu";

        return `
      <div class="dh-criteria-item">
        <div class="dh-criteria-header">
          <span>${safeHtml(label)}
            <span class="results-criteria-weight">· trọng số ${formatWeight(weightVal)}</span>
          </span>
          <strong>${displayScore}</strong>
        </div>
        <div class="dh-progress-track">
          <div class="dh-progress-bar" style="width: ${scoreVal !== null ? Math.min(100, Math.max(0, scoreVal)) : 0}%"></div>
        </div>
      </div>`;
      })
      .join("");
  }

  function renderReasonItems(items, icon) {
    if (!items || items.length === 0) return "";
    return items
      .map(
        (text) => `
        <li class="dh-reason-item">
          <span class="dh-reason-icon" aria-hidden="true">${icon}</span>
          <span>${safeHtml(text)}</span>
        </li>`,
      )
      .join("");
  }

  function renderExplanation(option, criteria) {
    const el = getElements();
    if (!el.explanationBody) return;

    const rank = option.ranking ?? option.rank ?? 1;
    const isTop = rank === 1;
    const totalScoreVal = option.total_score ?? option.score ?? 0;
    const imageHtml = option.image
      ? `<div class="results-explain-image">
        <img src="${option.image}" alt="${safeHtml(option.name)}" loading="lazy">
       </div>`
      : "";

    // Quick specs chips (giá, thời gian, loại bữa ăn)
    const specs = [];
    if (option.price !== undefined && option.price !== null) {
      const priceStr = Number(option.price).toLocaleString("vi-VN") + " ₫";
      specs.push(`<span class="results-spec-chip">Giá: <strong>${priceStr}</strong></span>`);
    }
    if (option.prep_time !== undefined && option.prep_time !== null) {
      specs.push(`<span class="results-spec-chip">Thời gian: <strong>${option.prep_time} phút</strong></span>`);
    }
    if (option.meal_type) {
      const mealLabels = { breakfast: "Sáng", lunch: "Trưa", dinner: "Tối", snack: "Ăn vặt" };
      specs.push(`<span class="results-spec-chip">Bữa: <strong>${mealLabels[option.meal_type] || option.meal_type}</strong></span>`);
    }

    el.explanationBody.innerHTML = `
    <div class="results-explain-head">
      <div class="results-explain-title-group">
        ${imageHtml}
        <div>
          <span class="dh-status ${isTop ? "dh-status-success" : "dh-status-info"}">
            Hạng ${rank}${isTop ? " · Đứng đầu" : ""}
          </span>
          <h3 class="results-explain-name">${safeHtml(option.name)}</h3>
          ${specs.length > 0 ? `<div class="results-specs-chips">${specs.join("")}</div>` : ""}
        </div>
      </div>
      <div class="dh-score-box">
        <span class="dh-score-value">${formatScore(totalScoreVal)}</span>
        <span class="dh-score-label">Điểm tổng (WSM)</span>
      </div>
    </div>

    <!-- Biểu đồ cột đóng góp điểm theo tiêu chí (Thay thế thanh tiến trình cũ) -->
    <div class="results-chart-section mt-4 mb-3" id="results-chart-section">
      <div class="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-2">
        <div>
          <h4 class="results-subtitle mb-0" id="results-chart-title">Biểu đồ đóng góp điểm theo tiêu chí</h4>
          <span class="dh-muted dh-small">
            Mức đóng góp điểm (<code class="dh-code-inline">contribution = weight × normalized_score</code>) của từng tiêu chí vào tổng điểm WSM
          </span>
        </div>
        <div class="results-chart-view-toggle btn-group btn-group-sm" role="group" aria-label="Chế độ hiển thị biểu đồ">
          <button type="button" class="dh-btn dh-btn-xs dh-btn-outline${state.chartMode === "compare" ? " is-active" : ""}" data-chart-mode="compare" id="btn-chart-mode-compare" aria-pressed="${state.chartMode === "compare"}">
            So sánh các phương án
          </button>
          <button type="button" class="dh-btn dh-btn-xs dh-btn-outline${state.chartMode === "single" ? " is-active" : ""}" data-chart-mode="single" id="btn-chart-mode-single" aria-pressed="${state.chartMode === "single"}">
            Chỉ phương án này
          </button>
        </div>
      </div>
      <div id="criteria-chart-container" class="criteria-chart-container" aria-labelledby="results-chart-title"></div>
    </div>

    <h4 class="results-subtitle">Vì sao phương án này đạt hạng ${rank}?</h4>
    <p class="results-reason-text">${safeHtml(option.explanation || "")}</p>
    ${
      option.reasons && option.reasons.length > 0
        ? `<ul class="dh-reason-list mb-3">${renderReasonItems(option.reasons, "✦")}</ul>`
        : ""
    }

    <div class="results-pros-cons">
      <div class="results-note-box results-pros">
        <h4 class="results-note-title">Ưu điểm nổi bật</h4>
        <ul class="dh-reason-list">${renderReasonItems(option.advantages || (option.reasons || []).slice(0, 2), "✓")}</ul>
      </div>
      <div class="results-note-box results-cons">
        <h4 class="results-note-title">Điểm cần lưu ý</h4>
        <ul class="dh-reason-list">${renderReasonItems(option.disadvantages || ["Điểm tổng hợp phụ thuộc vào mức ngân sách và điều kiện lọc đã chọn"], "!")}</ul>
      </div>
    </div>`;

    // Render biểu đồ đóng góp điểm theo tiêu chí (CriteriaChart)
    const chartContainer = el.explanationBody.querySelector("#criteria-chart-container");
    if (chartContainer && typeof CriteriaChart !== "undefined" && typeof CriteriaChart.render === "function") {
      CriteriaChart.render({
        container: chartContainer,
        results: state.results,
        criteria: state.criteria,
        selectedId: option.id,
        mode: state.chartMode,
        onSelectOption: (newOptId) => {
          selectOption(newOptId, state.results, state.criteria);
        },
      });

      // Gắn sự kiện chuyển đổi chế độ biểu đồ
      const btnCompare = el.explanationBody.querySelector("#btn-chart-mode-compare");
      const btnSingle = el.explanationBody.querySelector("#btn-chart-mode-single");

      if (btnCompare) {
        btnCompare.addEventListener("click", () => {
          state.chartMode = "compare";
          btnCompare.classList.add("is-active");
          btnCompare.setAttribute("aria-pressed", "true");
          if (btnSingle) {
            btnSingle.classList.remove("is-active");
            btnSingle.setAttribute("aria-pressed", "false");
          }
          CriteriaChart.render({
            container: chartContainer,
            results: state.results,
            criteria: state.criteria,
            selectedId: option.id,
            mode: "compare",
            onSelectOption: (newOptId) => {
              selectOption(newOptId, state.results, state.criteria);
            },
          });
        });
      }

      if (btnSingle) {
        btnSingle.addEventListener("click", () => {
          state.chartMode = "single";
          btnSingle.classList.add("is-active");
          btnSingle.setAttribute("aria-pressed", "true");
          if (btnCompare) {
            btnCompare.classList.remove("is-active");
            btnCompare.setAttribute("aria-pressed", "false");
          }
          CriteriaChart.render({
            container: chartContainer,
            results: state.results,
            criteria: state.criteria,
            selectedId: option.id,
            mode: "single",
            onSelectOption: (newOptId) => {
              selectOption(newOptId, state.results, state.criteria);
            },
          });
        });
      }
    }
  }

  // Hiển thị danh sách các phương án bị loại (Excluded Candidates)
  function renderExcludedCandidates(excludedList) {
    const el = getElements();
    if (!el.excludedSection || !el.excludedBody) return;

    const list = Array.isArray(excludedList) ? excludedList : [];
    if (el.excludedBadge) {
      el.excludedBadge.textContent = `${list.length} phương án`;
      el.excludedBadge.className = `dh-status ${list.length > 0 ? "dh-status-danger" : "dh-status-success"}`;
    }
    if (el.excludedCount) {
      el.excludedCount.textContent = list.length;
    }
    if (el.excludedHint) {
      el.excludedHint.textContent = list.length > 0 ? "Vi phạm điều kiện bắt buộc" : "Không có phương án vi phạm";
    }

    if (list.length === 0) {
      el.excludedBody.innerHTML = `
        <div class="p-4 text-center text-muted dh-small">
          <span class="text-success fw-bold fs-5 d-block mb-1">✓</span>
          Tất cả các phương án xem xét đều thỏa mãn toàn bộ điều kiện bắt buộc (không có phương án nào bị loại).
        </div>
      `;
      return;
    }

    const rows = list.map((item, idx) => {
      const name = safeHtml(item.name || `Phương án #${item.id || idx + 1}`);
      const reason = safeHtml(item.exclusion_reason || "Không thỏa mãn điều kiện bắt buộc");
      const reasonsList = Array.isArray(item.exclusion_reasons) && item.exclusion_reasons.length > 1
        ? `<ul class="results-excluded-reasons-list dh-small mt-1 mb-0 ps-3">
             ${item.exclusion_reasons.map((r) => `<li>${safeHtml(r)}</li>`).join("")}
           </ul>`
        : "";

      return `
      <tr>
        <td>
          <div class="d-flex align-items-center gap-2">
            <span class="results-excluded-dot" aria-hidden="true">✕</span>
            <strong class="results-excluded-name">${name}</strong>
          </div>
        </td>
        <td class="text-center">
          <span class="dh-status dh-status-danger">Bị loại</span>
        </td>
        <td>
          <div class="results-excluded-reason">${reason}</div>
          ${reasonsList}
        </td>
      </tr>`;
    }).join("");

    el.excludedBody.innerHTML = `
      <div class="table-responsive">
        <table class="dh-table results-excluded-table" aria-label="Danh sách phương án bị loại">
          <thead>
            <tr>
              <th scope="col" style="width: 28%;">Tên phương án</th>
              <th scope="col" style="width: 16%;" class="text-center">Trạng thái</th>
              <th scope="col">Lý do bị loại cụ thể</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      </div>
    `;
  }

  // Khi tất cả phương án bị loại (không còn phương án hợp lệ)
  function renderAllExcludedState(excludedList, message) {
    const el = getElements();
    if (el.total) el.total.textContent = "0";
    if (el.topName) el.topName.textContent = "Không có phương án";
    if (el.topScore) el.topScore.textContent = "0 phương án hợp lệ";

    if (el.rankingList) {
      el.rankingList.innerHTML = `
      <li class="dh-empty-state py-4">
        <div class="dh-empty-icon text-warning">⚠️</div>
        <div class="dh-empty-title">Không có phương án hợp lệ</div>
        <p class="dh-empty-desc">${safeHtml(message || "Tất cả phương án đều đã bị loại bởi các điều kiện bắt buộc. Vui lòng xem lý do chi tiết ở bảng bên dưới và thử nới lỏng bộ lọc.")}</p>
      </li>`;
    }

    if (el.explanationBody) {
      el.explanationBody.innerHTML = `
      <div class="dh-empty-state py-4">
        <div class="dh-empty-icon text-muted">📋</div>
        <div class="dh-empty-title">Không thể chấm điểm WSM</div>
        <p class="dh-empty-desc">Decision Engine đã dừng quá trình chấm điểm vì không còn phương án nào thỏa mãn điều kiện lọc. Vui lòng điều chỉnh lại ngân sách, thời gian chuẩn bị hoặc nguyên liệu cần tránh.</p>
      </div>`;
    }

    renderExcludedCandidates(excludedList);
  }

  function renderEmptyState(message) {
    const el = getElements();
    if (el.total) el.total.textContent = "0";
    if (el.topName) el.topName.textContent = "–";
    if (el.topScore) el.topScore.textContent = "";
    if (el.rankingList) {
      el.rankingList.innerHTML = `
      <li class="dh-empty-state">
        <div class="dh-empty-icon">📋</div>
        <div class="dh-empty-title">Chưa có phương án phù hợp</div>
        <p class="dh-empty-desc">${safeHtml(message || "Hãy thử nới lỏng điều kiện để nhận thêm kết quả.")}</p>
      </li>`;
    }
    if (el.explanationBody) {
      el.explanationBody.innerHTML = `
        <div class="criteria-chart-state criteria-chart-empty py-4 text-center">
          <div class="dh-empty-icon mb-2" aria-hidden="true">📊</div>
          <div class="criteria-chart-empty-title fw-semibold text-muted mb-1">Chưa có dữ liệu để hiển thị biểu đồ</div>
          <p class="dh-muted dh-small mb-0">${safeHtml(message || "Chưa có phương án nào để hiển thị biểu đồ và giải thích kết quả.")}</p>
        </div>
      `;
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

  // config: { results: [...], criteria: [...], excluded: [...], message: "..." }
  function initResultsPage(config) {
    state.results = config.results || [];
    state.criteria = config.criteria || [];
    state.excluded = config.excluded || [];
    state.message = config.message || "";

    initSidebar();

    const el = getElements();
    const sorted = sortResults(state.results);

    if (sorted.length === 0) {
      if (state.excluded.length > 0) {
        renderAllExcludedState(state.excluded, state.message);
      } else {
        renderEmptyState(state.message);
        renderExcludedCandidates([]);
      }
    } else {
      renderSummary(sorted, state.excluded);
      renderRanking(sorted);
      selectOption(sorted[0].id, state.results, state.criteria);
      renderExcludedCandidates(state.excluded);
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
    renderCriteriaBars,
    renderReasonItems,
    renderExplanation,
    renderExcludedCandidates,
    renderAllExcludedState,
    renderEmptyState,
    selectOption,
    initSidebar,
    initResultsPage,
  };
})(window);
