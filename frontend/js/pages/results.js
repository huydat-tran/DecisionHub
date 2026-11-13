// Trang Đề xuất thông minh (Recommendations) – hỗ trợ 2 phân hệ:
// 1. Đề xuất món ăn (Food)
// 2. Đề xuất du lịch (Travel)
//
// Mô hình WSM: Điểm tổng = Σ (trọng số × điểm tiêu chí).
// Frontend KHÔNG tự tính điểm, chỉ hiển thị, chuyển đổi phân hệ và giải thích.

// ---------- 1. DỮ LIỆU ĐỀ XUẤT MÓN ĂN (FOOD) ----------
const FOOD_CRITERIA = [
  { key: "price", label: "Giá", weight: 0.4 },
  { key: "preference", label: "Mức phù hợp nhu cầu/khẩu vị", weight: 0.35 },
  { key: "prep_time", label: "Thời gian chuẩn bị", weight: 0.25 },
];

const FOOD_RESULTS = [
  {
    id: 1,
    name: "Bún chả Hà Nội",
    image: "../assets/images/foods/hihi.png",
    score: 87.3,
    ranking: 1,
    criteria: { price: 86, preference: 94, prep_time: 80 },
    explanation:
      "Đứng đầu nhờ điểm phù hợp khẩu vị cao nhất (94/100) và mức giá nằm trong ngân sách. Thời gian chuẩn bị ở mức khá nên chỉ bị trừ nhẹ ở tiêu chí này.",
    advantages: [
      "Mức phù hợp khẩu vị cao nhất trong 5 phương án",
      "Giá thấp hơn ngân sách tối đa",
      "Đủ đạm và rau, hợp một bữa trưa đầy đủ",
    ],
    disadvantages: [
      "Thời gian chuẩn bị lâu hơn phở và bánh mì",
      "Giá cao hơn bánh mì thịt",
    ],
  },
  {
    id: 2,
    name: "Phở bò tái",
    image: "../assets/images/foods/hihi.png",
    score: 85.2,
    ranking: 2,
    criteria: { price: 78, preference: 90, prep_time: 90 },
    explanation:
      "Xếp thứ hai nhờ chuẩn bị nhanh (90/100) và khẩu vị tốt (90/100). Giá cao hơn bún chả nên kém phương án đứng đầu 2,1 điểm.",
    advantages: [
      "Phục vụ nhanh, ít phải chờ",
      "Mức phù hợp khẩu vị cao",
      "Món nước nóng, dễ ăn",
    ],
    disadvantages: [
      "Giá cao hơn bún chả và bánh mì",
      "Thiên về đạm và tinh bột, ít rau",
    ],
  },
  {
    id: 3,
    name: "Bánh mì thịt",
    image: "../assets/images/foods/hihi.png",
    score: 84.5,
    ranking: 3,
    criteria: { price: 90, preference: 70, prep_time: 96 },
    explanation:
      "Thắng ở giá (90/100) và tốc độ chuẩn bị (96/100), nhưng mức phù hợp khẩu vị chỉ đạt 70/100 nên không vượt được hai phương án đầu.",
    advantages: [
      "Giá thấp nhất trong 5 phương án",
      "Chuẩn bị nhanh nhất, có thể mang đi",
      "Linh hoạt khi cần ăn vội",
    ],
    disadvantages: [
      "Mức phù hợp khẩu vị thấp nhất trong 5 phương án",
      "Khó no lâu nếu ăn một mình",
    ],
  },
  {
    id: 4,
    name: "Cơm tấm sườn",
    image: "../assets/images/foods/hihi.png",
    score: 80.6,
    ranking: 4,
    criteria: { price: 72, preference: 88, prep_time: 84 },
    explanation:
      "Khẩu vị tốt (88/100) và chuẩn bị khá nhanh (84/100), nhưng điểm giá chỉ 72/100 nên điểm tổng dừng ở 80,6.",
    advantages: [
      "No lâu, đủ năng lượng cho buổi chiều",
      "Mức phù hợp khẩu vị cao",
      "Thời gian chuẩn bị ngắn",
    ],
    disadvantages: [
      "Giá cao hơn nhiều phương án khác",
      "Dễ vượt ngân sách nếu gọi thêm món",
    ],
  },
  {
    id: 5,
    name: "Lẩu mini một người",
    image: "../assets/images/foods/hihi.png",
    score: 60.5,
    ranking: 5,
    criteria: { price: 52, preference: 82, prep_time: 44 },
    explanation:
      "Khẩu vị khá (82/100) nhưng giá cao (52/100) và thời gian chuẩn bị dài (44/100) nên điểm tổng thấp nhất nhóm.",
    advantages: [
      "Phù hợp khi muốn ăn ấm, nhiều món",
      "Có thể điều chỉnh khẩu phần",
    ],
    disadvantages: [
      "Điểm giá thấp nhất trong 5 phương án",
      "Thời gian chuẩn bị dài nhất",
      "Không phù hợp khi cần ăn nhanh",
    ],
  },
];

// ---------- 2. DỮ LIỆU ĐỀ XUẤT DU LỊCH (TRAVEL) ----------
const TRAVEL_CRITERIA = [
  { key: "cost", label: "Chi phí tham khảo", weight: 0.4 },
  { key: "experience", label: "Mức phù hợp trải nghiệm", weight: 0.35 },
  { key: "duration", label: "Thời lượng & Tiếp cận", weight: 0.25 },
];

const TRAVEL_RESULTS = [
  {
    id: 101,
    name: "Phố cổ Hội An (Quảng Nam)",
    image: "../assets/images/travel/hoian.jpg",
    score: 88.5,
    ranking: 1,
    criteria: { cost: 85, experience: 95, duration: 84 },
    explanation:
      "Đứng đầu đề xuất du lịch nhờ điểm trải nghiệm văn hóa ẩm thực vượt trội (95/100) và chi phí du lịch hợp lý, phù hợp lịch trình 2-3 ngày.",
    advantages: [
      "Di sản văn hóa thế giới, trải nghiệm phố đi bộ và đèn lồng đặc sắc",
      "Ẩm thực phong phú, chi phí ăn uống và lưu trú rất phải chăng",
      "Thuận tiện kết hợp tham quan Đà Nẵng và biển An Bàng",
    ],
    disadvantages: [
      "Mùa cao điểm du lịch khá đông đúc",
      "Mùa mưa cuối năm (tháng 10 - 11) có nguy cơ ngập lụt",
    ],
  },
  {
    id: 102,
    name: "Vịnh Hạ Long (Quảng Ninh)",
    image: "../assets/images/travel/halong.jpg",
    score: 86.8,
    ranking: 2,
    criteria: { cost: 76, experience: 96, duration: 90 },
    explanation:
      "Xếp thứ hai với điểm trải nghiệm cảnh quan thiên nhiên kỳ vĩ đạt 96/100, đường cao tốc di chuyển nhanh chóng, chi phí du thuyền nhỉnh hơn các điểm khác.",
    advantages: [
      "Kỳ quan thiên nhiên thế giới với hàng nghìn đảo đá vôi kỳ thú",
      "Trải nghiệm du thuyền ngủ đêm và chèo thuyền kayak đẳng cấp",
      "Hạ tầng giao thông thuận tiện từ Hà Nội (chỉ khoảng 2 giờ)",
    ],
    disadvantages: [
      "Chi phí tour du thuyền cao hơn các hình thức du lịch tự túc",
      "Dễ bị ảnh hưởng bởi bão hoặc lệnh cấm tàu vào mùa mưa bão",
    ],
  },
  {
    id: 103,
    name: "Đà Lạt (Lâm Đồng)",
    image: "../assets/images/travel/dalat.jpg",
    score: 84.2,
    ranking: 3,
    criteria: { cost: 88, experience: 86, duration: 76 },
    explanation:
      "Được ưa chuộng nhờ khí hậu se lạnh quanh năm, chi phí nghỉ dưỡng và ẩm thực rất dễ chịu, thời gian di chuyển từ miền Bắc/Trung dài hơn.",
    advantages: [
      "Khí hậu mát mẻ ôn hòa quanh năm, cảnh quan thông reo lãng mạn",
      "Vô số quán cà phê đẹp, điểm check-in nông trại và đồi chè",
      "Chi phí dịch vụ ăn uống và homestay đa dạng, hợp túi tiền",
    ],
    disadvantages: [
      "Tình trạng đông đúc, ùn tắc vào các dịp lễ tết và cuối tuần",
      "Đường đèo dốc uốn lượn, cần tay lái vững khi tự di chuyển",
    ],
  },
  {
    id: 104,
    name: "Đảo Phú Quốc (Kiên Giang)",
    image: "../assets/images/travel/phuquoc.jpg",
    score: 81.6,
    ranking: 4,
    criteria: { cost: 68, experience: 94, duration: 84 },
    explanation:
      "Thiên đường nghỉ dưỡng biển đảo với tổ hợp giải trí hiện đại, tuy nhiên chi phí vé máy bay và lưu trú cao nên xếp thứ tư.",
    advantages: [
      "Bãi biển trong xanh, cát mịn và ngắm hoàng hôn đẹp nhất Việt Nam",
      "Tổ hợp vui chơi giải trí VinWonders, Safari và cáp treo Hòn Thơm",
      "Hải sản tươi ngon, hệ thống resort nghỉ dưỡng quốc tế phong phú",
    ],
    disadvantages: [
      "Chi phí vé máy bay và dịch vụ du lịch thuộc mức cao",
      "Khoảng cách giữa các cụm điểm tham quan Bắc đảo và Nam đảo khá xa",
    ],
  },
  {
    id: 105,
    name: "Tràng An - Bái Đính (Ninh Bình)",
    image: "../assets/images/travel/trangan.jpg",
    score: 79.4,
    ranking: 5,
    criteria: { cost: 86, experience: 82, duration: 92 },
    explanation:
      "Rất tối ưu cho chuyến đi ngắn 1 - 2 ngày với chi phí tiết kiệm và vị trí gần, nhưng hoạt động trải nghiệm về đêm chưa thực sự phong phú.",
    advantages: [
      "Di sản kép văn hóa và thiên nhiên, phong cảnh non nước kỳ vĩ",
      "Khoảng cách gần Hà Nội (chỉ khoảng 1.5 - 2 giờ di chuyển)",
      "Chi phí vé tham quan và dịch vụ thuyền đò niêm yết rõ ràng",
    ],
    disadvantages: [
      "Ngồi thuyền tham quan ngoài trời khá lâu, dễ bị nắng nóng mùa hè",
      "Các hoạt động vui chơi giải trí về đêm còn hạn chế",
    ],
  },
];

// ---------- 3. QUẢN LÝ PHÂN HỆ HIỆN TẠI (STATE) ----------
let currentModule = "food"; // "food" | "travel"

function getCurrentData() {
  return currentModule === "food"
    ? { results: FOOD_RESULTS, criteria: FOOD_CRITERIA }
    : { results: TRAVEL_RESULTS, criteria: TRAVEL_CRITERIA };
}

const rankingListEl = document.getElementById("results-ranking-list");
const explanationCardEl = document.getElementById("results-explanation");
const explanationBodyEl = document.getElementById("results-explanation-body");
const moduleStatusBadgeEl = document.getElementById("module-status-badge");
const moduleSelectorEl = document.getElementById("results-module-selector");

// ---------- 4. HÀM HIỂN THỊ ----------

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
function getSortedResults() {
  const { results } = getCurrentData();
  return [...results].sort(
    (a, b) => b.score - a.score || a.ranking - b.ranking,
  );
}

function renderSummary(sortedResults) {
  const top = sortedResults[0];
  document.getElementById("results-total").textContent = sortedResults.length;
  document.getElementById("results-top-name").textContent = top ? top.name : "–";
  document.getElementById("results-top-score").textContent = top
    ? `${formatScore(top.score)}/100 điểm`
    : "";
}

function renderRanking(sortedResults) {
  rankingListEl.innerHTML = sortedResults
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

function renderCriteria(option) {
  const { criteria } = getCurrentData();
  return criteria.map((criterion) => {
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
  }).join("");
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

function renderExplanation(option) {
  const isTop = option.ranking === 1;
  const imageHtml = option.image
    ? `<div class="results-explain-image">
        <img src="${option.image}" alt="${escapeHtml(option.name)}" loading="lazy">
       </div>`
    : "";
  explanationBodyEl.innerHTML = `
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
    <div class="dh-criteria-group">${renderCriteria(option)}</div>

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
  document.getElementById("results-total").textContent = "0";
  rankingListEl.innerHTML = `
    <li class="dh-empty-state">
      <div class="dh-empty-icon">📋</div>
      <div class="dh-empty-title">Chưa có phương án phù hợp</div>
      <p class="dh-empty-desc">Hãy thử nới lỏng điều kiện để nhận thêm kết quả.</p>
    </li>`;
  explanationBodyEl.innerHTML =
    '<p class="dh-muted mb-0">Chưa có phương án nào để giải thích.</p>';
}

// ---------- 5. CHỌN PHƯƠNG ÁN & CHUYỂN PHÂN HỆ ----------

function selectOption(optionId) {
  const { results } = getCurrentData();
  const option = results.find((item) => item.id === optionId);
  if (!option) return;

  rankingListEl.querySelectorAll(".results-rank-item").forEach((button) => {
    const isSelected = Number(button.dataset.optionId) === optionId;
    button.classList.toggle("is-selected", isSelected);
    button.setAttribute("aria-pressed", String(isSelected));
  });
  renderExplanation(option);
}

function switchModule(moduleName) {
  if (moduleName !== "food" && moduleName !== "travel") return;
  currentModule = moduleName;

  // Cập nhật chip active
  if (moduleSelectorEl) {
    moduleSelectorEl.querySelectorAll(".dh-chip").forEach((chip) => {
      const isActive = chip.dataset.module === moduleName;
      chip.classList.toggle("active", isActive);
      chip.setAttribute("aria-selected", String(isActive));
    });
  }

  // Cập nhật badge
  if (moduleStatusBadgeEl) {
    if (moduleName === "food") {
      moduleStatusBadgeEl.className = "dh-status dh-status-success";
      moduleStatusBadgeEl.textContent = "Phân hệ Món ăn (Food)";
    } else {
      moduleStatusBadgeEl.className = "dh-status dh-status-info";
      moduleStatusBadgeEl.textContent = "Phân hệ Du lịch (Travel)";
    }
  }

  // Render lại bảng xếp hạng & tổng kết
  const sorted = getSortedResults();
  if (sorted.length === 0) {
    renderEmptyState();
  } else {
    renderSummary(sorted);
    renderRanking(sorted);
    selectOption(sorted[0].id);
  }
}

// Lắng nghe click chọn phân hệ Food / Travel
if (moduleSelectorEl) {
  moduleSelectorEl.addEventListener("click", (event) => {
    const chip = event.target.closest(".dh-chip");
    if (!chip || !chip.dataset.module) return;
    switchModule(chip.dataset.module);
  });
}

// Lắng nghe click chọn món ăn / địa điểm
rankingListEl.addEventListener("click", (event) => {
  const button = event.target.closest(".results-rank-item");
  if (!button) return;

  selectOption(Number(button.dataset.optionId));

  if (window.matchMedia("(max-width: 991.98px)").matches) {
    explanationCardEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

// ---------- 6. MENU MOBILE ----------
const sidebarEl = document.querySelector(".dh-sidebar");
const sidebarToggleEl = document.querySelector("[data-sidebar-toggle]");

function setSidebarOpen(isOpen) {
  sidebarEl.classList.toggle("is-open", isOpen);
  sidebarToggleEl.setAttribute("aria-expanded", String(isOpen));
}

if (sidebarToggleEl && sidebarEl) {
  sidebarToggleEl.addEventListener("click", () => {
    setSidebarOpen(!sidebarEl.classList.contains("is-open"));
  });

  document.addEventListener("click", (event) => {
    if (event.target.closest(".dh-sidebar, [data-sidebar-toggle]")) return;
    setSidebarOpen(false);
  });
}

// ---------- 7. KHỞI TẠO ----------
function initResultsPage() {
  switchModule("food"); // Mặc định mở Food trước
}

initResultsPage();
