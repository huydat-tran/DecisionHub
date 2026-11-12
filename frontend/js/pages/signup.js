function switchToRegister() {
    document.getElementById('mainContainer').classList.add('register-active');
    // Chuyển mode không để lại lỗi cũ của form đăng nhập.
    clearAllErrors("loginForm");
}

function switchToLogin() {
    document.getElementById('mainContainer').classList.remove('register-active');
    // Chuyển mode không để lại lỗi cũ của form đăng ký.
    clearAllErrors("signupForm");
}

function togglePasswordVisibility(inputId, iconElement) {
    const passwordInput = document.getElementById(inputId);
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        iconElement.classList.remove('fa-eye');
        iconElement.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        iconElement.classList.remove('fa-eye-slash');
        iconElement.classList.add('fa-eye');
    }
}
// --doạn hàm thay đổi theme màu em viết có tìm hiểu nhiều nguồn e sẽ trình bày theo cách 
// hiểu của em

// --khi ngươi dùng mới vào trang web lần đầu tiên họ sẽ được set time theo thời gian hiên tại một lần
// --script ở phần head của html để tránh khi load trang sẽ bị nháy sáng theo css light được cài đặt mặc định
// vì sau mỗi lần load nó sẽ lấy html và css đầu tiên
// --hàm onlyThemecho phép cài đặt theme theo thời gian đầu cùng với hàm checkTheme để không bị ghi đè ở mỗi lần load trang
const onlyTheme = () => {
    let root = document.documentElement;
    let themeBtn = document.getElementById('themeToggleBtn');
    let icon = themeBtn.querySelector('i');
    let now = new Date() ;
    let hours = now.getHours() ;
    if (hours >= 18 || hours < 6){
        
        root.setAttribute('data-theme', 'dark');
        localStorage.setItem('selectedTheme', 'dark');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    } else {
        root.removeAttribute('data-theme');
        localStorage.setItem('selectedTheme', 'light');
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    }
}
// --hàm applyTheme dể kiểm tra hiện tại trang đang dược lưu bộ nhớ tạm là gì 
// để tránh việc sau mỗi lần load trang sẽ bị mất dữ liệu và set sẵn theme khi load lại trang
const applyTheme = () => {
    let themeBtn = document.getElementById('themeToggleBtn');
    let icon = themeBtn.querySelector('i');
    let theme = localStorage.getItem("selectedTheme");
    if (theme === "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    } else {
        document.documentElement.removeAttribute("data-theme");
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
};
const checkTheme = () => {
    
    if (!localStorage.getItem("selectedTheme")) {
        onlyTheme();
    } else {
        applyTheme();
    }
}
checkTheme();
// --bắt sự kiện đổi theme màu khi onclick
// --thay vì khi người dùng click vào và stlye trong js thì e chọn cách chỉnh lại atribute cho html với logic
// ghi đè lại css (root) được cài làm mặc định và ưu tiên cao nhất, nếu cả element html đã có theme=dark([data-theme="dark"]) thì 
// cài đặt lại light bằng cách xóa attribute data-theme, nếu chưa có thì tương đương với việc đang để chế độ light và set lại attribute
// sau đó bước cuối cùng là lưu lại trên localstorega
const toggleTheme = () => {
    let root = document.documentElement;
    let themeBtn = document.getElementById('themeToggleBtn');
    let icon = themeBtn.querySelector('i');
    
    if (root.hasAttribute('data-theme')) {
        root.removeAttribute('data-theme');
        localStorage.setItem('selectedTheme', 'light');
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    } else {
        root.setAttribute('data-theme', 'dark');
        localStorage.setItem('selectedTheme', 'dark');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
}

// ---------------------------------------------------------------------------
// Tích hợp API đăng nhập / đăng ký (Backend FastAPI)
// ---------------------------------------------------------------------------

// Quy ước lưu token đã có sẵn trong project (js/api.js: localStorage "token").
const TOKEN_STORAGE_KEY = "token";

// ---------------------------------------------------------------------------
// Quy tắc validate - đồng bộ với backend/app/modules/auth/schemas.py
// ---------------------------------------------------------------------------
const USERNAME_MIN_LENGTH = 5;
const USERNAME_MAX_LENGTH = 50;
const MIN_PASSWORD_LENGTH = 8;
const BCRYPT_MAX_PASSWORD_BYTES = 72;

// Backend kiểm tra "ký tự đặc biệt" bằng `not char.isalnum()` cho từng ký tự.
// Dùng \p{L}\p{N} để loại đúng chữ cái + chữ số (kể cả tiếng Việt).
const PASSWORD_HAS_UPPERCASE = /\p{Lu}/u;
const PASSWORD_HAS_SPECIAL = /[^\p{L}\p{N}]/u;

// Số byte UTF-8 của chuỗi (bcrypt giới hạn theo byte, không theo ký tự).
function utf8ByteLength(value) {
    return new TextEncoder().encode(value).length;
}

// Trả về danh sách lỗi của từng trường (mảng rỗng = hợp lệ).
function validateEmail(value) {
    const errors = [];
    if (!value) {
        errors.push("Email không được để trống.");
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        errors.push("Email không đúng định dạng.");
    }
    return errors;
}

function validateUsername(value) {
    const errors = [];
    if (!value) {
        errors.push("Username không được để trống.");
    } else {
        if (value.length < USERNAME_MIN_LENGTH) {
            errors.push(`Username phải có ít nhất ${USERNAME_MIN_LENGTH} ký tự.`);
        }
        if (value.length > USERNAME_MAX_LENGTH) {
            errors.push(`Username không được vượt quá ${USERNAME_MAX_LENGTH} ký tự.`);
        }
    }
    return errors;
}

// Chỉ dùng cho đăng ký. Đăng nhập không áp dụng các quy tắc này
// (tài khoản cũ có thể đã tạo trước khi áp dụng quy tắc mới).
function validatePasswordSignup(value) {
    const errors = [];
    if (!value) {
        errors.push("Mật khẩu không được để trống.");
        return errors;
    }
    if (value.length < MIN_PASSWORD_LENGTH) {
        errors.push(`Mật khẩu phải có ít nhất ${MIN_PASSWORD_LENGTH} ký tự.`);
    }
    if (!PASSWORD_HAS_UPPERCASE.test(value)) {
        errors.push("Mật khẩu phải có ít nhất 1 chữ cái in hoa.");
    }
    if (!PASSWORD_HAS_SPECIAL.test(value)) {
        errors.push("Mật khẩu phải có ít nhất 1 ký tự đặc biệt.");
    }
    if (utf8ByteLength(value) > BCRYPT_MAX_PASSWORD_BYTES) {
        errors.push(`Mật khẩu không được vượt quá ${BCRYPT_MAX_PASSWORD_BYTES} byte khi mã hóa UTF-8.`);
    }
    return errors;
}

// Đăng nhập chỉ kiểm tra mật khẩu không rỗng.
function validatePasswordLogin(value) {
    return value ? [] : ["Mật khẩu không được để trống."];
}

// ---------------------------------------------------------------------------
// Hiển thị lỗi ngay dưới input tương ứng
// ---------------------------------------------------------------------------
function setFieldError(inputId, messages) {
    const input = document.getElementById(inputId);
    const errorEl = document.getElementById(inputId + "Error");
    const container = input ? input.closest(".field-container") : null;
    const list = Array.isArray(messages) ? messages : [messages];

    if (errorEl) {
        errorEl.innerHTML = "";
        if (list.length) {
            const ul = document.createElement("ul");
            list.forEach(function (message) {
                const li = document.createElement("li");
                li.textContent = message;
                ul.appendChild(li);
            });
            errorEl.appendChild(ul);
        }
    }
    if (container) {
        container.classList.toggle("is-invalid", list.length > 0);
    }
    if (input) {
        input.classList.toggle("is-invalid", list.length > 0);
        input.setAttribute("aria-invalid", list.length > 0 ? "true" : "false");
    }
}

function clearFieldError(inputId) {
    setFieldError(inputId, []);
}

// Thông báo lỗi chung của form (không xác định được trường nào sai).
function setFormAlert(alertId, message) {
    const el = document.getElementById(alertId);
    if (el) {
        el.textContent = message || "";
    }
}

const FORM_FIELDS = {
    loginForm: ["loginEmail", "loginPass"],
    signupForm: ["signupUsername", "signupEmail", "signupPass"],
};

function clearAllErrors(formId) {
    (FORM_FIELDS[formId] || []).forEach(function (id) {
        clearFieldError(id);
    });
    setFormAlert(formId === "loginForm" ? "loginAlert" : "signupAlert", "");
}

// ---------------------------------------------------------------------------
// Ánh xạ lỗi từ Backend vào đúng trường input
// ---------------------------------------------------------------------------
const FIELD_BY_LOC = {
    email: "signupEmail",
    username: "signupUsername",
    password: "signupPass",
};

// Lỗi 422 của FastAPI/Pydantic: detail là mảng [{ loc: ["body", "email"], msg: "..." }]
function applyDetailList(detail, context) {
    detail.forEach(function (item) {
        const loc = item.loc || [];
        const field = loc[loc.length - 1];
        const inputId = FIELD_BY_LOC[field];
        if (inputId) {
            setFieldError(inputId, [item.msg]);
        } else {
            setFormAlert(context.alertId, item.msg);
        }
    });
}

// Lỗi 409 của backend (DecisionHubException): detail là chuỗi thông báo.
function applyDetailMessage(message, context) {
    const text = String(message || "").toLowerCase();

    const hasEmail = text.includes("email");
    const hasUsername = text.includes("username");
    const hasPassword = text.includes("mật khẩu") || text.includes("password");

    // Lỗi đăng nhập gộp email + mật khẩu ("Email hoặc mật khẩu không đúng."):
    // backend không phân biệt được lỗi nằm ở trường nào, nên hiển thị ở ô mật khẩu
    // với nguyên văn thông báo chung (không suy đoán trường nào sai).
    if (hasEmail && hasPassword && !hasUsername && context.credentialField) {
        setFieldError(context.credentialField, [message]);
        return;
    }

    if (hasEmail && !hasUsername && !hasPassword) {
        setFieldError(context.emailField, [message]);
    } else if (hasUsername && !hasEmail && !hasPassword) {
        setFieldError(context.usernameField, [message]);
    } else if (hasPassword && !hasEmail && !hasUsername) {
        setFieldError(context.passwordField, [message]);
    } else {
        setFormAlert(context.alertId, message);
    }
}

// Hiển thị lỗi API theo đúng trường, hoặc thông báo chung nếu không xác định được.
function showApiError(error, context) {
    const status = error && error.status;
    const detail = error && error.data ? error.data.detail : null;

    if (Array.isArray(detail)) {
        applyDetailList(detail, context);
        return;
    }
    if (typeof detail === "string" && detail) {
        applyDetailMessage(detail, context);
        return;
    }

    // Không xác định được trường -> thông báo chung, không gán đoán.
    let message = "Đã xảy ra lỗi. Vui lòng thử lại.";
    if (status === 0) {
        message = "Không kết nối được backend. Backend đã chạy chưa? Kiểm tra CONFIG.API_BASE_URL.";
    } else if (status >= 500) {
        message = "Hệ thống đang bận. Vui lòng thử lại sau.";
    } else if (error && error.message) {
        message = error.message;
    }
    setFormAlert(context.alertId, message);
}

function setLoading(button, loading, loadingText) {
    if (loading) {
        button.dataset.originalText = button.textContent;
        button.textContent = loadingText;
        button.disabled = true;
    } else {
        button.textContent = button.dataset.originalText || button.textContent;
        button.disabled = false;
    }
}

// ---------------------------------------------------------------------------
// Validate theo thời gian thực: sửa dữ liệu thì lỗi tương ứng được cập nhật
// ---------------------------------------------------------------------------
function bindLiveValidation(inputId, validator) {
    const input = document.getElementById(inputId);
    if (!input) {
        return;
    }
    input.addEventListener("input", function () {
        setFieldError(inputId, validator(input.value.trim()));
    });
}

// Password đăng ký: kiểm tra từng điều kiện ngay khi gõ, xóa sạch khi hợp lệ.
bindLiveValidation("signupUsername", validateUsername);
bindLiveValidation("signupEmail", validateEmail);
bindLiveValidation("signupPass", validatePasswordSignup);

// Email đăng nhập: chỉ kiểm tra định dạng, không áp dụng quy tắc password.
bindLiveValidation("loginEmail", validateEmail);

document.getElementById('loginForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const button = e.target.querySelector('button[type="submit"]');
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPass').value;

    clearAllErrors("loginForm");

    const emailErrors = validateEmail(email);
    const passwordErrors = validatePasswordLogin(password);
    setFieldError("loginEmail", emailErrors);
    setFieldError("loginPass", passwordErrors);
    if (emailErrors.length || passwordErrors.length) {
        return;
    }

    setLoading(button, true, "Đang đăng nhập...");
    try {
        const data = await api.post("/auth/login", { email: email, password: password });
        // Backend trả về { success, message, data: { access_token, token_type, user } }
        localStorage.setItem(TOKEN_STORAGE_KEY, data.data.access_token);

        // Chỉ hiện popup sau khi API xác nhận đăng nhập thành công.
        await Swal.fire({
            icon: "success",
            title: "Đăng nhập thành công!",
            html: "Chào mừng bạn quay trở lại DecisionHub.",
            confirmButtonText: "Bắt đầu",
            customClass: { popup: "auth-login-popup" },
        });
    } catch (error) {
        showApiError(error, {
            alertId: "loginAlert",
            emailField: "loginEmail",
            usernameField: "loginEmail",
            passwordField: "loginPass",
            credentialField: "loginPass",
        });
    } finally {
        setLoading(button, false);
    }
});

document.getElementById('signupForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const button = e.target.querySelector('button[type="submit"]');
    const username = document.getElementById('signupUsername').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPass').value;

    clearAllErrors("signupForm");

    const usernameErrors = validateUsername(username);
    const emailErrors = validateEmail(email);
    const passwordErrors = validatePasswordSignup(password);
    setFieldError("signupUsername", usernameErrors);
    setFieldError("signupEmail", emailErrors);
    setFieldError("signupPass", passwordErrors);
    if (usernameErrors.length || emailErrors.length || passwordErrors.length) {
        return;
    }

    setLoading(button, true, "Đang đăng ký...");
    try {
        // Không gửi confirm password và không gửi role (client không được tự chọn quyền).
        const data = await api.post("/auth/register", {
            username: username,
            email: email,
            password: password,
        });

        const result = await Swal.fire({
            icon: "success",
            title: "Đăng ký thành công!",
            html: "Tài khoản của bạn đã được tạo. Bạn có thể đăng nhập ngay bây giờ.",
            confirmButtonText: "Đăng nhập ngay",
            customClass: { popup: "auth-success-popup" },
        });

        if (result.isConfirmed) {
            // Chuyển về chế độ đăng nhập và điền sẵn email vừa đăng ký.
            switchToLogin();
            document.getElementById('loginEmail').value = email;
        }
    } catch (error) {
        showApiError(error, {
            alertId: "signupAlert",
            emailField: "signupEmail",
            usernameField: "signupUsername",
            passwordField: "signupPass",
        });
    } finally {
        setLoading(button, false);
    }
});

document.querySelectorAll('.social-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        Swal.fire({
            icon: "info",
            title: "Đang phát triển",
            text: "Đăng nhập bằng mạng xã hội chưa được hỗ trợ.",
            confirmButtonText: "Đóng",
        });
    });
});