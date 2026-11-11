// ==========================================================
// JS riêng cho phân hệ Travel (Khám phá du lịch - WhereShouldITravel)
// Dựa trên DecisionHub.md Mục 5 & UI Guidelines
// ==========================================================

const TRAVEL_ITEMS = [
  {
    id: 1,
    name: "Vịnh Hạ Long",
    region: "bac",
    region_name: "Miền Bắc",
    province: "Quảng Ninh",
    cost: 1500000,
    duration: "2-3",
    duration_text: "2 ngày 1 đêm",
    type: "khampha",
    type_name: "Khám phá thiên nhiên",
    description: "Kỳ quan thiên nhiên thế giới với hàng nghìn đảo đá vôi kỳ vĩ trên vịnh biển nước xanh như ngọc."
  },
  {
    id: 2,
    name: "Phố cổ Hội An",
    region: "trung",
    region_name: "Miền Trung",
    province: "Quảng Nam",
    cost: 1200000,
    duration: "2-3",
    duration_text: "2 - 3 ngày",
    type: "nghiduong",
    type_name: "Nghỉ dưỡng & Văn hóa",
    description: "Đô thị cổ bên dòng sông Hoài với những ngôi nhà vàng cổ kính và ánh đèn lồng rực rỡ về đêm."
  },
  {
    id: 3,
    name: "Đà Lạt Mộng Mơ",
    region: "trung",
    region_name: "Miền Trung",
    province: "Lâm Đồng",
    cost: 2000000,
    duration: "2-3",
    duration_text: "3 ngày 2 đêm",
    type: "nghiduong",
    type_name: "Nghỉ dưỡng",
    description: "Khí hậu se lạnh quanh năm, rừng thông reo và những quán cà phê view thung lũng lãng mạn."
  },
  {
    id: 4,
    name: "Làng cổ Đường Lâm",
    region: "bac",
    region_name: "Miền Bắc",
    province: "Hà Nội",
    cost: 300000,
    duration: "1",
    duration_text: "Đi trong ngày",
    type: "khampha",
    type_name: "Văn hóa & Lịch sử",
    description: "Ngôi làng cổ đá ong độc đáo mang đậm hồn quê vùng đồng bằng Bắc Bộ xưa."
  },
  {
    id: 5,
    name: "Đảo Ngọc Phú Quốc",
    region: "nam",
    region_name: "Miền Nam",
    province: "Kiên Giang",
    cost: 3500000,
    duration: "2-3",
    duration_text: "3 ngày 2 đêm",
    type: "nghiduong",
    type_name: "Nghỉ dưỡng biển",
    description: "Bãi cát trắng mịn, nước biển trong vắt và hải sản tươi ngon bậc nhất."
  }
];

let travelFilter = {
  keyword: "",
  region: "all",
  duration: null,
  type: null
};

function formatMoney(num) {
  return Number(num).toLocaleString("vi-VN") + " ₫";
}

function renderTravelResults() {
  const grid = document.getElementById("travel-results-grid");
  const countEl = document.getElementById("travel-results-count");
  const emptyEl = document.getElementById("travel-empty");
  if (!grid) return;

  let list = [...TRAVEL_ITEMS];

  if (travelFilter.keyword) {
    const q = travelFilter.keyword.toLowerCase().trim();
    list = list.filter(t => t.name.toLowerCase().includes(q) || t.province.toLowerCase().includes(q) || t.description.toLowerCase().includes(q));
  }
  if (travelFilter.region !== "all") {
    list = list.filter(t => t.region === travelFilter.region);
  }
  if (travelFilter.duration) {
    list = list.filter(t => t.duration === travelFilter.duration);
  }
  if (travelFilter.type) {
    list = list.filter(t => t.type === travelFilter.type);
  }

  countEl.textContent = `Hiển thị ${list.length} địa điểm gợi ý`;

  if (list.length === 0) {
    grid.innerHTML = "";
    emptyEl.classList.remove("d-none");
    return;
  }
  emptyEl.classList.add("d-none");

  grid.innerHTML = list.map(item => `
    <div class="col-12 col-md-6 col-lg-4">
      <div class="dh-card travel-item-card h-100 d-flex flex-column">
        <div class="dh-card-body d-flex flex-column flex-grow-1">
          <div class="d-flex justify-content-between align-items-start mb-1">
            <h3 class="dh-section-title mb-0" style="font-size: 16px;">${item.name}</h3>
            <span class="badge bg-light text-primary border travel-card-badge">${item.region_name}</span>
          </div>

          <div class="mb-2">
            <span class="dh-small text-muted">📍 ${item.province}</span>
            <span class="mx-1 text-muted">·</span>
            <span class="badge bg-light text-dark border" style="font-size: 11px;">${item.type_name}</span>
          </div>

          <p class="dh-muted mb-3 flex-grow-1" style="font-size: 13px;">${item.description}</p>

          <div class="d-flex justify-content-between align-items-center pt-2 border-top mt-auto">
            <div>
              <strong class="travel-cost-tag">~${formatMoney(item.cost)}</strong>
              <span class="travel-duration-tag d-block">🗓 ${item.duration_text}</span>
            </div>
            <span class="dh-small text-muted">Travel P1</span>
          </div>
        </div>
      </div>
    </div>
  `).join("");
}

document.addEventListener("DOMContentLoaded", () => {
  renderTravelResults();

  // Mobile sidebar toggle
  const toggleBtn = document.querySelector("[data-sidebar-toggle]");
  const sidebar = document.querySelector(".dh-sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("is-open");
    });
  }

  // Tìm kiếm
  const searchInput = document.getElementById("travel-search-input");
  const searchBtn = document.getElementById("btn-travel-search");
  const resetBtn = document.getElementById("btn-travel-reset");
  const emptyResetBtn = document.getElementById("btn-travel-empty-reset");

  if (searchBtn && searchInput) {
    searchBtn.addEventListener("click", () => {
      travelFilter.keyword = searchInput.value;
      renderTravelResults();
    });
    searchInput.addEventListener("keyup", (e) => {
      if (e.key === "Enter") {
        travelFilter.keyword = searchInput.value;
        renderTravelResults();
      }
    });
  }

  // Chip vùng miền
  const regionChips = document.getElementById("chip-travel-regions");
  if (regionChips) {
    regionChips.addEventListener("click", (e) => {
      const chip = e.target.closest(".dh-chip");
      if (!chip) return;
      regionChips.querySelectorAll(".dh-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      travelFilter.region = chip.getAttribute("data-region");
      renderTravelResults();
    });
  }

  // Chip thời lượng & loại hình
  const typeChips = document.getElementById("chip-travel-types");
  if (typeChips) {
    typeChips.addEventListener("click", (e) => {
      const chip = e.target.closest(".dh-chip");
      if (!chip) return;
      chip.classList.toggle("active");
      const dur = chip.getAttribute("data-duration");
      const typ = chip.getAttribute("data-type");

      if (dur) travelFilter.duration = chip.classList.contains("active") ? dur : null;
      if (typ) travelFilter.type = chip.classList.contains("active") ? typ : null;

      renderTravelResults();
    });
  }

  const resetAll = () => {
    travelFilter = { keyword: "", region: "all", duration: null, type: null };
    if (searchInput) searchInput.value = "";
    if (regionChips) regionChips.querySelectorAll(".dh-chip").forEach((c, i) => c.classList.toggle("active", i === 0));
    if (typeChips) typeChips.querySelectorAll(".dh-chip").forEach(c => c.classList.remove("active"));
    renderTravelResults();
  };

  if (resetBtn) resetBtn.addEventListener("click", resetAll);
  if (emptyResetBtn) emptyResetBtn.addEventListener("click", resetAll);
});

