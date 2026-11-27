// DecisionHub Admin · Layout dùng chung cho mọi trang Admin.
// Mỗi trang khai báo: <body data-page="dashboard" data-title="Tổng quan" data-crumb="Tổng quan">
// Trang này tự chèn Sidebar + Header để không lặp lại HTML giữa các file.

const ADM_NAV = [
  { id: "dashboard", href: "dashboard.html", label: "Dashboard", icon: "◈" },
  { id: "foods", href: "foods.html", label: "Quản lý món ăn", icon: "🍜" },
  { id: "places", href: "places.html", label: "Quản lý du lịch", icon: "📍" },
];

const ADM_ADMIN = { name: "Quản trị viên", role: "Administrator" };

function renderAdminLayout() {
  const body = document.body;
  const page = body.dataset.page || "";
  const title = body.dataset.title || "Dashboard";
  const crumb = body.dataset.crumb || "";

  const navLinks = ADM_NAV.map(
    (item) => `
      <a class="adm-nav-link${item.id === page ? " active" : ""}" href="${item.href}"${
        item.id === page ? ' aria-current="page"' : ""
      }>
        <span class="adm-nav-icon" aria-hidden="true">${item.icon}</span>
        <span>${item.label}</span>
      </a>`,
  ).join("");

  const sidebar = document.getElementById("adm-sidebar");
  if (sidebar) {
    sidebar.innerHTML = `
      <a class="adm-brand" href="dashboard.html">
        <span class="adm-brand-mark" aria-hidden="true">D</span>
        <span class="adm-brand-text">
          <span class="adm-brand-name">DecisionHub</span>
          <span class="adm-brand-role">Admin Console</span>
        </span>
      </a>
      <div class="adm-nav-label">Quản trị</div>
      <nav class="adm-nav" aria-label="Điều hướng Admin">${navLinks}</nav>
      <div class="adm-sidebar-bottom">
        <div class="adm-profile">
          <span class="adm-avatar" aria-hidden="true">QT</span>
          <span class="adm-profile-info">
            <span class="adm-profile-name">${ADM_ADMIN.name}</span>
            <span class="adm-profile-role">${ADM_ADMIN.role}</span>
          </span>
        </div>
      </div>`;
  }

  const header = document.getElementById("adm-header");
  if (header) {
    header.innerHTML = `
      <div class="adm-header-left">
        <button type="button" class="adm-icon-button d-lg-none" data-sidebar-toggle aria-label="Mở menu" aria-expanded="false">☰</button>
        <div>
          ${
            crumb
              ? `<ol class="adm-breadcrumb">
                   <li><a href="dashboard.html">Admin</a></li>
                   <li class="adm-breadcrumb-current">${crumb}</li>
                 </ol>`
              : ""
          }
          <h1 class="adm-page-title">${title}</h1>
        </div>
      </div>
      <div class="adm-header-right">
        <button type="button" class="adm-btn adm-btn-ghost adm-btn-sm" data-logout>Đăng xuất</button>
      </div>`;
  }
}

function bindAdminLayout() {
  const sidebar = document.getElementById("adm-sidebar");
  const backdrop = document.getElementById("adm-backdrop");
  const toggle = document.querySelector("[data-sidebar-toggle]");
  const logoutBtn = document.querySelector("[data-logout]");

  const setOpen = (open) => {
    if (!sidebar) return;
    sidebar.classList.toggle("is-open", open);
    if (backdrop) backdrop.classList.toggle("show", open);
    if (toggle) toggle.setAttribute("aria-expanded", String(open));
  };

  if (toggle) toggle.addEventListener("click", () => setOpen(!sidebar.classList.contains("is-open")));
  if (backdrop) backdrop.addEventListener("click", () => setOpen(false));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setOpen(false);
  });

  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      const confirmed = await admConfirm({
        title: "Đăng xuất khỏi DecisionHub?",
        text: "Phiên quản trị hiện tại sẽ kết thúc.",
        confirmText: "Đăng xuất",
        cancelText: "Hủy",
      });
      if (!confirmed) return;
      admToast("Đã đăng xuất khỏi giao diện quản trị.", "success");
      setOpen(false);
    });
  }
}

renderAdminLayout();
bindAdminLayout();
