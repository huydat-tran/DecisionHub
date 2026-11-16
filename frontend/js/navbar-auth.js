// Quản lý khu vực tài khoản ở navbar (góc trên phải).
//
// - Đã đăng nhập  -> hiện avatar + tên người dùng (link tới trang Hồ sơ cá nhân)
// - Chưa đăng nhập -> ẩn avatar, hiện nút "Đăng nhập"
//
// Trang Hồ sơ cá nhân tự điều khiển (đặt <body data-navbar-auth="skip">)
// nên không bị init() gọi thêm một lần nữa.

(function (global) {
  const TOKEN_STORAGE_KEY = "token";

  function chip() {
    return document.querySelector("[data-user-chip]");
  }

  function loginButton() {
    return document.querySelector("[data-login-btn]");
  }

  // "Nguyễn Văn An" -> "NVA"; "an" -> "AN"
  function toMonogram(username) {
    const parts = String(username || "").trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return "DH";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  // Chưa đăng nhập: chỉ hiện nút Đăng nhập, ẩn avatar.
  function showLogin() {
    const userChip = chip();
    if (userChip) userChip.classList.add("d-none");

    const button = loginButton();
    if (button) button.classList.remove("d-none");
  }

  // Đã đăng nhập: hiện avatar + tên người dùng, ẩn nút Đăng nhập.
  function showUser(profile) {
    const button = loginButton();
    if (button) button.classList.add("d-none");

    const userChip = chip();
    if (!userChip) return;
    userChip.classList.remove("d-none");

    if (!profile) return;

    const avatar = userChip.querySelector("[data-user-avatar]");
    const name = userChip.querySelector("[data-user-name]");
    const role = userChip.querySelector("[data-user-role]");

    if (avatar) avatar.textContent = toMonogram(profile.username);
    if (name) name.textContent = profile.username;
    if (role) role.textContent = profile.role;
  }

  // Đọc hồ sơ từ backend để điền tên/avatar. Token hết hạn -> xoá token.
  async function init() {
    if (!localStorage.getItem(TOKEN_STORAGE_KEY)) {
      showLogin();
      return;
    }

    try {
      const response = await api.get("/users/me");
      showUser(response.data);
    } catch (error) {
      if (error && error.status === 401) {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
      }
      showLogin();
    }
  }

  global.DHNavbarAuth = { showLogin, showUser, init, toMonogram };

  const body = document.body;
  if (body && body.dataset.navbarAuth !== "skip") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", init);
    } else {
      init();
    }
  }
})(window);
