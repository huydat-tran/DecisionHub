// DecisionHub Admin · Trang Quản lý địa điểm du lịch
// - Tải danh sách địa điểm (loading / empty / no-result / table)
// - Tìm kiếm + lọc theo khu vực, loại hình và trạng thái
// - Modal thêm / sửa / xem chi tiết, xác nhận xoá bằng SweetAlert2
// Dữ liệu lấy từ ../store.js (tạm thời trong phiên, chưa gọi API).

const PLACE_REGIONS = ["Bắc", "Trung", "Nam", "Tây Nguyên", "Tây Nam Bộ"];
const DEFAULT_PLACE_IMAGE = "../../assets/images/travel/dalat.jpg";
const DEFAULT_ACTIVITY_TYPES = [
  "Nghỉ dưỡng biển",
  "Khám phá thiên nhiên",
  "Văn hóa lịch sử",
  "Nghỉ dưỡng núi",
  "Sinh thái",
];
const DEFAULT_PLACE_RATING = 4.5;

const placeState = { places: [], filtered: [], activityTypes: [] };

const el = {
  tbody: document.getElementById("place-tbody"),
  tableWrap: document.getElementById("place-table-wrap"),
  loading: document.getElementById("place-loading"),
  empty: document.getElementById("place-empty"),
  noResult: document.getElementById("place-no-result"),
  count: document.getElementById("place-count"),
  search: document.getElementById("place-search"),
  filterRegion: document.getElementById("place-filter-region"),
  filterActivity: document.getElementById("place-filter-activity"),
  filterStatus: document.getElementById("place-filter-status"),
  btnAdd: document.getElementById("btn-add-place"),
  btnEmptyAdd: document.getElementById("btn-empty-add-place"),
  btnClearFilters: document.getElementById("btn-clear-place-filters"),
  formModalEl: document.getElementById("place-form-modal"),
  form: document.getElementById("place-form"),
  formTitle: document.getElementById("place-form-title"),
  formSubtitle: document.getElementById("place-form-subtitle"),
  formSubmit: document.getElementById("place-form-submit"),
  viewModalEl: document.getElementById("place-view-modal"),
  viewBody: document.getElementById("place-view-body"),
};

let placeFormModal = null;
let placeViewModal = null;

function placeStatusBadge(place) {
  return place.is_active
    ? '<span class="adm-badge adm-badge-success"><span class="adm-dot"></span>Đang mở cửa</span>'
    : '<span class="adm-badge adm-badge-muted"><span class="adm-dot"></span>Tạm ngưng</span>';
}

function placeThumb(place) {
  const src = place.image_url || DEFAULT_PLACE_IMAGE;
  return `<img class="adm-thumb" src="${escapeHtml(src)}" alt="${escapeHtml(place.name)}" loading="lazy" />`;
}

function placeRow(place) {
  return `
    <tr data-id="${place.id}">
      <td>
        <div class="adm-item-cell">
          ${placeThumb(place)}
          <div>
            <div class="adm-item-name">${escapeHtml(place.name)}</div>
            <div class="adm-item-meta">${escapeHtml(place.province_city)}</div>
          </div>
        </div>
      </td>
      <td><span class="adm-badge adm-badge-primary">${escapeHtml(place.region)}</span></td>
      <td>${escapeHtml(place.activity_type)}</td>
      <td>${escapeHtml(formatMoney(place.estimated_cost))}</td>
      <td>${escapeHtml(place.estimated_duration)} giờ</td>
      <td>${escapeHtml(place.rating)} ★</td>
      <td>${placeStatusBadge(place)}</td>
      <td class="adm-col-actions">
        <div class="adm-actions">
          <button type="button" class="adm-action-btn" data-action="view" title="Xem chi tiết" aria-label="Xem chi tiết">👁</button>
          <button type="button" class="adm-action-btn" data-action="edit" title="Sửa" aria-label="Sửa">✎</button>
          <button type="button" class="adm-action-btn is-danger" data-action="delete" title="Xoá" aria-label="Xoá">🗑</button>
        </div>
      </td>
    </tr>`;
}

function applyFilters() {
  const keyword = el.search.value.trim().toLowerCase();
  const region = el.filterRegion.value;
  const activity = el.filterActivity.value;
  const status = el.filterStatus.value;

  placeState.filtered = placeState.places.filter((place) => {
    if (keyword) {
      const haystack = (place.name + " " + place.province_city).toLowerCase();
      if (!haystack.includes(keyword)) return false;
    }
    if (region && place.region !== region) return false;
    if (activity && place.activity_type !== activity) return false;
    if (status === "active" && !place.is_active) return false;
    if (status === "inactive" && place.is_active) return false;
    return true;
  });

  renderList();
}

function renderList() {
  const hasData = placeState.places.length > 0;
  const hasResults = placeState.filtered.length > 0;

  el.loading.hidden = true;
  el.tableWrap.hidden = !hasResults;
  el.empty.hidden = hasData;
  el.noResult.hidden = !hasData || hasResults;

  el.tbody.innerHTML = hasResults ? placeState.filtered.map(placeRow).join("") : "";

  const total = placeState.places.length;
  el.count.textContent = placeState.filtered.length !== total
    ? `${placeState.filtered.length} / ${total} địa điểm`
    : `${total} địa điểm`;
}

/** Đồng bộ danh sách loại hình trong bộ lọc theo dữ liệu hiện có. */
function syncActivityFilter() {
  const current = el.filterActivity.value;
  const types = Array.from(
    new Set(placeState.places.map((place) => place.activity_type).filter(Boolean)),
  ).sort();

  el.filterActivity.innerHTML =
    '<option value="">Tất cả loại hình</option>' +
    types.map((type) => `<option value="${escapeHtml(type)}">${escapeHtml(type)}</option>`).join("");
  el.filterActivity.value = types.includes(current) ? current : "";
}

/** Đổ danh sách loại hình trong form: gợi ý mặc định + các loại hình đang có trong dữ liệu. */
function syncActivityOptions() {
  const select = document.getElementById("place-activity");
  const types = Array.from(
    new Set(
      DEFAULT_ACTIVITY_TYPES.concat(
        placeState.places.map((place) => place.activity_type).filter(Boolean),
      ),
    ),
  ).sort();

  select.innerHTML =
    '<option value="">Chọn loại hình trải nghiệm</option>' +
    types.map((type) => `<option value="${escapeHtml(type)}">${escapeHtml(type)}</option>`).join("");
}

async function loadPlaces() {
  el.loading.hidden = false;
  el.tableWrap.hidden = true;
  el.empty.hidden = true;
  el.noResult.hidden = true;

  placeState.places = await admStoreListPlaces();
  syncActivityFilter();
  syncActivityOptions();
  applyFilters();
}

/* ------------------------------------------------------------------ Form */

function placeHighlightsToString(highlights) {
  return (highlights || []).join(", ");
}

function placeStringToList(value) {
  return value
    .split(/[,\n]/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function openPlaceForm(place) {
  const isEdit = Boolean(place);
  admClearFormErrors(el.form);
  el.form.reset();

  el.formTitle.textContent = isEdit ? "Sửa địa điểm" : "Thêm địa điểm";
  el.formSubtitle.textContent = isEdit
    ? "Cập nhật thông tin địa điểm " + place.name
    : "Điền thông tin địa điểm theo cấu trúc dữ liệu hiện có";
  el.formSubmit.textContent = isEdit ? "Lưu thay đổi" : "Lưu địa điểm";

  document.getElementById("place-id").value = isEdit ? place.id : "";
  document.getElementById("place-name").value = isEdit ? place.name : "";
  document.getElementById("place-province").value = isEdit ? place.province_city : "";
  document.getElementById("place-region").value = isEdit ? place.region : PLACE_REGIONS[0];
  document.getElementById("place-activity").value = isEdit ? place.activity_type : "";
  document.getElementById("place-cost").value = isEdit ? place.estimated_cost : "";
  document.getElementById("place-duration").value = isEdit ? place.estimated_duration : "";
  document.getElementById("place-rating").value = isEdit && place.rating !== undefined ? place.rating : DEFAULT_PLACE_RATING;
  document.getElementById("place-description").value = isEdit ? place.description || "" : "";
  document.getElementById("place-highlights").value = isEdit ? placeHighlightsToString(place.highlights) : "";
  document.getElementById("place-image-url").value = isEdit ? place.image_url || "" : "";
  document.getElementById("place-is-active").checked = isEdit ? Boolean(place.is_active) : true;

  placeFormModal.show();
}

function validatePlaceForm(values) {
  const errors = {};
  if (!values.name) errors.name = "Vui lòng nhập tên địa điểm.";
  if (!values.province_city) errors.province_city = "Vui lòng nhập tỉnh hoặc thành phố.";
  if (!values.region) errors.region = "Vui lòng chọn khu vực.";
  if (!values.activity_type) errors.activity_type = "Vui lòng chọn loại hình trải nghiệm.";
  if (values.estimated_cost === "" || values.estimated_cost === undefined) {
    errors.estimated_cost = "Vui lòng nhập chi phí tham khảo.";
  } else if (Number(values.estimated_cost) < 0) {
    errors.estimated_cost = "Chi phí không được âm.";
  }
  if (values.estimated_duration === "" || values.estimated_duration === undefined) {
    errors.estimated_duration = "Vui lòng nhập thời lượng.";
  } else if (Number(values.estimated_duration) <= 0) {
    errors.estimated_duration = "Thời lượng phải lớn hơn 0 giờ.";
  }
  if (values.rating === "" || values.rating === undefined) {
    errors.rating = "Vui lòng nhập đánh giá.";
  } else if (Number(values.rating) < 0 || Number(values.rating) > 5) {
    errors.rating = "Đánh giá phải từ 0 đến 5 sao.";
  }
  if (values.image_url && !/^https?:\/\//i.test(values.image_url)) {
    errors.image_url = "URL hình ảnh phải bắt đầu bằng http:// hoặc https://.";
  }
  return errors;
}

function showPlaceErrors(errors) {
  const fieldMap = {
    name: "place-name",
    province_city: "place-province",
    region: "place-region",
    activity_type: "place-activity",
    estimated_cost: "place-cost",
    estimated_duration: "place-duration",
    rating: "place-rating",
    image_url: "place-image-url",
  };
  Object.keys(fieldMap).forEach((key) => {
    const input = document.getElementById(fieldMap[key]);
    if (!input) return;
    if (errors[key]) admSetFieldError(input, errors[key]);
    else admClearFieldError(input);
  });
  const firstError = Object.keys(errors)[0];
  if (firstError && fieldMap[firstError]) {
    document.getElementById(fieldMap[firstError]).focus();
  }
}

async function handlePlaceSubmit(event) {
  event.preventDefault();
  const values = admFormValues(el.form);
  const errors = validatePlaceForm(values);
  showPlaceErrors(errors);
  if (Object.keys(errors).length) return;

  const id = document.getElementById("place-id").value;
  const current = id
    ? placeState.places.find((item) => item.id === Number(id))
    : null;

  const payload = {
    name: values.name,
    province_city: values.province_city,
    region: values.region,
    activity_type: values.activity_type,
    estimated_cost: Number(values.estimated_cost),
    estimated_duration: Number(values.estimated_duration),
    rating: Number(values.rating || DEFAULT_PLACE_RATING),
    description: values.description || null,
    highlights: placeStringToList(values.highlights),
    image_url: values.image_url || null,
    is_active: values.is_active,
  };

  el.formSubmit.disabled = true;
  try {
    if (id) {
      await admStoreUpdatePlace(Number(id), payload);
      admToast("Đã cập nhật địa điểm trong phiên hiện tại (chưa ghi xuống máy chủ).", "success");
    } else {
      await admStoreCreatePlace(payload);
      admToast("Đã thêm địa điểm vào phiên hiện tại (chưa ghi xuống máy chủ).", "success");
    }
    placeFormModal.hide();
    await loadPlaces();
  } catch (error) {
    admToast(error.message || "Không lưu được địa điểm.", "error");
  } finally {
    el.formSubmit.disabled = false;
  }
}

/* ------------------------------------------------------------ View detail */

function openPlaceView(place) {
  const highlights = (place.highlights || []).map((item) => escapeHtml(item)).join(", ") || "—";
  const src = place.image_url || DEFAULT_PLACE_IMAGE;

  el.viewBody.innerHTML = `
    <div class="adm-preview">
      <img src="${escapeHtml(src)}" alt="${escapeHtml(place.name)}" />
      <div class="adm-preview-info">
        <h4 class="adm-preview-name">${escapeHtml(place.name)}</h4>
        <p class="adm-preview-desc">${escapeHtml(place.description || "Địa điểm chưa có mô tả.")}</p>
        <dl class="adm-preview-meta">
          <div><dt>Tỉnh / Thành phố</dt><dd>${escapeHtml(place.province_city)}</dd></div>
          <div><dt>Khu vực</dt><dd>${escapeHtml(place.region)}</dd></div>
          <div><dt>Loại hình</dt><dd>${escapeHtml(place.activity_type)}</dd></div>
          <div><dt>Chi phí tham khảo</dt><dd>${escapeHtml(formatMoney(place.estimated_cost))}</dd></div>
          <div><dt>Thời lượng</dt><dd>${escapeHtml(place.estimated_duration)} giờ</dd></div>
          <div><dt>Điểm đánh giá</dt><dd>${escapeHtml(place.rating)} ★</dd></div>
          <div><dt>Hoạt động nổi bật</dt><dd>${highlights}</dd></div>
          <div><dt>Trạng thái</dt><dd>${place.is_active ? "Đang mở cửa" : "Tạm ngưng"}</dd></div>
        </dl>
      </div>
    </div>`;
  placeViewModal.show();
}

async function handlePlaceAction(action, id) {
  const place = placeState.places.find((item) => item.id === id);
  if (!place) return;

  if (action === "view") {
    openPlaceView(place);
    return;
  }
  if (action === "edit") {
    openPlaceForm(place);
    return;
  }
  if (action === "delete") {
    const confirmed = await admConfirm({
      title: "Xoá địa điểm?",
      text: `"${place.name}" sẽ bị xoá khỏi danh mục trong phiên hiện tại.`,
      confirmText: "Xoá",
      cancelText: "Giữ lại",
      danger: true,
    });
    if (!confirmed) return;
    try {
      await admStoreDeletePlace(id);
      admToast("Đã xoá địa điểm khỏi phiên hiện tại (chưa ghi xuống máy chủ).", "success");
      await loadPlaces();
    } catch (error) {
      admToast(error.message || "Không xoá được địa điểm.", "error");
    }
  }
}

/* ------------------------------------------------------------------ Init */

function initPlacePage() {
  if (typeof bootstrap !== "undefined") {
    placeFormModal = new bootstrap.Modal(el.formModalEl);
    placeViewModal = new bootstrap.Modal(el.viewModalEl);
  }

  el.btnAdd.addEventListener("click", () => openPlaceForm(null));
  el.btnEmptyAdd.addEventListener("click", () => openPlaceForm(null));
  el.search.addEventListener("input", applyFilters);
  el.filterRegion.addEventListener("change", applyFilters);
  el.filterActivity.addEventListener("change", applyFilters);
  el.filterStatus.addEventListener("change", applyFilters);
  el.btnClearFilters.addEventListener("click", () => {
    el.search.value = "";
    el.filterRegion.value = "";
    el.filterActivity.value = "";
    el.filterStatus.value = "";
    applyFilters();
  });

  el.form.addEventListener("submit", handlePlaceSubmit);
  el.form.querySelectorAll("input, select, textarea").forEach((input) => {
    input.addEventListener("input", () => admClearFieldError(input));
  });

  el.tbody.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const row = button.closest("tr");
    handlePlaceAction(button.dataset.action, Number(row.dataset.id));
  });

  loadPlaces();
}

initPlacePage();
