// Trang Hồ sơ cá nhân (Profile) – module Users.
// API: GET /users/me (đọc), PATCH /users/me (chỉ cho phép đổi username).
// Backend trả { success, message, data: { id, username, email, role, created_at } }.

const USERNAME_MIN_LENGTH = 5;
const USERNAME_MAX_LENGTH = 50;

let currentProfile = null;
let isEditing = false;

const els = {
  content: document.getElementById("profile-content"),
  authRequired: document.getElementById("profile-auth-required"),
  errorBox: document.getElementById("profile-error"),
  errorText: document.getElementById("profile-error-text"),

  monogram: document.getElementById("profile-monogram"),
  heroName: document.getElementById("profile-hero-name"),
  heroEmail: document.getElementById("profile-hero-email"),
  heroRole: document.getElementById("profile-hero-role"),
  heroCreated: document.getElementById("profile-hero-created"),

  usernameText: document.getElementById("profile-username-text"),
  usernameField: document.getElementById("profile-username-field"),
  usernameInput: document.getElementById("profile-username-input"),
  usernameError: document.getElementById("profile-username-error"),

  emailText: document.getElementById("profile-email-text"),
  idText: document.getElementById("profile-id-text"),
  roleText: document.getElementById("profile-role-text"),
  createdText: document.getElementById("profile-created-text"),

  editBar: document.getElementById("profile-edit-bar"),
  btnEdit: document.getElementById("btn-profile-edit"),
  btnCancel: document.getElementById("btn-profile-cancel"),
  btnSave: document.getElementById("btn-profile-save"),
  btnRefresh: document.getElementById("btn-profile-refresh"),
  btnRetry: document.getElementById("btn-profile-retry"),

  navAvatar: document.getElementById("nav-avatar"),
  navUsername: document.getElementById("nav-username"),
  navRole: document.getElementById("nav-role"),
};

// ---------- Hiển thị ----------

// "Nguyễn Văn An" -> "NVA"; "an" -> "AN"
function toMonogram(username) {
  const parts = String(username || "").trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "DH";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function formatCreatedAt(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
}

function renderProfile(profile) {
  currentProfile = profile;

  els.monogram.textContent = toMonogram(profile.username);
  els.heroName.textContent = profile.username;
  if (els.heroEmail) els.heroEmail.textContent = profile.email;
  if (els.heroRole) els.heroRole.textContent = profile.role;
  if (els.heroCreated) {
    els.heroCreated.textContent = `Thành viên từ ${formatCreatedAt(profile.created_at)}`;
  }

  els.usernameText.textContent = profile.username;
  els.emailText.textContent = profile.email;
  els.idText.textContent = `#${profile.id}`;
  els.roleText.textContent = profile.role;
  els.createdText.textContent = formatCreatedAt(profile.created_at);

  els.navAvatar.textContent = toMonogram(profile.username);
  els.navUsername.textContent = profile.username;
  els.navRole.textContent = profile.role;

  // Đã đăng nhập: hiện avatar + dropdown tài khoản, ẩn nút Đăng nhập.
  window.DHNavbarAuth.mount(profile);
}

// ---------- Chế độ chỉnh sửa ----------

function setEditing(editing) {
  isEditing = editing;
  els.editBar.classList.toggle("d-none", !editing);
  els.btnEdit.classList.toggle("d-none", editing);
  els.usernameText.classList.toggle("d-none", editing);
  els.usernameField.classList.toggle("d-none", !editing);

  if (editing) {
    els.usernameInput.value = currentProfile ? currentProfile.username : "";
    clearUsernameError();
    els.usernameInput.focus();
  }
}

function clearUsernameError() {
  els.usernameError.textContent = "";
  els.usernameError.classList.add("d-none");
  els.usernameInput.classList.remove("is-invalid");
}

function validateUsername(value) {
  if (!value) return "Tên người dùng không được để trống.";
  if (value.length < USERNAME_MIN_LENGTH) {
    return `Tên người dùng phải có ít nhất ${USERNAME_MIN_LENGTH} ký tự.`;
  }
  if (value.length > USERNAME_MAX_LENGTH) {
    return `Tên người dùng không được vượt quá ${USERNAME_MAX_LENGTH} ký tự.`;
  }
  return "";
}

function showUsernameError(message) {
  els.usernameError.textContent = message;
  els.usernameError.classList.toggle("d-none", !message);
  els.usernameInput.classList.toggle("is-invalid", Boolean(message));
}

// Đọc message lỗi từ backend theo format chuẩn: 409 trả về message dạng chuỗi,
// 422 trả về errors (mảng { field, message }).
function readUsernameError(error) {
  const data = error && error.data ? error.data : {};
  const message = typeof data.message === "string" ? data.message : null;
  if (message) return message;
  if (Array.isArray(data.errors) && data.errors.length) {
    return data.errors.map((item) => item.message).join("; ");
  }
  if (error && error.message) return error.message;
  return "Không lưu được thay đổi. Vui lòng thử lại.";
}

// ---------- Gọi API ----------

async function loadProfile() {
  els.content.classList.add("d-none");
  els.errorBox.classList.add("d-none");
  els.authRequired.classList.add("d-none");

  try {
    // authMode "required": thiếu token hoặc token hết hạn -> api.js báo người dùng
    // và chuyển về trang đăng nhập.
    const response = await api.get("/users/me", undefined, { authMode: "required" });
    api.session.setUser(response.data);
    renderProfile(response.data);
    els.content.classList.remove("d-none");
    setEditing(false);
  } catch (error) {
    // 401: token hết hạn hoặc không hợp lệ -> api.js đã xoá token và chuyển
    // về trang đăng nhập; hiển thị lại trạng thái yêu cầu đăng nhập.
    if (error && error.status === 401) {
      showLoginState();
      els.authRequired.classList.remove("d-none");
      return;
    }
    els.errorText.textContent = error && error.message ? error.message : "Đã xảy ra lỗi. Vui lòng thử lại.";
    els.errorBox.classList.remove("d-none");
  }
}

// Chưa đăng nhập: ẩn avatar ở navbar, chỉ hiện nút Đăng nhập.
function showLoginState() {
  window.DHNavbarAuth.mount(null);
}

async function saveProfile() {
  const username = els.usernameInput.value.trim();
  const validationMessage = validateUsername(username);
  if (validationMessage) {
    showUsernameError(validationMessage);
    els.usernameInput.focus();
    return;
  }

  if (currentProfile && username === currentProfile.username) {
    setEditing(false);
    return;
  }

  els.btnSave.disabled = true;
  els.btnSave.textContent = "Đang lưu...";
  try {
    const response = await api.patch("/users/me", { username }, { authMode: "required" });
    renderProfile(response.data);
    setEditing(false);
    await Swal.fire({
      icon: "success",
      title: "Đã cập nhật hồ sơ",
      text: `Tên người dùng mới là ${response.data.username}.`,
      confirmButtonText: "Đóng",
    });
  } catch (error) {
    showUsernameError(readUsernameError(error));
  } finally {
    els.btnSave.disabled = false;
    els.btnSave.textContent = "Lưu thay đổi";
  }
}

// ---------- Sự kiện ----------

els.btnEdit.addEventListener("click", () => setEditing(true));
els.btnCancel.addEventListener("click", () => setEditing(false));
els.btnSave.addEventListener("click", saveProfile);
if (els.btnRefresh) els.btnRefresh.addEventListener("click", loadProfile);
els.btnRetry.addEventListener("click", loadProfile);

const btnCopyEmailEl = document.getElementById("btn-copy-email");
if (btnCopyEmailEl) {
  btnCopyEmailEl.addEventListener("click", async () => {
    if (!currentProfile || !currentProfile.email || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(currentProfile.email);
      if (typeof showToast === "function") {
        showToast("Đã sao chép email đăng nhập.", "success");
      }
    } catch {
      if (typeof showToast === "function") {
        showToast("Không thể sao chép email.", "error");
      }
    }
  });
}

els.usernameInput.addEventListener("input", () => {
  const message = validateUsername(els.usernameInput.value.trim());
  if (!message) clearUsernameError();
});

els.usernameInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    saveProfile();
  }
});

// ---------- Menu mobile (giống các trang khác) ----------
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

loadProfile();
