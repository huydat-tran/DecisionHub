// ==========================================================
// JS riêng cho phân hệ History (Lịch sử hoạt động)
// Dựa trên DecisionHub.md Mục 6.1 & UI Guidelines
// ==========================================================

let HISTORY_ITEMS = [
  {
    id: 1,
    time: "Hôm nay, 12:15",
    type: "food",
    typeName: "Food (Món ăn)",
    criteria: "Bữa trưa · Dưới 50.000đ · Nhanh < 15p",
    result: "Cơm Tấm Sườn Bì Chả (Điểm WSM: 88)"
  },
  {
    id: 2,
    time: "Hôm nay, 08:30",
    type: "food",
    typeName: "Food (Món ăn)",
    criteria: "Bữa sáng · Tìm từ khóa \"Phở bò\"",
    result: "Phở Bò Tái Nạm (45.000đ)"
  },
  {
    id: 3,
    time: "Hôm qua, 19:40",
    type: "travel",
    typeName: "Travel (Du lịch)",
    criteria: "Miền Trung · Nghỉ dưỡng · 2 - 3 ngày",
    result: "Phố cổ Hội An (~1.200.000đ)"
  },
  {
    id: 4,
    time: "09/11/2026, 14:20",
    type: "travel",
    typeName: "Travel (Du lịch)",
    criteria: "Miền Bắc · Khám phá thiên nhiên · 1 - 2 ngày",
    result: "Vịnh Hạ Long (~1.500.000đ)"
  }
];

let selectedFilter = "all";

function renderHistoryTable() {
  const tbody = document.getElementById("history-table-body");
  const emptyEl = document.getElementById("history-empty");
  if (!tbody) return;

  let list = [...HISTORY_ITEMS];
  if (selectedFilter !== "all") {
    list = list.filter(item => item.type === selectedFilter);
  }

  if (list.length === 0) {
    tbody.innerHTML = "";
    if (emptyEl) emptyEl.classList.remove("d-none");
    return;
  }
  if (emptyEl) emptyEl.classList.add("d-none");

  tbody.innerHTML = list.map(item => {
    const badgeClass = item.type === "food" ? "history-badge-food" : "history-badge-travel";
    return `
      <tr>
        <td style="color: var(--dh-text-muted);">${item.time}</td>
        <td><span class="badge ${badgeClass} px-2 py-1">${item.typeName}</span></td>
        <td>${item.criteria}</td>
        <td><strong>${item.result}</strong></td>
        <td style="text-align: right;">
          <button class="dh-btn dh-btn-sm dh-btn-outline btn-delete-row" data-id="${item.id}" style="padding: 2px 8px; font-size: 12px;">Xóa</button>
        </td>
      </tr>
    `;
  }).join("");

  document.querySelectorAll(".btn-delete-row").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = Number(btn.getAttribute("data-id"));
      HISTORY_ITEMS = HISTORY_ITEMS.filter(it => it.id !== id);
      renderHistoryTable();
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  renderHistoryTable();

  // Mobile sidebar toggle
  const toggleBtn = document.querySelector("[data-sidebar-toggle]");
  const sidebar = document.querySelector(".dh-sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("is-open");
    });
  }

  // Filter chips (Tất cả / Food / Travel)
  const chips = document.getElementById("history-filter-chips");
  if (chips) {
    chips.addEventListener("click", (e) => {
      const chip = e.target.closest(".dh-chip");
      if (!chip) return;
      chips.querySelectorAll(".dh-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      selectedFilter = chip.getAttribute("data-type");
      renderHistoryTable();
    });
  }

  // Xóa toàn bộ lịch sử
  const clearBtn = document.getElementById("btn-clear-history");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (confirm("Bạn có chắc chắn muốn xóa toàn bộ lịch sử hoạt động không?")) {
        HISTORY_ITEMS = [];
        renderHistoryTable();
      }
    });
  }
});

