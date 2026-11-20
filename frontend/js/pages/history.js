// ==========================================================
// Module: History (Lịch sử hoạt động)
// Quản lý và hiển thị lịch sử tìm kiếm & gợi ý từ localStorage
// ==========================================================

(function () {
  const STORAGE_KEY = "dh_decision_history";
  const tableBody = document.getElementById("history-table-body");
  const emptyState = document.getElementById("history-empty");
  const clearBtn = document.getElementById("btn-clear-history");
  const filterChips = document.getElementById("history-filter-chips");

  let currentFilter = "all";

  function getHistoryList() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  function saveHistoryList(list) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    } catch (err) {
      console.warn("Lỗi lưu lịch sử:", err);
    }
  }

  function renderHistory() {
    if (!tableBody || !emptyState) return;

    const list = getHistoryList();
    const filtered = currentFilter === "all"
      ? list
      : list.filter((item) => item.module === currentFilter);

    if (filtered.length === 0) {
      tableBody.innerHTML = "";
      emptyState.classList.remove("d-none");
      return;
    }

    emptyState.classList.add("d-none");
    tableBody.innerHTML = filtered
      .map((item, idx) => {
        const timeStr = typeof formatDateTime === "function"
          ? formatDateTime(item.createdAt)
          : new Date(item.createdAt).toLocaleString("vi-VN");

        const isFood = item.module === "food";
        const badgeClass = isFood ? "bg-success text-white" : "bg-primary text-white";
        const badgeLabel = item.moduleLabel || (isFood ? "Gợi ý Món ăn" : "Du lịch");

        let actionUrl = "#";
        if (isFood && item.budget_max) {
          const params = new URLSearchParams();
          params.set("budget_max", item.budget_max);
          if (item.meal_type) params.set("meal_type", item.meal_type);
          if (item.avoid_ingredients && item.avoid_ingredients.length) {
            params.set("avoid", item.avoid_ingredients.join(","));
          }
          actionUrl = `food-results.html?${params.toString()}`;
        }

        return `
          <tr>
            <td class="text-nowrap dh-small dh-muted">${escapeHtml(timeStr)}</td>
            <td>
              <span class="badge ${badgeClass}" style="font-weight: 500; font-size: 11px; padding: 4px 8px;">
                ${escapeHtml(badgeLabel)}
              </span>
            </td>
            <td class="dh-small">
              <strong>${escapeHtml(item.criteriaSummary || "Tiêu chí đã chọn")}</strong>
            </td>
            <td class="dh-small">
              <span class="text-success fw-bold">${escapeHtml(item.resultSummary || "–")}</span>
              <span class="dh-muted ms-1" style="font-size: 11px;">(${item.total || 0} món)</span>
            </td>
            <td class="text-end">
              <a href="${actionUrl}" class="dh-btn dh-btn-sm dh-btn-outline py-1 px-2 text-nowrap" style="font-size: 12px; text-decoration: none;">
                Xem lại
              </a>
            </td>
          </tr>
        `;
      })
      .join("");
  }

  // Lắng nghe sự kiện lọc theo Chips
  if (filterChips) {
    filterChips.addEventListener("click", (event) => {
      const chip = event.target.closest(".dh-chip");
      if (!chip) return;

      filterChips.querySelectorAll(".dh-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      currentFilter = chip.dataset.type || "all";
      renderHistory();
    });
  }

  // Xóa toàn bộ lịch sử
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (confirm("Bạn có chắc chắn muốn xóa toàn bộ lịch sử hoạt động không?")) {
        localStorage.removeItem(STORAGE_KEY);
        renderHistory();
        if (typeof showToast === "function") {
          showToast("Đã xóa sạch lịch sử hoạt động.", "success");
        }
      }
    });
  }

  // Khởi chạy khi tải trang
  document.addEventListener("DOMContentLoaded", renderHistory);
  renderHistory();
})();

