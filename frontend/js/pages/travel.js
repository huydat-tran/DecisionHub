// =============================================================================
// Phân hệ Travel (WhereShouldITravel) - Client Prototype
// Quản lý form nhập ngân sách, thời lượng, sở thích và hiển thị kết quả gợi ý
// =============================================================================

(function () {
  "use strict";

  // Dữ liệu mẫu các điểm đến du lịch (chuẩn hóa theo schema backend & assets sẵn có)
  const TRAVEL_DESTINATIONS = [
    {
      id: 1,
      name: "Phố cổ Hội An",
      province: "Quảng Nam",
      region: "trung",
      regionName: "Miền Trung",
      cost: 1500000,
      duration: "2-3",
      durationText: "2 - 3 ngày",
      preferences: ["van-hoa", "chua-lanh"],
      preferenceLabels: ["🏛️ Văn hóa di sản", "🌿 Chữa lành"],
      rating: 4.8,
      wsmScore: 88.5,
      description: "Đô thị cổ được UNESCO công nhận là Di sản Thế giới với những ngôi nhà sơn vàng, đèn lồng rực rỡ và ẩm thực đặc sắc.",
      image: "../assets/images/travel/hoian.jpg",
    },
    {
      id: 2,
      name: "Vịnh Hạ Long",
      province: "Quảng Ninh",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 3200000,
      duration: "2-3",
      durationText: "2 - 3 ngày",
      preferences: ["thien-nhien", "bien"],
      preferenceLabels: ["🌲 Thiên nhiên kỳ vĩ", "🏖️ Nghỉ dưỡng biển"],
      rating: 4.9,
      wsmScore: 86.8,
      description: "Kỳ quan thiên nhiên thế giới sở hữu hàng nghìn đảo đá vôi kỳ thú, trải nghiệm du thuyền ngủ đêm và chèo kayak.",
      image: "../assets/images/travel/halong.jpg",
    },
    {
      id: 3,
      name: "Đà Lạt ngàn hoa",
      province: "Lâm Đồng",
      region: "tay-nguyen",
      regionName: "Tây Nguyên",
      cost: 2200000,
      duration: "2-3",
      durationText: "2 - 3 ngày",
      preferences: ["chua-lanh", "giai-tri", "thien-nhien"],
      preferenceLabels: ["🌿 Nghỉ dưỡng & Chill", "🎡 Check-in sống ảo"],
      rating: 4.7,
      wsmScore: 84.2,
      description: "Khí hậu mát mẻ quanh năm, cảnh quan đồi thông săn mây lãng mạn cùng vô số quán cà phê đẹp và homestay hợp túi tiền.",
      image: "../assets/images/travel/dalat.jpg",
    },
    {
      id: 4,
      name: "Đảo ngọc Phú Quốc",
      province: "Kiên Giang",
      region: "nam",
      regionName: "Miền Nam",
      cost: 4500000,
      duration: "4-5",
      durationText: "4 - 5 ngày",
      preferences: ["bien", "giai-tri"],
      preferenceLabels: ["🏖️ Nghỉ dưỡng biển", "🎡 Vui chơi giải trí"],
      rating: 4.8,
      wsmScore: 81.6,
      description: "Bãi cát trắng mịn, ngắm hoàng hôn đẹp nhất Việt Nam, tổ hợp vui chơi VinWonders và cáp treo Hòn Thơm vượt biển.",
      image: "../assets/images/travel/phuquoc.jpg",
    },
    {
      id: 5,
      name: "Quần thể danh thắng Tràng An",
      province: "Ninh Bình",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 850000,
      duration: "1",
      durationText: "Đi trong ngày",
      preferences: ["thien-nhien", "van-hoa"],
      preferenceLabels: ["🌲 Thiên nhiên", "🏛️ Di sản kép"],
      rating: 4.9,
      wsmScore: 79.4,
      description: "Di sản thế giới kép đầu tiên tại Đông Nam Á với non nước kỳ vĩ, hệ thống hang động tự nhiên và phim trường Kong.",
      image: "../assets/images/travel/trangan.jpg",
    },
    {
      id: 6,
      name: "Sa Pa & Đỉnh Fansipan",
      province: "Lào Cai",
      region: "bac",
      regionName: "Miền Bắc",
      cost: 2600000,
      duration: "2-3",
      durationText: "2 - 3 ngày",
      preferences: ["thien-nhien", "giai-tri"],
      preferenceLabels: ["🌲 Khám phá thiên nhiên", "🎡 Check-in Fansipan"],
      rating: 4.8,
      wsmScore: 83.0,
      description: "Chinh phục nóc nhà Đông Dương, chiêm ngưỡng ruộng bậc thang Mường Hoa và trải nghiệm văn hóa bản sắc vùng cao Tây Bắc.",
      image: "../assets/images/travel/halong.jpg",
    },
    {
      id: 7,
      name: "Mũi Né - Đồi Cát Bay",
      province: "Bình Thuận",
      region: "nam",
      regionName: "Miền Nam",
      cost: 1800000,
      duration: "2-3",
      durationText: "2 - 3 ngày",
      preferences: ["bien", "giai-tri"],
      preferenceLabels: ["🏖️ Biển xanh nắng vàng", "🎡 Lái xe địa hình"],
      rating: 4.6,
      wsmScore: 78.5,
      description: "Thiên đường nghỉ dưỡng với những đồi cát mênh mông đổi màu theo giờ, thể thao lướt sóng và hải sản tươi ngon giá rẻ.",
      image: "../assets/images/travel/phuquoc.jpg",
    },
    {
      id: 8,
      name: "Cố đô Huế",
      province: "Thừa Thiên Huế",
      region: "trung",
      regionName: "Miền Trung",
      cost: 1200000,
      duration: "2-3",
      durationText: "2 - 3 ngày",
      preferences: ["van-hoa", "chua-lanh"],
      preferenceLabels: ["🏛️ Di sản cố đô", "🌿 Thơ mộng & Chữa lành"],
      rating: 4.7,
      wsmScore: 82.1,
      description: "Quần thể di tích Cố đô trầm mặc, Đại Nội uy nghiêm, nghe ca Huế trên sông Hương và thưởng thức ẩm thực cung đình thanh tao.",
      image: "../assets/images/travel/hoian.jpg",
    },
  ];

  // Trạng thái bộ lọc
  const filterState = {
    keyword: "",
    region: "all",
    budgetRange: "all",
    maxBudget: null,
    duration: "all",
    preference: "all",
  };

  // DOM Elements
  const searchInput = document.getElementById("travel-search-input");
  const maxBudgetInput = document.getElementById("travel-max-budget");
  const durationSelect = document.getElementById("travel-duration-select");
  const preferenceSelect = document.getElementById("travel-preference-select");
  const btnSearch = document.getElementById("btn-travel-search");
  const btnReset = document.getElementById("btn-travel-reset");
  const btnEmptyReset = document.getElementById("btn-travel-empty-reset");

  const regionChips = document.querySelectorAll("#chip-travel-regions .dh-chip");
  const budgetChips = document.querySelectorAll("#chip-travel-budgets .dh-chip");

  const resultsGrid = document.getElementById("travel-results-grid");
  const resultsCount = document.getElementById("travel-results-count");
  const emptyState = document.getElementById("travel-empty");

  // Kiểm tra điểm đến có thỏa mãn điều kiện ngân sách hay không
  function matchBudget(item) {
    // 1. Nếu người dùng nhập trực tiếp số tiền ở ô input
    if (filterState.maxBudget && filterState.maxBudget > 0) {
      return item.cost <= filterState.maxBudget;
    }

    // 2. Hoặc nếu người dùng chọn chip khoảng giá nhanh
    switch (filterState.budgetRange) {
      case "1000000":
        return item.cost <= 1000000;
      case "3000000":
        return item.cost >= 1000000 && item.cost <= 3000000;
      case "5000000":
        return item.cost >= 3000000 && item.cost <= 5000000;
      case "5000001":
        return item.cost > 5000000;
      default:
        return true;
    }
  }

  // Lọc danh sách điểm đến dựa trên toàn bộ tiêu chí
  function filterDestinations() {
    return TRAVEL_DESTINATIONS.filter((item) => {
      // 1. Từ khóa (tên điểm đến hoặc tỉnh thành)
      if (filterState.keyword) {
        const kw = filterState.keyword.toLowerCase().trim();
        const matchName = item.name.toLowerCase().includes(kw);
        const matchProv = item.province.toLowerCase().includes(kw);
        if (!matchName && !matchProv) return false;
      }

      // 2. Vùng miền
      if (filterState.region !== "all" && item.region !== filterState.region) {
        return false;
      }

      // 3. Ngân sách
      if (!matchBudget(item)) {
        return false;
      }

      // 4. Thời lượng
      if (filterState.duration !== "all" && item.duration !== filterState.duration) {
        return false;
      }

      // 5. Sở thích
      if (filterState.preference !== "all" && !item.preferences.includes(filterState.preference)) {
        return false;
      }

      return true;
    });
  }

  // Render danh sách thẻ điểm đến
  function renderResults(list) {
    if (!resultsGrid || !emptyState || !resultsCount) return;

    if (list.length === 0) {
      resultsGrid.innerHTML = "";
      emptyState.classList.remove("d-none");
      resultsCount.textContent = "Không tìm thấy điểm đến nào phù hợp";
      return;
    }

    emptyState.classList.add("d-none");
    resultsCount.textContent = `Tìm thấy ${list.length} địa điểm gợi ý phù hợp`;

    const html = list
      .map((item) => {
        const safeName = typeof escapeHtml === "function" ? escapeHtml(item.name) : item.name;
        const safeProv = typeof escapeHtml === "function" ? escapeHtml(item.province) : item.province;
        const safeDesc = typeof escapeHtml === "function" ? escapeHtml(item.description) : item.description;
        const formattedCost = typeof formatMoney === "function" ? formatMoney(item.cost) : item.cost.toLocaleString("vi-VN") + " ₫";

        const tagsHtml = item.preferenceLabels
          .map((label) => `<span class="travel-tag-pill">${escapeHtml(label)}</span>`)
          .join(" ");

        return `
          <div class="col-12 col-md-6 col-xl-3">
            <article class="travel-item-card" aria-label="${safeName}">
              <!-- Ảnh đại diện & badges -->
              <div class="travel-card-media">
                <img
                  src="${item.image}"
                  alt="${safeName}"
                  class="travel-card-img"
                  loading="lazy"
                  onerror="this.src='../assets/images/travel/dalat.jpg'"
                >
                <span class="travel-floating-badge">★ ${item.wsmScore ? item.wsmScore.toFixed(1) : item.rating}</span>
                <span class="travel-region-pill">${escapeHtml(item.regionName)}</span>
              </div>

              <!-- Nội dung thẻ -->
              <div class="travel-card-body">
                <h3 class="travel-card-title">${safeName}</h3>
                <div class="travel-card-location">
                  <span>📍</span>
                  <span>${safeProv}</span>
                </div>

                <!-- Thông số ngân sách & thời lượng -->
                <div class="travel-card-specs">
                  <div>
                    <div class="travel-cost-lbl">Ngân sách ước tính</div>
                    <div class="travel-cost-val">${formattedCost}</div>
                  </div>
                  <div class="text-end">
                    <div class="travel-cost-lbl">Thời lượng</div>
                    <div class="travel-duration-val">⏱️ ${escapeHtml(item.durationText)}</div>
                  </div>
                </div>

                <!-- Tags sở thích -->
                <div class="travel-tags-wrap">
                  ${tagsHtml}
                </div>

                <!-- Mô tả tóm tắt -->
                <p class="travel-card-desc">${safeDesc}</p>

                <!-- Footer hành động -->
                <div class="travel-card-footer">
                  <div class="travel-rating-box">
                    <span class="travel-rating-star">⭐</span>
                    <span>${item.rating} / 5.0</span>
                  </div>
                  <a href="travel-results.html" class="dh-btn dh-btn-sm dh-btn-outline" style="text-decoration:none;">
                    Chi tiết đề xuất →
                  </a>
                </div>
              </div>
            </article>
          </div>
        `;
      })
      .join("");

    resultsGrid.innerHTML = html;
  }

  // Áp dụng bộ lọc và render lại
  function applyFilter() {
    const filtered = filterDestinations();
    renderResults(filtered);
  }

  // Đặt lại toàn bộ form về mặc định
  function resetFilter() {
    filterState.keyword = "";
    filterState.region = "all";
    filterState.budgetRange = "all";
    filterState.maxBudget = null;
    filterState.duration = "all";
    filterState.preference = "all";

    if (searchInput) searchInput.value = "";
    if (maxBudgetInput) maxBudgetInput.value = "";
    if (durationSelect) durationSelect.value = "all";
    if (preferenceSelect) preferenceSelect.value = "all";

    regionChips.forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.region === "all");
    });

    budgetChips.forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.budget === "all");
    });

    applyFilter();
    if (typeof showToast === "function") {
      showToast("Đã đặt lại bộ lọc tìm kiếm", "success");
    }
  }

  // Gắn sự kiện tương tác
  function initEvents() {
    // 1. Ô tìm kiếm từ khóa
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        filterState.keyword = e.target.value;
        applyFilter();
      });
      searchInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          applyFilter();
        }
      });
    }

    // 2. Nhập ngân sách tối đa
    if (maxBudgetInput) {
      maxBudgetInput.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        filterState.maxBudget = val ? Number(val) : null;
        // Bỏ active ở các chip khoảng giá nếu tự nhập tay
        if (val) {
          filterState.budgetRange = "custom";
          budgetChips.forEach((c) => c.classList.remove("active"));
        } else {
          filterState.budgetRange = "all";
          const allChip = document.querySelector("#chip-travel-budgets [data-budget='all']");
          if (allChip) allChip.classList.add("active");
        }
        applyFilter();
      });
    }

    // 3. Chip ngân sách nhanh
    budgetChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        budgetChips.forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");

        filterState.budgetRange = chip.dataset.budget;
        filterState.maxBudget = null;
        if (maxBudgetInput) maxBudgetInput.value = "";

        applyFilter();
      });
    });

    // 4. Chip vùng miền
    regionChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        regionChips.forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");

        filterState.region = chip.dataset.region;
        applyFilter();
      });
    });

    // 5. Select thời lượng
    if (durationSelect) {
      durationSelect.addEventListener("change", (e) => {
        filterState.duration = e.target.value;
        applyFilter();
      });
    }

    // 6. Select sở thích
    if (preferenceSelect) {
      preferenceSelect.addEventListener("change", (e) => {
        filterState.preference = e.target.value;
        applyFilter();
      });
    }

    // 7. Nút tìm kiếm & nút đặt lại
    if (btnSearch) {
      btnSearch.addEventListener("click", () => {
        applyFilter();
        if (typeof showToast === "function") {
          showToast("Đã cập nhật kết quả tìm kiếm", "success");
        }
      });
    }

    if (btnReset) {
      btnReset.addEventListener("click", resetFilter);
    }

    if (btnEmptyReset) {
      btnEmptyReset.addEventListener("click", resetFilter);
    }

    // 8. Đóng/mở sidebar trên màn hình di động
    const sidebarEl = document.querySelector(".dh-sidebar");
    const sidebarToggleEl = document.querySelector("[data-sidebar-toggle]");
    if (sidebarToggleEl && sidebarEl) {
      sidebarToggleEl.addEventListener("click", () => {
        const isOpen = sidebarEl.classList.toggle("is-open");
        sidebarToggleEl.setAttribute("aria-expanded", String(isOpen));
      });
      document.addEventListener("click", (event) => {
        if (event.target.closest(".dh-sidebar, [data-sidebar-toggle]")) return;
        sidebarEl.classList.remove("is-open");
        sidebarToggleEl.setAttribute("aria-expanded", "false");
      });
    }
  }

  // Khởi chạy khi tài liệu sẵn sàng
  document.addEventListener("DOMContentLoaded", () => {
    initEvents();
    applyFilter();
  });
})();
