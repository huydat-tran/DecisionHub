// Kiem thu nhanh cho frontend/admin/js/store.js (khong can browser):
// kiem tra vong doi them / sua / xoa va dem so lieu trong phiên.
//
// Chay: node frontend/tests/admin-store.test.js

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const storeSource = fs.readFileSync(
  path.join(__dirname, "..", "admin", "js", "store.js"),
  "utf8",
);

const sessionStorage = (() => {
  let cache = {};
  return {
    getItem: (key) => (key in cache ? cache[key] : null),
    setItem: (key, value) => {
      cache[key] = String(value);
    },
    removeItem: (key) => {
      delete cache[key];
    },
  };
})();

const context = vm.createContext({ console, setTimeout, sessionStorage });
vm.runInContext(storeSource, context);

const { store } = context;
const results = [];
function check(name, actual, expected) {
  results.push({ ok: actual === expected, name, actual, expected });
}

(async () => {
  // Danh muc bat dau rong (khong co ban ghi gia).
  check("foods ban dau rong", (await context.admStoreListFoods()).length, 0);
  check("places ban dau rong", (await context.admStoreListPlaces()).length, 0);

  const food = await context.admStoreCreateFood({
    name: "Phở bò tái",
    price: 45000,
    meal_type: "breakfast",
    is_active: true,
  });
  check("tao food co id", food.id, 1);
  check("food ghi nhan hoat dong", food.is_active, true);
  check("food co created_at", typeof food.created_at, "string");

  const updated = await context.admStoreUpdateFood(food.id, { price: 50000 });
  check("cap nhat gia", updated.price, 50000);
  check("cap nhat giu ten", updated.name, "Phở bò tái");

  const place = await context.admStoreCreatePlace({
    name: "Phố cổ Hội An",
    region: "Trung",
    estimated_cost: 500000,
    estimated_duration: 8,
    rating: 4.8,
  });
  check("tao place co id", place.id, 1);

  const counts = await context.admStoreCounts();
  check("dem foods", counts.foods, 1);
  check("dem places", counts.places, 1);

  const activity = await context.admStoreListActivity();
  check("co hoat dong ghi nhan", activity.length >= 3, true);

  await context.admStoreDeleteFood(food.id);
  check("xoa food", (await context.admStoreListFoods()).length, 0);
  check("place con nguyen", (await context.admStoreListPlaces()).length, 1);

  let threw = false;
  try {
    await context.admStoreDeleteFood(999);
  } catch (error) {
    threw = true;
  }
  check("xoa id khong ton tai nem loi", threw, true);

  const failed = results.filter((item) => !item.ok);
  results.forEach((item) => {
    console.log(`${item.ok ? "PASS" : "FAIL"} - ${item.name}` + (item.ok ? "" : ` (expected ${item.expected}, got ${item.actual})`));
  });
  console.log(`\n${results.length - failed.length}/${results.length} test pass`);
  process.exit(failed.length ? 1 : 0);
})();
