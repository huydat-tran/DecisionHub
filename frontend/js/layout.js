// Layout chung: tự chèn header (menu) và footer vào mọi trang,
// để không phải copy lại HTML menu ở từng file.
//
// Mỗi trang cần có:  <body data-root="./">   (trang ở thư mục gốc)
//              hoặc  <body data-root="../">  (trang trong thư mục pages/)
// và hai thẻ rỗng:   <header id="app-header"></header> ... <footer id="app-footer"></footer>

// Thêm trang mới vào menu: thêm 1 dòng vào mảng này (đường dẫn tính từ thư mục frontend/)
const MENU = [
  { href: "index.html", label: "Trang chủ" },
  { href: "pages/items.html", label: "Items (CRUD mẫu)" },
  { href: "demo-design-system.html", label: "Giao diện mẫu (Demo)" },
];

function renderLayout() {
  const root = document.body.dataset.root || "./";
  const currentPath = window.location.pathname.replace(/\\/g, "/");

  const links = MENU.map((item) => {
    const isActive = currentPath.endsWith("/" + item.href) ||
      (item.href === "index.html" && (currentPath.endsWith("/") || currentPath.endsWith("/frontend/")));
    return `<a href="${root}${item.href}" class="${isActive ? "active" : ""}">${item.label}</a>`;
  }).join("");

  const header = document.getElementById("app-header");
  if (header) {
    header.innerHTML = `
      <div class="container header-inner">
        <a href="${root}index.html" class="brand">
          <img src="${root}assets/images/logo.svg" alt="logo" width="28" height="28">
          <span>${CONFIG.APP_NAME || "DecisionHub"}</span>
        </a>
        <nav class="nav">${links}</nav>
      </div>`;
  }

  const footer = document.getElementById("app-footer");
  if (footer) {
    footer.innerHTML = `
      <div class="container">© ${new Date().getFullYear()} HN-KS25-CNTT1 · Base code thực tập doanh nghiệp</div>`;
  }
}

renderLayout();
