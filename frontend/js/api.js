// Module gọi API bằng axios: cấu hình 1 lần, mọi trang dùng chung.
// (axios được nạp từ CDN bằng thẻ <script> trong từng trang HTML, trước file này)
//
// Cách dùng (trong các file js/pages/*.js):
//   const data = await api.get("/health");
//   const data = await api.get("/food/quick-search", { q: "phở" });  // -> /food/quick-search?q=phở
//   const created = await api.post("/travel/recommend", { budget: 500000 });
//   await api.put("/food/1", { name: "Tên mới" });
//   await api.delete("/food/1");
//
// Các hàm trả về thẳng dữ liệu JSON (đã lấy sẵn response.data).
// Nếu lỗi, hàm sẽ throw ApiError -> bắt bằng try/catch và hiện error.message cho người dùng.
//
// authMode quy định cách gắn access token cho từng lệnh gọi:
//   "none" (mặc định) : API công khai -> KHÔNG gửi token.
//   "optional"       : API đọc được khi có token -> gửi token nếu còn hạn.
//                       Trả 401 thì chỉ xoá phiên, KHÔNG chuyển trang.
//   "required"       : API bắt buộc đăng nhập -> thiếu/hết hạn token sẽ báo
//                       người dùng và chuyển về trang đăng nhập.

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status; // mã HTTP: 404, 422, 500... (0 = không gọi được server)
    this.data = data; // nội dung lỗi gốc server trả về
  }
}

// ---------------------------------------------------------------------------
// Phiên đăng nhập: lưu token, đọc trạng thái hợp lệ và thông báo cho các trang
// ---------------------------------------------------------------------------
const AUTH_TOKEN_KEY = "token";
const LOGIN_PAGE = "pages/signup.html";

let currentUser = null;
const sessionListeners = [];
let redirectingToLogin = false;

// Thư mục gốc frontend (chứa index.html), ví dụ "/frontend/".
function frontendRootDir() {
  const path = window.location.pathname;
  const idx = path.indexOf("/pages/");
  if (idx !== -1) return path.slice(0, idx + 1);
  return path.slice(0, path.lastIndexOf("/") + 1);
}

// Đường dẫn của trang hiện tại tính từ thư mục gốc frontend, ví dụ "pages/profile.html".
function pathFromFrontendRoot() {
  return window.location.pathname.slice(frontendRootDir().length);
}

// Thư mục chứa trang hiện tại, tính từ thư mục gốc frontend: "" hoặc "pages/".
function currentDirFromRoot() {
  const rel = pathFromFrontendRoot();
  const idx = rel.lastIndexOf("/");
  return idx === -1 ? "" : rel.slice(0, idx + 1);
}

// Đổi đường dẫn tính từ thư mục gốc frontend sang đường dẫn tương đối với
// thư mục chứa trang hiện tại, để dùng cho thẻ href.
function appUrl(targetFromRoot) {
  const dir = currentDirFromRoot();
  if (targetFromRoot.indexOf(dir) === 0) {
    // Cùng thư mục -> bỏ tiền tố chung.
    return targetFromRoot.slice(dir.length);
  }
  // Khác thư mục -> đi lên thư mục gốc rồi xuống trang đích.
  const levels = dir.split("/").filter(Boolean).length;
  return "../".repeat(levels) + targetFromRoot;
}

// Đọc claim "exp" của JWT để biết token đã hết hạn chưa.
function decodeTokenPayload(token) {
  const part = String(token || "").split(".")[1];
  if (!part) return null;
  try {
    // JWT dùng base64url (- _), cần đổi lại base64 chuẩn rồi thêm padding.
    const base64 = part.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(window.atob(padded));
  } catch (error) {
    return null;
  }
}

function notifySessionChange(user) {
  sessionListeners.forEach((listener) => {
    try {
      listener(user);
    } catch (error) {
      console.error(error);
    }
  });
}

const session = {
  getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  },

  setToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  },

  isExpired(token) {
    if (!token) return true;
    const payload = decodeTokenPayload(token);
    if (!payload || !payload.exp) return false; // không đọc được exp -> để backend quyết định
    return payload.exp * 1000 <= Date.now();
  },

  isLoggedIn() {
    const token = this.getToken();
    return Boolean(token) && !this.isExpired(token);
  },

  getUser() {
    return currentUser;
  },

  setUser(user) {
    currentUser = user || null;
    notifySessionChange(currentUser);
  },

  // Xoá token + thông tin đăng nhập -> trở về trạng thái Guest.
  clear() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    currentUser = null;
    notifySessionChange(null);
  },

  subscribe(listener) {
    sessionListeners.push(listener);
  },
};

function showErrorToast(message) {
  if (typeof showToast === "function") showToast(message, "error");
}

// Đưa người dùng về trang đăng nhập, nhớ lại trang đang xem để quay lại sau khi
// đăng nhập. Không chuyển hướng nếu đang ở trang đăng nhập (tránh vòng lặp).
function redirectToLogin(message) {
  if (redirectingToLogin) return;
  if (pathFromFrontendRoot().indexOf("pages/signup.html") !== -1) return;

  redirectingToLogin = true;
  if (message) showErrorToast(message);

  // Lưu trang đang xem (tính từ thư mục gốc frontend) để quay lại sau khi đăng nhập.
  const back = pathFromFrontendRoot() + window.location.search;
  const target = appUrl(LOGIN_PAGE) + "?redirect=" + encodeURIComponent(back);

  // Chờ một chút để người dùng kịp đọc thông báo trước khi rời trang.
  setTimeout(function () {
    window.location.href = target;
  }, 1200);
}

// Instance axios dùng chung: mọi request tự nối thêm baseURL phía trước
const http = axios.create({
  baseURL: CONFIG.API_BASE_URL,
  timeout: 10000, // quá 10 giây không phản hồi thì báo lỗi
  headers: { "Content-Type": "application/json" },
});

// Chỉ gửi Authorization khi lệnh gọi cần token và token còn hạn.
http.interceptors.request.use((config) => {
  const authMode = config.authMode || "none";
  if (authMode === "none") return config;

  const token = session.getToken();
  if (!token) return config;

  // Token đã hết hạn -> xoá khỏi bộ nhớ, không gửi lên server.
  if (session.isExpired(token)) {
    session.clear();
    return config;
  }

  config.headers.Authorization = `Bearer ${token}`;
  config.authTokenSent = true;
  return config;
});

// Lấy câu thông báo lỗi dễ đọc từ response của FastAPI (hỗ trợ cả chuẩn DecisionHub { message, errors } và FastAPI { detail })
function getErrorMessage(data, status) {
  if (data && typeof data.message === "string" && data.message.trim()) {
    return data.message.trim();
  }
  if (data && typeof data.detail === "string" && data.detail.trim()) {
    return data.detail.trim();
  }
  if (data && Array.isArray(data.errors) && data.errors.length > 0) {
    return data.errors
      .map((e) => (e && e.message ? e.message : ""))
      .filter(Boolean)
      .join("; ");
  }
  // Lỗi 422 mặc định của FastAPI: detail là mảng [{ loc: [...], msg: "..." }]
  if (data && Array.isArray(data.detail)) {
    return data.detail.map((e) => `${e.loc[e.loc.length - 1]}: ${e.msg}`).join("; ");
  }
  if (status === 401) return "Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại.";
  if (status === 403) return "Bạn không có quyền truy cập chức năng này.";
  if (status === 404) return "Không tìm thấy dữ liệu yêu cầu.";
  if (status === 422) return "Dữ liệu gửi lên không hợp lệ. Vui lòng kiểm tra lại.";
  if (status >= 500) return "Hệ thống máy chủ đang gặp sự cố tạm thời. Vui lòng thử lại sau.";
  return `Yêu cầu không thành công (mã ${status}).`;
}

// Gom xử lý lỗi một chỗ: đổi lỗi của axios thành ApiError dễ dùng
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server có trả lời nhưng là lỗi (4xx, 5xx)
      const { status, data } = error.response;
      const config = error.config || {};
      const authMode = config.authMode;

      // 401 khi đã gửi token: token hết hạn / không hợp lệ -> về trạng thái Guest.
      if (status === 401 && config.authTokenSent) {
        session.clear();
        // Chỉ chuyển về trang đăng nhập khi người dùng đang dùng chức năng
        // bắt buộc đăng nhập; chức năng công khai thì người dùng vẫn dùng được.
        if (authMode === "required") {
          redirectToLogin("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
        } else {
          showErrorToast("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
        }
      }

      return Promise.reject(new ApiError(getErrorMessage(data, status), status, data));
    }

    // Quá thời gian chờ (Timeout)
    if (
      error &&
      (error.code === "ECONNABORTED" ||
        (typeof error.message === "string" && error.message.toLowerCase().includes("timeout")))
    ) {
      const timeoutErr = new ApiError(
        "Yêu cầu phản hồi quá thời gian chờ. Vui lòng kiểm tra mạng và thử lại.",
        0,
        { code: "TIMEOUT" },
      );
      timeoutErr.isTimeout = true;
      return Promise.reject(timeoutErr);
    }

    // Không có response: server tắt, sai URL, hoặc bị chặn kết nối
    return Promise.reject(
      new ApiError(
        "Không thể kết nối tới máy chủ DecisionHub. Vui lòng kiểm tra kết nối mạng hoặc thử lại sau.",
        0,
        { code: "NETWORK_ERROR" },
      ),
    );
  },
);

// Gọi API theo authMode. Với authMode "required", thiếu token thì báo và chuyển
// về trang đăng nhập mà không gọi API.
function request(method, path, body, params, options) {
  const authMode = (options && options.authMode) || "none";

  if (authMode === "required" && !session.isLoggedIn()) {
    // Token đã hết hạn (hoặc không có) -> xoá phiên cũ rồi yêu cầu đăng nhập.
    session.clear();
    redirectToLogin("Vui lòng đăng nhập để tiếp tục.");
    return Promise.reject(new ApiError("Chưa đăng nhập.", 401, null));
  }

  return http.request({ method, url: path, data: body, params, authMode }).then((res) => res.data);
}

const api = {
  get: (path, params, options) => request("get", path, undefined, params, options),
  post: (path, body, options) => request("post", path, body, undefined, options),
  put: (path, body, options) => request("put", path, body, undefined, options),
  patch: (path, body, options) => request("patch", path, body, undefined, options),
  delete: (path, options) => request("delete", path, undefined, undefined, options),
  session,
  appUrl,
  redirectToLogin,
};
