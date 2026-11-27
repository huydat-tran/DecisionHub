// DecisionHub Admin · Trang Dashboard
// Hiển thị số liệu tổng quan và hoạt động gần đây trong phiên quản trị.

const statFoodsEl = document.getElementById("stat-foods");
const statPlacesEl = document.getElementById("stat-places");
const activityListEl = document.getElementById("adm-activity-list");
const activityEmptyEl = document.getElementById("adm-activity-empty");
const welcomeTitleEl = document.getElementById("adm-welcome-title");

const ACTIVITY_ICONS = {
  primary: "＋",
  success: "✎",
  danger: "🗑",
};

function renderWelcome() {
  if (!welcomeTitleEl) return;
  const hour = new Date().getHours();
  const period = hour < 12 ? "Buổi sáng" : hour < 18 ? "Buổi chiều" : "Buổi tối";
  welcomeTitleEl.textContent = "Xin chào, " + ADM_ADMIN.name + " — " + period;
}

function renderStats(counts) {
  statFoodsEl.textContent = counts.foods;
  statPlacesEl.textContent = counts.places;
}

function renderActivity(items) {
  if (!items.length) {
    activityEmptyEl.hidden = false;
    activityListEl.innerHTML = "";
    return;
  }
  activityEmptyEl.hidden = true;
  activityListEl.innerHTML = items
    .map(
      (item) => `
      <div class="adm-activity-item">
        <span class="adm-activity-dot is-${item.type}" aria-hidden="true">${ACTIVITY_ICONS[item.type] || "•"}</span>
        <div class="adm-activity-text">
          <div class="adm-activity-title">${escapeHtml(item.title)}</div>
          <div class="adm-activity-time">${escapeHtml(admFormatDateTime(item.at))}</div>
        </div>
      </div>`,
    )
    .join("");
}

async function loadDashboard() {
  const counts = await admStoreCounts();
  renderStats(counts);
  renderActivity(await admStoreListActivity());
}

renderWelcome();
loadDashboard();
