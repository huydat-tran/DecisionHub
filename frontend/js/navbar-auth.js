// Quản lý khu vực tài khoản ở navbar (góc trên phải).
//
// - Đã đăng nhập  -> hiện avatar + tên người dùng, nhấn vào mở dropdown
//                   (Username, Email, Hồ sơ cá nhân, Đăng xuất)
// - Chưa đăng nhập -> hiện nút "Đăng nhập" và "Đăng ký"
//
// Thông tin người dùng lấy từ API GET /users/me (không hardcode).
// Token hết hạn -> API trả 401, api.js tự xoá token và báo cho trang này.

(function (global) {
  const ACCOUNT_MENU_CLASS = "dh-account-menu";
  let eventsBound = false;

  function chip() {
    return document.querySelector("[data-user-chip]");
  }

  function loginButton() {
    return document.querySelector("[data-login-btn]");
  }

  function registerButton() {
    return document.querySelector("[data-register-btn]");
  }

  // "Nguyễn Văn An" -> "NVA"; "an" -> "AN"
  function toMonogram(username) {
    const parts = String(username || "").trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return "DH";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  // Đường dẫn tương đối tới 1 trang nằm trong frontend/.
  function relativeUrl(target) {
    return api.appUrl(target);
  }

  // ----- Menu tài khoản (dropdown) -----

  function dropdown() {
    return document.querySelector("[data-account-dropdown]");
  }

  // Tạo dropdown một lần, gắn vào ngay sau nút avatar.
  function buildDropdown() {
    if (dropdown()) return dropdown();

    const userChip = chip();
    if (!userChip) return null;

    const wrapper = document.createElement("div");
    wrapper.className = ACCOUNT_MENU_CLASS;
    userChip.parentNode.insertBefore(wrapper, userChip);
    wrapper.appendChild(userChip);

    const panel = document.createElement("div");
    panel.className = "dh-account-dropdown d-none";
    panel.setAttribute("data-account-dropdown", "");
    panel.innerHTML = `
      <div class="dh-account-info">
        <strong class="dh-account-username" data-account-username></strong>
        <span class="dh-account-email" data-account-email></span>
      </div>
      <a class="dh-account-item" href="${relativeUrl("pages/profile.html")}">Hồ sơ cá nhân</a>
      <button type="button" class="dh-account-item dh-account-logout" data-logout-btn>Đăng xuất</button>`;
    wrapper.appendChild(panel);

    return panel;
  }

  function closeDropdown() {
    const panel = dropdown();
    if (panel) panel.classList.add("d-none");
    const userChip = chip();
    if (userChip) userChip.setAttribute("aria-expanded", "false");
  }

  function toggleDropdown() {
    const panel = dropdown();
    if (!panel) return;
    const willOpen = panel.classList.contains("d-none");
    panel.classList.toggle("d-none", !willOpen);
    const userChip = chip();
    if (userChip) userChip.setAttribute("aria-expanded", String(willOpen));
  }

  // ----- Trạng thái Guest -----

  // Nút "Đăng ký" nằm cạnh nút "Đăng nhập" (chỉ hiện khi là Guest).
  function ensureRegisterButton() {
    let button = registerButton();
    if (button) return button;

    const loginBtn = loginButton();
    if (!loginBtn) return null;

    button = document.createElement("a");
    button.className = "dh-btn dh-btn-sm dh-btn-outline";
    button.style.textDecoration = "none";
    button.setAttribute("data-register-btn", "");
    button.href = relativeUrl("pages/signup.html") + "?mode=register";
    button.textContent = "Đăng ký";
    loginBtn.parentNode.insertBefore(button, loginBtn.nextSibling);
    return button;
  }

  // Chưa đăng nhập: ẩn avatar + dropdown, hiện nút Đăng nhập / Đăng ký.
  function showLogin() {
    const userChip = chip();
    if (userChip) {
      userChip.classList.add("d-none");
      userChip.removeAttribute("href");
    }
    closeDropdown();

    ensureRegisterButton();

    const loginBtn = loginButton();
    if (loginBtn) loginBtn.classList.remove("d-none");

    const regBtn = registerButton();
    if (regBtn) regBtn.classList.remove("d-none");
  }

  // ----- Trạng thái User -----

  // Đã đăng nhập: hiện avatar + tên người dùng, ẩn nút Đăng nhập / Đăng ký.
  function showUser(profile) {
    const loginBtn = loginButton();
    if (loginBtn) loginBtn.classList.add("d-none");

    const regBtn = registerButton();
    if (regBtn) regBtn.classList.add("d-none");

    const userChip = chip();
    if (!userChip) return;
    userChip.classList.remove("d-none");
    userChip.href = relativeUrl("pages/profile.html");
    userChip.setAttribute("aria-haspopup", "true");
    userChip.setAttribute("aria-expanded", "false");

    if (!profile) return;

    const avatar = userChip.querySelector("[data-user-avatar]");
    const name = userChip.querySelector("[data-user-name]");
    const role = userChip.querySelector("[data-user-role]");

    if (avatar) avatar.textContent = toMonogram(profile.username);
    if (name) name.textContent = profile.username;
    if (role) role.textContent = profile.role;

    const username = document.querySelector("[data-account-username]");
    if (username) username.textContent = profile.username;
    const email = document.querySelector("[data-account-email]");
    if (email) email.textContent = profile.email;
  }

  // ----- Đăng xuất -----

  function logout() {
    api.session.clear();
    showLogin();
    closeDropdown();
    window.location.href = relativeUrl("demo-design-system.html");
  }

  // ----- Sự kiện -----

  function bindEvents() {
    if (eventsBound) return;
    eventsBound = true;

    document.addEventListener("click", (event) => {
      const userChip = chip();
      if (userChip && userChip.contains(event.target)) {
        event.preventDefault();
        toggleDropdown();
        return;
      }
      if (!event.target.closest("." + ACCOUNT_MENU_CLASS)) closeDropdown();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeDropdown();
    });

    const logoutBtn = document.querySelector("[data-logout-btn]");
    if (logoutBtn) logoutBtn.addEventListener("click", logout);

    // Token hết hạn -> api.js xoá phiên -> cập nhật lại giao diện về Guest.
    api.session.subscribe((user) => {
      if (!user) showLogin();
    });
  }

  // ----- Khởi tạo -----

  // Gắn dropdown + sự kiện và hiển thị tài khoản từ hồ sơ đã có sẵn.
  // Dùng cho trang tự tải hồ sơ riêng (Profile).
  function mount(profile) {
    buildDropdown();
    bindEvents();
    if (profile) showUser(profile);
    else showLogin();
  }

  // Đọc hồ sơ từ backend để điền tên/avatar/email.
  async function init() {
    buildDropdown();
    bindEvents();

    if (!api.session.isLoggedIn()) {
      api.session.clear();
      showLogin();
      return;
    }

    try {
      const response = await api.get("/users/me", undefined, { authMode: "optional" });
      api.session.setUser(response.data);
      showUser(response.data);
    } catch (error) {
      // 401 do token hết hạn: api.js đã xoá token, chỉ cần về trạng thái Guest.
      api.session.clear();
      showLogin();
    }
  }

  global.DHNavbarAuth = { showLogin, showUser, mount, init, logout, toMonogram };

  const body = document.body;
  if (body && body.dataset.navbarAuth !== "skip") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }
})(window);
