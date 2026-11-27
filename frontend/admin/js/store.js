// DecisionHub Admin · Lớp dữ liệu tạm thời (in-memory).
// Phase này chưa tích hợp Backend API: dữ liệu bắt đầu rỗng và chỉ tồn tại trong phiên.
// Khi có API, chỉ cần thay thân các hàm trong file này, UI không phải viết lại.

const ADM_LATENCY = 250;

/** Kho dữ liệu tạm, khởi tạo rỗng (không tạo bản ghi giả để trang trí giao diện). */
const store = {
  foods: [],
  places: [],
  activity: [],
  nextFoodId: 1,
  nextPlaceId: 1,
};

const STORE_KEY = "decisionhub.admin.store";

function admStoreLoad() {
  try {
    const raw = sessionStorage.getItem(STORE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    store.foods = saved.foods || [];
    store.places = saved.places || [];
    store.activity = saved.activity || [];
    store.nextFoodId = saved.nextFoodId || store.foods.length + 1;
    store.nextPlaceId = saved.nextPlaceId || store.places.length + 1;
  } catch (error) {
    console.warn("Không đọc được dữ liệu phiên quản trị, khởi tạo lại từ đầu.", error);
  }
}

function admStoreSave() {
  try {
    sessionStorage.setItem(STORE_KEY, JSON.stringify(store));
  } catch (error) {
    console.warn("Không lưu được dữ liệu phiên quản trị.", error);
  }
}

admStoreLoad();

function admDelay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function admLogActivity(type, title) {
  store.activity.unshift({
    id: Date.now() + Math.random(),
    type: type,
    title: title,
    at: new Date().toISOString(),
  });
  if (store.activity.length > 20) store.activity.length = 20;
  admStoreSave();
}

/* ------------------------------------------------------------------ Food */

async function admStoreListFoods() {
  await admDelay(ADM_LATENCY);
  return store.foods.slice();
}

async function admStoreCreateFood(payload) {
  await admDelay(ADM_LATENCY);
  const item = Object.assign({}, payload, {
    id: store.nextFoodId++,
    is_active: payload.is_active !== false,
    created_at: new Date().toISOString(),
  });
  store.foods.push(item);
  admLogActivity("primary", "Thêm món ăn: " + item.name);
  return item;
}

async function admStoreUpdateFood(id, payload) {
  await admDelay(ADM_LATENCY);
  const index = store.foods.findIndex((f) => f.id === id);
  if (index === -1) throw new Error("Không tìm thấy món ăn cần cập nhật.");
  store.foods[index] = Object.assign({}, store.foods[index], payload);
  admLogActivity("success", "Cập nhật món ăn: " + store.foods[index].name);
  return store.foods[index];
}

async function admStoreDeleteFood(id) {
  await admDelay(ADM_LATENCY);
  const index = store.foods.findIndex((f) => f.id === id);
  if (index === -1) throw new Error("Không tìm thấy món ăn cần xoá.");
  const removed = store.foods.splice(index, 1)[0];
  admLogActivity("danger", "Xoá món ăn: " + removed.name);
  return removed;
}

/* ---------------------------------------------------------------- Travel */

async function admStoreListPlaces() {
  await admDelay(ADM_LATENCY);
  return store.places.slice();
}

async function admStoreCreatePlace(payload) {
  await admDelay(ADM_LATENCY);
  const item = Object.assign({}, payload, {
    id: store.nextPlaceId++,
    is_active: payload.is_active !== false,
    created_at: new Date().toISOString(),
  });
  store.places.push(item);
  admLogActivity("primary", "Thêm địa điểm: " + item.name);
  return item;
}

async function admStoreUpdatePlace(id, payload) {
  await admDelay(ADM_LATENCY);
  const index = store.places.findIndex((p) => p.id === id);
  if (index === -1) throw new Error("Không tìm thấy địa điểm cần cập nhật.");
  store.places[index] = Object.assign({}, store.places[index], payload);
  admLogActivity("success", "Cập nhật địa điểm: " + store.places[index].name);
  return store.places[index];
}

async function admStoreDeletePlace(id) {
  await admDelay(ADM_LATENCY);
  const index = store.places.findIndex((p) => p.id === id);
  if (index === -1) throw new Error("Không tìm thấy địa điểm cần xoá.");
  const removed = store.places.splice(index, 1)[0];
  admLogActivity("danger", "Xoá địa điểm: " + removed.name);
  return removed;
}

/* ------------------------------------------------------------- Activity */

async function admStoreListActivity() {
  await admDelay(0);
  return store.activity.slice();
}

async function admStoreCounts() {
  await admDelay(ADM_LATENCY);
  return { foods: store.foods.length, places: store.places.length };
}
