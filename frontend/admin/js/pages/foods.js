// DecisionHub Admin · Trang Quản lý món ăn
// - Tải danh sách món ăn từ GET /api/v1/food?include_inactive=true
// - Tìm kiếm + lọc theo loại bữa ăn và trạng thái
// - CRUD đầy đủ (GET / POST / PUT / DELETE /api/v1/food) qua ../../js/api.js

const FOOD_MEAL_LABELS = {
  breakfast: "Bữa sáng",
  lunch: "Bữa trưa",
  dinner: "Bữa tối",
  snack: "Bữa nhẹ",
};

const DEFAULT_FOOD_IMAGE = "../../assets/images/foods/hihi.png";

const foodState = { foods: [], filtered: [] };

const el = {
  tbody: document.getElementById("food-tbody"),
  tableWrap: document.getElementById("food-table-wrap"),
  loading: document.getElementById("food-loading"),
  empty: document.getElementById("food-empty"),
  noResult: document.getElementById("food-no-result"),
  errorBox: document.getElementById("food-error"),
  errorDesc: document.getElementById("food-error-desc"),
  btnRetry: document.getElementById("btn-retry-foods"),
  count: document.getElementById("food-count"),
  search: document.getElementById("food-search"),
  filterMeal: document.getElementById("food-filter-meal"),
  filterStatus: document.getElementById("food-filter-status"),
  btnAdd: document.getElementById("btn-add-food"),
  btnEmptyAdd: document.getElementById("btn-empty-add-food"),
  btnClearFilters: document.getElementById("btn-clear-food-filters"),
  formModalEl: document.getElementById("food-form-modal"),
  form: document.getElementById("food-form"),
  formTitle: document.getElementById("food-form-title"),
  formSubtitle: document.getElementById("food-form-subtitle"),
  formSubmit: document.getElementById("food-form-submit"),
  viewModalEl: document.getElementById("food-view-modal"),
  viewBody: document.getElementById("food-view-body"),
};

let foodFormModal = null;
let foodViewModal = null;

function foodMealLabel(value) {
  return FOOD_MEAL_LABELS[value] || value || "—";
}

function foodStatusBadge(food) {
  return food.is_active
    ? '<span class="adm-badge adm-badge-success"><span class="adm-dot"></span>Đang hoạt động</span>'
    : '<span class="adm-badge adm-badge-muted"><span class="adm-dot"></span>Tạm ngưng</span>';
}

function foodThumb(food) {
  const src = food.image_url || DEFAULT_FOOD_IMAGE;
  return `<img class="adm-thumb" src="${escapeHtml(src)}" alt="${escapeHtml(food.name)}" loading="lazy" />`;
}

function foodRow(food) {
  const tags = (food.tags || []).slice(0, 3).map((t) => `<span class="adm-badge adm-badge-muted">${escapeHtml(t)}</span>`).join(" ");
  const prep = food.prep_time === null || food.prep_time === undefined ? "—" : escapeHtml(food.prep_time) + " phút";
  return `
    <tr data-id="${food.id}">
      <td>
        <div class="adm-item-cell">
          ${foodThumb(food)}
          <div>
            <div class="adm-item-name">${escapeHtml(food.name)}</div>
            <div class="adm-item-meta">#${food.id}</div>
          </div>
        </div>
      </td>
      <td><span class="adm-badge adm-badge-primary">${escapeHtml(foodMealLabel(food.meal_type))}</span></td>
      <td>${escapeHtml(formatMoney(food.price))}</td>
      <td>${prep}</td>
      <td>${tags || '<span class="adm-muted">—</span>'}</td>
      <td>${foodStatusBadge(food)}</td>
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
  const meal = el.filterMeal.value;
  const status = el.filterStatus.value;

  foodState.filtered = foodState.foods.filter((food) => {
    if (keyword && !food.name.toLowerCase().includes(keyword)) return false;
    if (meal && food.meal_type !== meal) return false;
    if (status === "active" && !food.is_active) return false;
    if (status === "inactive" && food.is_active) return false;
    return true;
  });

  renderList();
}

function renderList() {
  const hasData = foodState.foods.length > 0;
  const hasResults = foodState.filtered.length > 0;

  el.loading.hidden = true;
  if (el.errorBox) el.errorBox.hidden = true;
  el.tableWrap.hidden = !hasResults;
  el.empty.hidden = hasData;
  el.noResult.hidden = !hasData || hasResults;

  if (hasResults) {
    el.tbody.innerHTML = foodState.filtered.map(foodRow).join("");
  } else {
    el.tbody.innerHTML = "";
  }

  const total = foodState.foods.length;
  el.count.textContent = foodState.filtered.length !== total
    ? `${foodState.filtered.length} / ${total} món ăn`
    : `${total} món ăn`;
}

async function loadFoods() {
  el.loading.hidden = false;
  if (el.errorBox) el.errorBox.hidden = true;
  el.tableWrap.hidden = true;
  el.empty.hidden = true;
  el.noResult.hidden = true;

  try {
    const response = await api.get("/api/v1/food", { include_inactive: true });
    foodState.foods = Array.isArray(response.data) ? response.data : [];
    applyFilters();
  } catch (error) {
    el.loading.hidden = true;
    const message = error && error.message ? error.message : "Không tải được danh sách món ăn.";
    if (el.errorDesc) el.errorDesc.textContent = message;
    if (el.errorBox) el.errorBox.hidden = false;
    el.count.textContent = "0 món ăn";
    admToast(message, "error");
  }
}

/* ------------------------------------------------------------------ Form */

function foodTagsToString(tags) {
  return (tags || []).join(", ");
}

function foodIngredientsToString(ingredients) {
  return (ingredients || []).map((item) => item.name).join(", ");
}

function foodStringToList(value) {
  return value
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function openFoodForm(food) {
  const isEdit = Boolean(food);
  admClearFormErrors(el.form);
  el.form.reset();

  el.formTitle.textContent = isEdit ? "Sửa món ăn" : "Thêm món ăn";
  el.formSubtitle.textContent = isEdit
    ? "Cập nhật thông tin món ăn " + food.name
    : "Điền thông tin món ăn theo cấu trúc dữ liệu hiện có";
  el.formSubmit.textContent = isEdit ? "Lưu thay đổi" : "Lưu món ăn";

  document.getElementById("food-id").value = isEdit ? food.id : "";
  document.getElementById("food-name").value = isEdit ? food.name : "";
  document.getElementById("food-price").value = isEdit ? food.price : "";
  document.getElementById("food-meal-type").value = isEdit ? food.meal_type : "breakfast";
  document.getElementById("food-prep-time").value = isEdit && food.prep_time !== null ? food.prep_time : "";
  document.getElementById("food-description").value = isEdit ? food.description || "" : "";
  document.getElementById("food-image-url").value = isEdit ? food.image_url || "" : "";
  document.getElementById("food-tags").value = isEdit ? foodTagsToString(food.tags) : "";
  document.getElementById("food-ingredients").value = isEdit ? foodIngredientsToString(food.ingredients) : "";
  document.getElementById("food-is-active").checked = isEdit ? Boolean(food.is_active) : true;

  foodFormModal.show();
}

function validateFoodForm(values) {
  const errors = {};
  if (!values.name) errors.name = "Vui lòng nhập tên món ăn.";
  if (!values.price && values.price !== 0) errors.price = "Vui lòng nhập giá tham khảo.";
  else if (Number(values.price) < 0) errors.price = "Giá không được âm.";
  if (!values.meal_type) errors.meal_type = "Vui lòng chọn loại bữa ăn.";
  if (values.prep_time !== "" && Number(values.prep_time) < 0) errors.prep_time = "Thời gian chuẩn bị không được âm.";
  if (values.image_url && !/^https?:\/\//i.test(values.image_url)) errors.image_url = "URL hình ảnh phải bắt đầu bằng http:// hoặc https://.";
  return errors;
}

function showFoodErrors(errors) {
  const fieldMap = {
    name: "food-name",
    price: "food-price",
    meal_type: "food-meal-type",
    prep_time: "food-prep-time",
    image_url: "food-image-url",
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

async function handleFoodSubmit(event) {
  event.preventDefault();
  const values = admFormValues(el.form);
  const errors = validateFoodForm(values);
  showFoodErrors(errors);
  if (Object.keys(errors).length) return;

  const payload = {
    name: values.name,
    price: Number(values.price),
    meal_type: values.meal_type,
    prep_time: values.prep_time === "" ? null : Number(values.prep_time),
    description: values.description || null,
    image_url: values.image_url || null,
    tags: foodStringToList(values.tags),
    ingredients: foodStringToList(values.ingredients).map((name) => ({ name })),
    is_active: values.is_active,
  };

  const id = document.getElementById("food-id").value;
  el.formSubmit.disabled = true;
  try {
    if (id) {
      await api.put(`/api/v1/food/${Number(id)}`, payload);
      admToast("Đã cập nhật món ăn thành công.", "success");
    } else {
      await api.post("/api/v1/food", payload);
      admToast("Đã thêm món ăn thành công.", "success");
    }
    foodFormModal.hide();
    await loadFoods();
  } catch (error) {
    admToast(error.message || "Không lưu được món ăn.", "error");
  } finally {
    el.formSubmit.disabled = false;
  }
}

/* ------------------------------------------------------------ View detail */

function openFoodView(food) {
  const ingredients = (food.ingredients || []).map((item) => escapeHtml(item.name)).join(", ") || "—";
  const tags = (food.tags || []).map((tag) => `<span class="adm-badge adm-badge-muted">${escapeHtml(tag)}</span>`).join(" ") || "—";
  const src = food.image_url || DEFAULT_FOOD_IMAGE;

  el.viewBody.innerHTML = `
    <div class="adm-preview">
      <img src="${escapeHtml(src)}" alt="${escapeHtml(food.name)}" />
      <div class="adm-preview-info">
        <h4 class="adm-preview-name">${escapeHtml(food.name)}</h4>
        <p class="adm-preview-desc">${escapeHtml(food.description || "Món ăn chưa có mô tả.")}</p>
        <dl class="adm-preview-meta">
          <div><dt>Loại bữa ăn</dt><dd>${escapeHtml(foodMealLabel(food.meal_type))}</dd></div>
          <div><dt>Giá tham khảo</dt><dd>${escapeHtml(formatMoney(food.price))}</dd></div>
          <div><dt>Thời gian chuẩn bị</dt><dd>${food.prep_time === null || food.prep_time === undefined ? "—" : escapeHtml(food.prep_time) + " phút"}</dd></div>
          <div><dt>Nguyên liệu</dt><dd>${ingredients}</dd></div>
          <div><dt>Nhãn</dt><dd>${tags}</dd></div>
          <div><dt>Trạng thái</dt><dd>${food.is_active ? "Đang hoạt động" : "Tạm ngưng"}</dd></div>
        </dl>
      </div>
    </div>`;
  foodViewModal.show();
}

async function handleFoodAction(action, id) {
  const food = foodState.foods.find((item) => item.id === id);
  if (!food) return;

  if (action === "view") {
    try {
      const response = await api.get(`/api/v1/food/${id}`, { include_inactive: true });
      openFoodView((response && response.data) || food);
    } catch (error) {
      admToast(error.message || "Không tải được chi tiết món ăn.", "error");
    }
    return;
  }
  if (action === "edit") {
    openFoodForm(food);
    return;
  }
  if (action === "delete") {
    const confirmed = await admConfirm({
      title: "Xoá món ăn?",
      text: `"${food.name}" sẽ bị xoá vĩnh viễn khỏi danh mục món ăn.`,
      confirmText: "Xoá",
      cancelText: "Giữ lại",
      danger: true,
    });
    if (!confirmed) return;
    try {
      await api.delete(`/api/v1/food/${id}`);
      admToast("Đã xoá món ăn thành công.", "success");
      await loadFoods();
    } catch (error) {
      admToast(error.message || "Không xoá được món ăn.", "error");
    }
  }
}

/* ------------------------------------------------------------------ Init */

function initFoodPage() {
  if (typeof bootstrap !== "undefined") {
    foodFormModal = new bootstrap.Modal(el.formModalEl);
    foodViewModal = new bootstrap.Modal(el.viewModalEl);
  }

  el.btnAdd.addEventListener("click", () => openFoodForm(null));
  el.btnEmptyAdd.addEventListener("click", () => openFoodForm(null));
  if (el.btnRetry) el.btnRetry.addEventListener("click", loadFoods);
  el.search.addEventListener("input", applyFilters);
  el.filterMeal.addEventListener("change", applyFilters);
  el.filterStatus.addEventListener("change", applyFilters);
  el.btnClearFilters.addEventListener("click", () => {
    el.search.value = "";
    el.filterMeal.value = "";
    el.filterStatus.value = "";
    applyFilters();
  });

  el.form.addEventListener("submit", handleFoodSubmit);
  el.form.querySelectorAll("input, select, textarea").forEach((input) => {
    input.addEventListener("input", () => admClearFieldError(input));
  });

  el.tbody.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const row = button.closest("tr");
    handleFoodAction(button.dataset.action, Number(row.dataset.id));
  });

  loadFoods();
}

initFoodPage();
