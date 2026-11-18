// Trang Lịch sử hoạt động (History).
//
// History là chức năng yêu cầu đăng nhập: Guest truy cập trang này sẽ được
// thông báo và chuyển về trang đăng nhập (api.redirectToLogin).
//
// Backend chưa có API lịch sử nên bảng hiển thị trạng thái rỗng; phần nạp dữ liệu
// sẽ nối vào API khi module History được triển khai.

const tableBodyEl = document.getElementById("history-table-body");
const emptyEl = document.getElementById("history-empty");

function renderEmpty() {
  if (tableBodyEl) tableBodyEl.innerHTML = "";
  if (emptyEl) emptyEl.classList.remove("d-none");
}

// Yêu cầu đăng nhập: Guest -> thông báo + chuyển về trang đăng nhập.
if (!api.session.isLoggedIn()) {
  api.redirectToLogin("Vui lòng đăng nhập để xem lịch sử hoạt động.");
} else {
  renderEmpty();
}
