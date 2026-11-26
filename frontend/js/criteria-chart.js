/**
 * DecisionHub - Criteria Contribution Bar Chart Component (Biểu đồ đóng góp điểm theo tiêu chí)
 *
 * Hiển thị biểu đồ cột thể hiện mức độ đóng góp điểm (contribution = weight × normalized_score)
 * của từng tiêu chí đối với mỗi phương án trong mô hình WSM (Weighted Sum Model).
 *
 * Sử dụng thuần SVG/HTML5, không phụ thuộc thư viện ngoài, tương thích 100% môi trường offline
 * và tuân thủ chặt chẽ DecisionHub UI Guidelines & Design System.
 */

(function (global) {
  "use strict";

  // Bảng màu chuẩn theo Design System (Green SaaS & Accessible Contrast)
  const OPTION_COLORS = [
    "#16845B", // Top 1: Brand Primary Green
    "#2876A8", // Rank 2: Info Blue / Ocean
    "#B7791F", // Rank 3: Warning Amber / Bronze
    "#6366F1", // Rank 4: Indigo
    "#0D9488", // Rank 5: Teal
    "#E11D48", // Rank 6: Rose Red
    "#8B5CF6", // Rank 7: Purple
    "#D97706", // Rank 8: Warm Orange
  ];

  // Helper escape HTML chống XSS
  function safe(str) {
    if (typeof escapeHtml === "function") return escapeHtml(str);
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Ánh xạ nhãn tiêu chí thân thiện
  function getCriterionLabel(key, fallbackLabel) {
    if (fallbackLabel && typeof fallbackLabel === "string" && fallbackLabel.trim()) {
      return fallbackLabel.trim();
    }
    const map = {
      price: "Giá",
      preference: "Mức phù hợp nhu cầu/khẩu vị",
      prep_time: "Thời gian chuẩn bị",
      cost: "Chi phí tham khảo",
      estimated_cost: "Chi phí ước tính",
      experience: "Mức phù hợp trải nghiệm",
      duration: "Thời lượng & Tiếp cận",
      estimated_duration: "Thời gian di chuyển",
      activities: "Hoạt động trải nghiệm",
    };
    return map[key] || key || "Tiêu chí";
  }

  function formatScore(val) {
    if (val === null || val === undefined || isNaN(val)) return "–";
    return Number(val).toLocaleString("vi-VN", {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    });
  }

  function formatWeight(weight) {
    const num = Number(weight || 0);
    return Math.round(num * 100) + "%";
  }

  /**
   * Chuẩn hóa dữ liệu từ Backend/Engine sang cấu trúc dùng cho biểu đồ.
   * Luôn ưu tiên dùng trường `contribution` từ Backend khi có sẵn.
   */
  function processChartData(results, criteriaList) {
    if (!Array.isArray(results) || results.length === 0) {
      return { criteria: [], series: [], maxContribution: 0 };
    }

    const safeResults = results.filter((item) => item && typeof item === "object");
    if (safeResults.length === 0) {
      return { criteria: [], series: [], maxContribution: 0 };
    }

    // 1. Xác định danh sách tiêu chí
    let criteria = [];
    if (Array.isArray(criteriaList) && criteriaList.length > 0) {
      criteria = criteriaList.map((c) => {
        const key = c.key || c.field_name || "unknown";
        return {
          key: key,
          label: getCriterionLabel(key, c.label),
          weight: Number(c.weight ?? 0),
        };
      });
    } else {
      // Tự suy diễn từ phần tử đầu tiên nếu không truyền criteriaList
      const first = safeResults[0];
      const details = first.criteria_details || {};
      const scores = first.criteria_scores || first.criteria || {};
      const keys = Object.keys(details).length > 0 ? Object.keys(details) : Object.keys(scores);
      criteria = keys.map((key) => ({
        key: key,
        label: getCriterionLabel(key, details[key]?.label),
        weight: Number(details[key]?.weight ?? 0),
      }));
    }

    if (criteria.length === 0) {
      return { criteria: [], series: [], maxContribution: 0 };
    }

    // 2. Trích xuất series cho từng phương án
    let maxContribution = 0;
    const series = safeResults.map((opt, optIndex) => {
      const optId = opt.id ?? opt.food_id ?? (optIndex + 1);
      const optName = opt.name || `Phương án ${optIndex + 1}`;
      const optRank = opt.ranking ?? opt.rank ?? (optIndex + 1);
      const optTotalScore = Number(opt.total_score ?? opt.score ?? 0);
      const color = OPTION_COLORS[optIndex % OPTION_COLORS.length];

      const rawDetails = opt.criteria_details || {};
      const rawScores = opt.criteria_scores || opt.criteria || {};

      const points = criteria.map((crit) => {
        const detail = rawDetails[crit.key] || {};
        const scoreVal =
          detail.normalized_score !== undefined
            ? detail.normalized_score
            : (rawScores[crit.key] !== undefined ? rawScores[crit.key] : null);

        const weightVal =
          detail.weight !== undefined && detail.weight !== null
            ? Number(detail.weight)
            : crit.weight;

        // ƯU TIÊN SỐ 1: Dùng trường `contribution` từ Backend trả về
        let contributionVal = 0;
        if (detail.contribution !== undefined && detail.contribution !== null) {
          contributionVal = Number(detail.contribution);
        } else if (scoreVal !== null && !isNaN(scoreVal)) {
          // Fallback nếu mock data hoặc thiếu contribution: weight * normalized_score
          contributionVal = Math.round(weightVal * Number(scoreVal) * 10000) / 10000;
        }

        if (isNaN(contributionVal) || contributionVal < 0) {
          contributionVal = 0;
        }

        if (contributionVal > maxContribution) {
          maxContribution = contributionVal;
        }

        return {
          criterionKey: crit.key,
          criterionLabel: crit.label,
          weight: weightVal,
          normalized_score: scoreVal !== null && !isNaN(scoreVal) ? Number(scoreVal) : null,
          contribution: contributionVal,
        };
      });

      return {
        id: optId,
        name: optName,
        rank: optRank,
        total_score: optTotalScore,
        color: color,
        points: points,
      };
    });

    return {
      criteria: criteria,
      series: series,
      maxContribution: maxContribution,
    };
  }

  /**
   * Tính toán bước chia trục Y (nice ticks)
   */
  function calculateYTicks(maxValue) {
    const target = Math.max(maxValue, 10);
    // Chọn thang đo trên: 10, 20, 30, 40, 50, 60, 80, 100
    const thresholds = [10, 20, 25, 30, 40, 50, 60, 75, 100];
    let top = 100;
    for (const t of thresholds) {
      if (target <= t) {
        top = t;
        break;
      }
    }
    const step = top <= 25 ? 5 : top <= 50 ? 10 : 20;
    const ticks = [];
    for (let v = 0; v <= top; v += step) {
      ticks.push(v);
    }
    return { top: top, ticks: ticks };
  }

  /**
   * Renders Tooltip HTML
   */
  function buildTooltipHtml(item) {
    const normText =
      item.normalized_score !== null
        ? `${formatScore(item.normalized_score)} / 100`
        : '<span class="text-muted">Không có dữ liệu</span>';

    return `
      <div class="criteria-chart-tooltip-header">
        <span class="criteria-chart-tooltip-dot" style="background-color: ${item.color}"></span>
        <strong class="criteria-chart-tooltip-opt">${safe(item.optionName)}</strong>
      </div>
      <div class="criteria-chart-tooltip-body">
        <div class="criteria-chart-tooltip-row">
          <span class="criteria-chart-tooltip-label">Tiêu chí:</span>
          <span class="criteria-chart-tooltip-val">${safe(item.criterionLabel)}</span>
        </div>
        <div class="criteria-chart-tooltip-row">
          <span class="criteria-chart-tooltip-label">Trọng số (Weight):</span>
          <span class="criteria-chart-tooltip-val">${formatWeight(item.weight)} (${Number(item.weight).toFixed(2)})</span>
        </div>
        <div class="criteria-chart-tooltip-row">
          <span class="criteria-chart-tooltip-label">Điểm chuẩn hóa (Normalized):</span>
          <span class="criteria-chart-tooltip-val">${normText}</span>
        </div>
        <div class="criteria-chart-tooltip-row criteria-chart-tooltip-highlight">
          <span class="criteria-chart-tooltip-label">Điểm đóng góp (Contribution):</span>
          <span class="criteria-chart-tooltip-val fw-bold">${formatScore(item.contribution)}</span>
        </div>
      </div>
    `;
  }

  /**
   * Component CriteriaChart
   */
  const CriteriaChart = {
    /**
     * Render trạng thái Đang tải (Loading)
     */
    renderLoading: function (container) {
      if (!container) return;
      container.innerHTML = `
        <div class="criteria-chart-state criteria-chart-loading py-4 text-center" role="status" aria-live="polite">
          <div class="spinner-border text-success mb-2" role="status">
            <span class="visually-hidden">Đang tải...</span>
          </div>
          <div class="dh-muted dh-small">Đang phân tích và tải dữ liệu biểu đồ...</div>
        </div>
      `;
    },

    /**
     * Render trạng thái Rỗng (Empty)
     */
    renderEmpty: function (container, message) {
      if (!container) return;
      const text = message || "Chưa có dữ liệu để hiển thị biểu đồ.";
      container.innerHTML = `
        <div class="criteria-chart-state criteria-chart-empty py-4 text-center">
          <div class="dh-empty-icon mb-2" aria-hidden="true">📊</div>
          <div class="criteria-chart-empty-title fw-semibold text-muted mb-1">
            ${safe(text)}
          </div>
          <p class="dh-muted dh-small mb-0">
            Hãy áp dụng bộ lọc hoặc chọn tiêu chí để xem mức đóng góp điểm WSM của từng phương án.
          </p>
        </div>
      `;
    },

    /**
     * Render trạng thái Lỗi (Error)
     */
    renderError: function (container, errorMessage) {
      if (!container) return;
      const text = errorMessage || "Đã xảy ra lỗi khi tạo biểu đồ đóng góp điểm.";
      container.innerHTML = `
        <div class="criteria-chart-state criteria-chart-error alert alert-danger py-3 px-3 my-2" role="alert">
          <div class="d-flex align-items-center gap-2">
            <span class="criteria-chart-error-icon" aria-hidden="true">⚠️</span>
            <div>
              <strong>Lỗi hiển thị biểu đồ</strong>
              <div class="dh-small mt-1">${safe(text)}</div>
            </div>
          </div>
        </div>
      `;
    },

    /**
     * Render chính của Biểu đồ đóng góp điểm theo tiêu chí
     *
     * @param {Object} options
     *   - container: HTMLElement (bắt buộc)
     *   - results: Danh sách phương án đã chấm điểm (từ Backend API hoặc Engine)
     *   - criteria: Danh sách tiêu chí (price, preference, prep_time...)
     *   - selectedId: ID phương án đang được chọn trong ranking list
     *   - mode: 'compare' (so sánh nhiều phương án) hoặc 'single' (chỉ phương án đang chọn)
     *   - onSelectOption: Callback khi click vào phương án trên biểu đồ
     */
    render: function (options) {
      const container = options.container;
      if (!container) return;

      const results = options.results || [];
      const criteriaList = options.criteria || [];
      const mode = options.mode || "compare"; // 'compare' | 'single'
      const selectedId = options.selectedId !== undefined ? options.selectedId : null;
      const onSelectOption = typeof options.onSelectOption === "function" ? options.onSelectOption : null;

      // 1. Kiểm tra trạng thái rỗng
      if (!results || results.length === 0) {
        this.renderEmpty(container, "Chưa có dữ liệu để hiển thị biểu đồ.");
        return;
      }

      // 2. Chuẩn hóa dữ liệu
      let chartData;
      try {
        chartData = processChartData(results, criteriaList);
      } catch (err) {
        console.error("Lỗi khi xử lý dữ liệu biểu đồ:", err);
        this.renderError(container, "Dữ liệu kết quả không hợp lệ hoặc thiếu trường bắt buộc.");
        return;
      }

      const { criteria, series, maxContribution } = chartData;
      if (criteria.length === 0 || series.length === 0) {
        this.renderEmpty(container, "Chưa có dữ liệu tiêu chí để hiển thị biểu đồ.");
        return;
      }

      // Xác định tập series cần vẽ dựa theo mode
      let displaySeries = series;
      if (mode === "single" && selectedId !== null) {
        const found = series.find((s) => s.id === selectedId);
        if (found) {
          displaySeries = [found];
        }
      }

      // 3. Kích thước & Tọa độ SVG
      const padLeft = 60;
      const padRight = 24;
      const padTop = 32;
      const padBottom = 54;
      const chartHeight = 280;
      const plotHeight = chartHeight - padTop - padBottom;

      const numCriteria = criteria.length;
      const numSeries = displaySeries.length;

      // Chiều rộng cột và nhóm cột linh hoạt, đảm bảo không bị chồng lấn
      const barWidth = numSeries === 1 ? 40 : Math.max(16, Math.min(32, Math.floor(120 / numSeries)));
      const barInnerGap = 4;
      const groupWidth = numSeries * barWidth + (numSeries - 1) * barInnerGap;
      const minGroupSpacing = 40;
      const groupSpacing = Math.max(minGroupSpacing, Math.floor(groupWidth * 0.4));

      const totalGroupSpan = groupWidth + groupSpacing;
      const plotWidth = Math.max(numCriteria * totalGroupSpan, 420);
      const chartWidth = padLeft + plotWidth + padRight;

      // Tính thang Y
      const { top: yTop, ticks: yTicks } = calculateYTicks(maxContribution);

      function getY(val) {
        const ratio = Math.max(0, Math.min(yTop, val)) / yTop;
        return padTop + plotHeight * (1 - ratio);
      }

      // 4. Sinh Gridlines & Y-Axis Labels
      let gridHtml = "";
      yTicks.forEach((tickVal) => {
        const y = getY(tickVal);
        gridHtml += `
          <g class="criteria-chart-grid-line">
            <line x1="${padLeft}" y1="${y}" x2="${chartWidth - padRight}" y2="${y}" stroke="${tickVal === 0 ? "#E0E8E3" : "#EDF3EF"}" stroke-dasharray="${tickVal === 0 ? "none" : "3,3"}" stroke-width="${tickVal === 0 ? "1" : "0.75"}"/>
            <text x="${padLeft - 8}" y="${y + 4}" text-anchor="end" fill="#66776F" font-size="11" font-family="Roboto, sans-serif">${tickVal}</text>
          </g>
        `;
      });

      // Nhãn trục Y (Điểm đóng góp)
      const yAxisTitleHtml = `
        <text transform="rotate(-90)" x="${-(padTop + plotHeight / 2)}" y="${16}" text-anchor="middle" fill="#66776F" font-size="11" font-weight="500" font-family="Roboto, sans-serif">
          Điểm đóng góp (Contribution)
        </text>
      `;

      // 5. Sinh Cột (Bars) & X-Axis Labels
      let barsHtml = "";
      let xLabelsHtml = "";
      const groupStep = plotWidth / numCriteria;

      criteria.forEach((crit, critIndex) => {
        const groupCenterX = padLeft + critIndex * groupStep + groupStep / 2;
        const groupStartX = groupCenterX - groupWidth / 2;

        // Nhãn tiêu chí dưới trục X
        xLabelsHtml += `
          <g class="criteria-chart-x-label">
            <text x="${groupCenterX}" y="${chartHeight - padBottom + 20}" text-anchor="middle" fill="#172B23" font-size="12" font-weight="600" font-family="Roboto, sans-serif">
              ${safe(crit.label)}
            </text>
            <text x="${groupCenterX}" y="${chartHeight - padBottom + 36}" text-anchor="middle" fill="#66776F" font-size="11" font-family="Roboto, sans-serif">
              Trọng số: ${formatWeight(crit.weight)}
            </text>
          </g>
        `;

        displaySeries.forEach((s, sIndex) => {
          const pt = s.points.find((p) => p.criterionKey === crit.key) || {
            criterionKey: crit.key,
            criterionLabel: crit.label,
            weight: crit.weight,
            normalized_score: null,
            contribution: 0,
          };

          const barX = groupStartX + sIndex * (barWidth + barInnerGap);
          const barY = getY(pt.contribution);
          const barH = Math.max(0, padTop + plotHeight - barY);

          const isSelected = selectedId !== null && s.id === selectedId;
          const barClass = `criteria-chart-bar${isSelected ? " is-selected" : ""}`;

          // Value label phía trên đỉnh cột (nếu cột đủ rộng)
          const valueTextY = Math.max(padTop - 6, barY - 6);
          const valDisplay = pt.contribution > 0 ? pt.contribution.toFixed(1) : "0";

          barsHtml += `
            <g class="criteria-chart-bar-group" data-option-id="${s.id}" data-crit-key="${crit.key}">
              <rect class="${barClass}"
                    x="${barX}" y="${barY}" width="${barWidth}" height="${barH}"
                    rx="4" fill="${s.color}" fill-opacity="0.78"
                    stroke="${s.color}" stroke-width="1" stroke-opacity="0.85"
                    data-option-id="${s.id}"
                    data-option-name="${safe(s.name)}"
                    data-crit-key="${crit.key}"
                    data-crit-label="${safe(crit.label)}"
                    data-weight="${pt.weight}"
                    data-norm-score="${pt.normalized_score !== null ? pt.normalized_score : ""}"
                    data-contribution="${pt.contribution}"
                    data-color="${s.color}"
                    tabindex="0"
                    role="graphics-symbol"
                    aria-label="${safe(s.name)} - ${safe(crit.label)}: Đóng góp ${valDisplay} điểm">
              </rect>
              <text class="criteria-chart-bar-val"
                    x="${barX + barWidth / 2}" y="${valueTextY}"
                    text-anchor="middle"
                    fill="#172B23"
                    font-size="11"
                    font-weight="600"
                    font-family="Roboto, sans-serif">
                ${valDisplay}
              </text>
            </g>
          `;
        });
      });

      // 6. Sinh Legend Chú thích các phương án
      let legendHtml = "";
      if (displaySeries.length > 1 || mode === "compare") {
        const legendItems = displaySeries
          .map((s) => {
            const isSelected = selectedId !== null && s.id === selectedId;
            return `
            <button type="button" class="criteria-chart-legend-item${isSelected ? " is-active" : ""}"
                    data-option-id="${s.id}" aria-pressed="${isSelected}">
              <span class="criteria-chart-legend-color" style="background-color: ${s.color};"></span>
              <span class="criteria-chart-legend-name">${safe(s.name)}</span>
              <span class="criteria-chart-legend-score dh-small text-muted">(${formatScore(s.total_score)}đ)</span>
            </button>
          `;
          })
          .join("");

        legendHtml = `
          <div class="criteria-chart-legend" role="group" aria-label="Chú thích các phương án">
            ${legendItems}
          </div>
        `;
      } else if (displaySeries.length === 1) {
        const single = displaySeries[0];
        legendHtml = `
          <div class="criteria-chart-single-badge">
            <span class="criteria-chart-legend-color" style="background-color: ${single.color};"></span>
            <strong>${safe(single.name)}</strong>
            <span class="dh-status dh-status-success ms-2">Hạng ${single.rank}</span>
            <span class="text-muted ms-2">Tổng điểm: <strong>${formatScore(single.total_score)}</strong>/100 (WSM)</span>
          </div>
        `;
      }

      // 7. Render tổng thể vào container
      container.innerHTML = `
        <div class="criteria-chart-wrapper">
          ${legendHtml}
          <div class="criteria-chart-scroll-box">
            <svg class="criteria-chart-svg" viewBox="0 0 ${chartWidth} ${chartHeight}" width="100%" height="${chartHeight}" preserveAspectRatio="xMinYMin meet" role="img" aria-label="Biểu đồ đóng góp điểm theo tiêu chí">
              ${gridHtml}
              ${yAxisTitleHtml}
              ${barsHtml}
              ${xLabelsHtml}
            </svg>
          </div>
          <div class="criteria-chart-tooltip" id="criteria-chart-tooltip" style="display: none;" role="tooltip" aria-hidden="true"></div>
        </div>
      `;

      // 8. Đăng ký sự kiện tương tác Tooltip & Click
      const tooltipEl = container.querySelector("#criteria-chart-tooltip");
      const wrapperEl = container.querySelector(".criteria-chart-wrapper");

      container.querySelectorAll(".criteria-chart-bar").forEach((bar) => {
        function showTip(evt) {
          if (!tooltipEl || !wrapperEl) return;
          const rect = bar.getBoundingClientRect();
          const wrapRect = wrapperEl.getBoundingClientRect();

          const data = {
            optionId: bar.dataset.optionId,
            optionName: bar.dataset.optionName,
            criterionLabel: bar.dataset.critLabel,
            weight: Number(bar.dataset.weight || 0),
            normalized_score: bar.dataset.normScore !== "" ? Number(bar.dataset.normScore) : null,
            contribution: Number(bar.dataset.contribution || 0),
            color: bar.dataset.color,
          };

          tooltipEl.innerHTML = buildTooltipHtml(data);
          tooltipEl.style.display = "block";
          tooltipEl.setAttribute("aria-hidden", "false");

          // Tính tọa độ tooltip căn giữa phía trên cột
          const tipWidth = tooltipEl.offsetWidth || 240;
          let left = rect.left - wrapRect.left + rect.width / 2 - tipWidth / 2;
          let top = rect.top - wrapRect.top - (tooltipEl.offsetHeight || 130) - 8;

          // Chống tràn lề trái / phải
          if (left < 10) left = 10;
          if (left + tipWidth > wrapRect.width - 10) {
            left = wrapRect.width - tipWidth - 10;
          }
          if (top < 10) {
            // Nếu tràn lề trên thì lật xuống dưới cột
            top = rect.bottom - wrapRect.top + 8;
          }

          tooltipEl.style.left = `${left}px`;
          tooltipEl.style.top = `${top}px`;
        }

        function hideTip() {
          if (!tooltipEl) return;
          tooltipEl.style.display = "none";
          tooltipEl.setAttribute("aria-hidden", "true");
        }

        bar.addEventListener("mouseenter", showTip);
        bar.addEventListener("focus", showTip);
        bar.addEventListener("mouseleave", hideTip);
        bar.addEventListener("blur", hideTip);

        if (onSelectOption) {
          bar.addEventListener("click", () => {
            const optId = Number(bar.dataset.optionId);
            if (!isNaN(optId)) onSelectOption(optId);
          });
        }
      });

      // Click vào Legend để chuyển chọn phương án
      container.querySelectorAll(".criteria-chart-legend-item").forEach((btn) => {
        btn.addEventListener("click", () => {
          const optId = Number(btn.dataset.optionId);
          if (!isNaN(optId) && onSelectOption) {
            onSelectOption(optId);
          }
        });
      });
    },
  };

  global.CriteriaChart = CriteriaChart;
})(window);
