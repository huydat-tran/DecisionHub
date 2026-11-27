// DecisionHub Admin · Tiện ích dùng chung
// - Toast thông báo (success / error / warning)
// - Hộp thoại xác nhận bằng SweetAlert2
// - Validation form: đánh dấu lỗi theo từng field
// Dùng lại escapeHtml / formatMoney từ frontend/js/utils.js

const ADM_TOAST_DURATION = 3600;

function admToast(message, type = "success") {
  let container = document.querySelector(".adm-toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "adm-toast-container";
    container.setAttribute("role", "status");
    container.setAttribute("aria-live", "polite");
    document.body.appendChild(container);
  }

  const icons = { success: "✓", error: "✕", warning: "!" };
  const toast = document.createElement("div");
  toast.className = `adm-toast adm-toast-${type}`;
  toast.innerHTML = `<span class="adm-toast-icon">${icons[type] || "•"}</span><span></span>`;
  toast.lastElementChild.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transition = "opacity .3s ease";
    setTimeout(() => toast.remove(), 300);
  }, ADM_TOAST_DURATION);
}

/**
 * Hộp thoại xác nhận. Trả về Promise<boolean>.
 * @param {{title: string, text?: string, confirmText?: string, cancelText?: string, danger?: boolean}} options
 */
function admConfirm(options) {
  if (typeof Swal === "undefined") {
    return Promise.resolve(window.confirm(options.text || options.title));
  }
  return Swal.fire({
    title: options.title,
    text: options.text || "",
    icon: options.danger ? "warning" : "question",
    showCancelButton: true,
    confirmButtonText: options.confirmText || "Xác nhận",
    cancelButtonText: options.cancelText || "Hủy",
    reverseButtons: true,
    customClass: {
      popup: "adm-swal" + (options.danger ? " adm-swal-danger" : ""),
    },
  }).then((result) => result.isConfirmed);
}

/** Đánh dấu lỗi cho một field. input cần thuộc tính data-error-target trỏ tới phần tử hiển thị lỗi. */
function admSetFieldError(input, message) {
  const field = input.closest(".adm-field") || input.parentElement;
  const errorEl = field ? field.querySelector(".adm-error") : null;
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.classList.add("is-visible");
  }
  input.classList.add("is-invalid");
  input.setAttribute("aria-invalid", "true");
}

function admClearFieldError(input) {
  const field = input.closest(".adm-field") || input.parentElement;
  const errorEl = field ? field.querySelector(".adm-error") : null;
  if (errorEl) {
    errorEl.textContent = "";
    errorEl.classList.remove("is-visible");
  }
  input.classList.remove("is-invalid");
  input.removeAttribute("aria-invalid");
}

function admClearFormErrors(form) {
  form.querySelectorAll(".adm-error").forEach((el) => {
    el.textContent = "";
    el.classList.remove("is-visible");
  });
  form.querySelectorAll(".is-invalid").forEach((el) => {
    el.classList.remove("is-invalid");
    el.removeAttribute("aria-invalid");
  });
}

/** Đọc giá trị của form thành object, bỏ qua các field rỗng. */
function admFormValues(form) {
  const values = {};
  new FormData(form).forEach((value, key) => {
    values[key] = typeof value === "string" ? value.trim() : value;
  });
  form.querySelectorAll('input[type="checkbox"]').forEach((cb) => {
    values[cb.name] = cb.checked;
  });
  return values;
}

/** "2026-11-04T09:30:00" -> "09:30 04/11/2026" */
function admFormatDateTime(value) {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return (
    d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }) +
    " " +
    d.toLocaleDateString("vi-VN")
  );
}
