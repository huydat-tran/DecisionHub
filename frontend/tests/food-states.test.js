// Kiểm thử tự động 13 trường hợp giao diện Loading, Empty, Error luồng Food
// (Form Food, Kết quả Recommend Food, Lịch sử quyết định Food & Khám phá món ăn).
// Chạy: node frontend/tests/food-states.test.js

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const foodResultsHtml = fs.readFileSync(
  path.join(__dirname, "..", "pages", "food-results.html"),
  "utf8",
);
const foodHtml = fs.readFileSync(
  path.join(__dirname, "..", "pages", "food.html"),
  "utf8",
);
const historyHtml = fs.readFileSync(
  path.join(__dirname, "..", "pages", "history.html"),
  "utf8",
);
const resultsCss = fs.readFileSync(
  path.join(__dirname, "..", "css", "results.css"),
  "utf8",
);
const foodRecommendJs = fs.readFileSync(
  path.join(__dirname, "..", "js", "pages", "food-recommend.js"),
  "utf8",
);
const historyJs = fs.readFileSync(
  path.join(__dirname, "..", "js", "pages", "history.js"),
  "utf8",
);

const results = [];
function assert(name, condition, detail = "") {
  results.push({ ok: Boolean(condition), name, detail });
}

// Helper tạo phần tử DOM giả lập hỗ trợ classList, attributes, listeners
function createMockElement(id, initialHidden = false) {
  const classes = new Set(initialHidden ? ["d-none"] : []);
  const attrs = {};
  const listeners = {};
  return {
    id,
    value: "",
    textContent: "",
    innerHTML: "",
    className: "",
    disabled: false,
    dataset: {},
    classList: {
      add: (...c) => c.forEach((x) => classes.add(x)),
      remove: (...c) => c.forEach((x) => classes.delete(x)),
      toggle: (c, force) => {
        const shouldAdd = force !== undefined ? Boolean(force) : !classes.has(c);
        if (shouldAdd) classes.add(c);
        else classes.delete(c);
        return shouldAdd;
      },
      contains: (c) => classes.has(c),
    },
    setAttribute: (k, v) => {
      attrs[k] = String(v);
    },
    removeAttribute: (k) => {
      delete attrs[k];
    },
    getAttribute: (k) => (k in attrs ? attrs[k] : null),
    addEventListener: (ev, fn) => {
      listeners[ev] = fn;
    },
    trigger: (ev, eventObj = {}) => {
      if (listeners[ev]) {
        listeners[ev]({
          preventDefault: () => {},
          target: { closest: () => null },
          ...eventObj,
        });
      }
    },
    focus: () => {},
    scrollIntoView: () => {},
    querySelector: () => null,
    querySelectorAll: () => [],
  };
}

// Harness kiểm thử cho food-recommend.js
function createFoodRecommendHarness(apiPostImpl) {
  const els = {
    "food-recommend-form": createMockElement("food-recommend-form", false),
    "food-max-budget": createMockElement("food-max-budget", false),
    "food-meal-type": createMockElement("food-meal-type", false),
    "food-max-prep-time": createMockElement("food-max-prep-time", false),
    "food-avoid-ingredients": createMockElement("food-avoid-ingredients", false),
    "food-preferred-tags": createMockElement("food-preferred-tags", false),
    "food-preferred-tag-chips": createMockElement("food-preferred-tag-chips", false),
    "food-limit": createMockElement("food-limit", false),
    "food-max-budget-error": createMockElement("food-max-budget-error", false),
    "food-meal-type-error": createMockElement("food-meal-type-error", false),
    "food-max-prep-time-error": createMockElement("food-max-prep-time-error", false),
    "food-avoid-ingredients-error": createMockElement("food-avoid-ingredients-error", false),
    "food-preferred-tags-error": createMockElement("food-preferred-tags-error", false),
    "food-limit-error": createMockElement("food-limit-error", false),
    "food-recommend-status": createMockElement("food-recommend-status", true),
    "btn-food-recommend-submit": createMockElement("btn-food-recommend-submit", false),
    "btn-food-recommend-reset": createMockElement("btn-food-recommend-reset", false),

    "results-initial-state": createMockElement("results-initial-state", false),
    "results-loading-state": createMockElement("results-loading-state", true),
    "results-empty-state": createMockElement("results-empty-state", true),
    "results-empty-title": createMockElement("results-empty-title", false),
    "results-empty-desc": createMockElement("results-empty-desc", false),
    "results-error-state": createMockElement("results-error-state", true),
    "results-error-title": createMockElement("results-error-title", false),
    "results-error-desc": createMockElement("results-error-desc", false),
    "results-success-content": createMockElement("results-success-content", true),
    "results-excluded-section": createMockElement("results-excluded-section", true),

    "btn-results-focus-form": createMockElement("btn-results-focus-form", false),
    "btn-results-adjust-criteria": createMockElement("btn-results-adjust-criteria", false),
    "btn-results-retry-empty": createMockElement("btn-results-retry-empty", false),
    "btn-results-retry-error": createMockElement("btn-results-retry-error", false),
    "btn-results-error-adjust": createMockElement("btn-results-error-adjust", false),

    "results-ranking-list": createMockElement("results-ranking-list", false),
    "results-explanation-body": createMockElement("results-explanation-body", false),
    "results-total": createMockElement("results-total", false),
    "results-top-name": createMockElement("results-top-name", false),
    "results-top-score": createMockElement("results-top-score", false),
  };

  els["food-limit"].value = "5";
  els["food-recommend-form"].querySelector = () => els["btn-food-recommend-submit"];

  const apiCalls = [];
  const api = {
    post: (url, body, options) => {
      apiCalls.push({ url, body, options });
      return apiPostImpl(url, body, options);
    },
  };

  const DHResults = {
    initSidebar: () => {},
    initResultsPage: ({ results: items }) => {
      els["results-ranking-list"].innerHTML = items
        .map((it) => `<li>${it.name}</li>`)
        .join("");
    },
    renderExcludedCandidates: (excluded) => {
      els["results-excluded-section"].innerHTML = `Excluded: ${excluded.length}`;
    },
  };

  const windowObj = {
    location: { search: "" },
    FOOD_CRITERIA: [
      { key: "price", label: "Giá", weight: 0.4 },
      { key: "preference", label: "Khẩu vị", weight: 0.35 },
      { key: "prep_time", label: "Thời gian", weight: 0.25 },
    ],
    DHResults,
    matchMedia: () => ({ matches: false }),
  };

  const documentObj = {
    readyState: "complete",
    getElementById: (id) => els[id] || null,
    addEventListener: () => {},
  };

  const context = vm.createContext({
    window: windowObj,
    document: documentObj,
    api,
    DHResults,
    URLSearchParams,
    setTimeout,
    console,
    escapeHtml: (v) => String(v ?? ""),
    formatMoney: (v) => Number(v).toLocaleString("vi-VN") + " ₫",
    showToast: () => {},
  });

  vm.runInContext(foodRecommendJs, context);
  return { els, apiCalls, DHFoodRecommend: windowObj.DHFoodRecommend };
}

// Kiểm tra tại một thời điểm chỉ có đúng 1 container trạng thái chính hiển thị
function countVisibleResultStates(els) {
  const stateIds = [
    "results-initial-state",
    "results-loading-state",
    "results-empty-state",
    "results-error-state",
    "results-success-content",
  ];
  return stateIds.filter((id) => !els[id].classList.contains("d-none"));
}

// Harness kiểm thử cho history.js
function createHistoryHarness({ loggedIn = true, apiGetImpl }) {
  const ids = [
    "history-page-title",
    "history-page-desc",
    "btn-back-to-list",
    "btn-reload-history",
    "history-auth-required",
    "history-list-view",
    "history-toolbar",
    "history-filter-chips",
    "count-filter-all",
    "count-filter-food",
    "count-filter-travel",
    "history-summary-counter",
    "history-loading",
    "history-error",
    "history-error-message",
    "btn-retry-history",
    "history-empty",
    "history-empty-title",
    "history-empty-desc",
    "btn-reset-history-filter",
    "history-cards-container",
    "history-pagination",
    "history-page-info",
    "btn-prev-page",
    "btn-next-page",
    "history-detail-view",
    "history-detail-loading",
    "history-detail-not-found",
    "history-detail-not-found-text",
    "btn-not-found-back",
    "history-detail-error",
    "history-detail-error-text",
    "btn-retry-detail",
    "btn-error-back",
    "history-detail-content",
  ];
  const els = {};
  ids.forEach((id) => {
    els[id] = createMockElement(id, id !== "history-list-view");
  });

  const apiCalls = [];
  const api = {
    session: { isLoggedIn: () => loggedIn },
    get: (url, params, options) => {
      apiCalls.push({ url, params, options });
      return apiGetImpl(url, params, options);
    },
  };

  const windowObj = {
    location: { href: "http://127.0.0.1:5500/frontend/pages/history.html", search: "" },
    history: { pushState: () => {} },
    addEventListener: () => {},
  };

  const documentObj = {
    readyState: "loading", // Không tự chạy init để test chủ động điều khiển từng bước
    getElementById: (id) => els[id] || null,
    querySelector: () => null,
    addEventListener: () => {},
  };

  const context = vm.createContext({
    window: windowObj,
    document: documentObj,
    api,
    URL,
    URLSearchParams,
    console,
    escapeHtml: (v) => String(v ?? ""),
    formatMoney: (v) => Number(v).toLocaleString("vi-VN") + " ₫",
    formatDateTime: () => "09:00 26/11/2026",
  });

  vm.runInContext(historyJs, context);
  return { els, apiCalls, DHHistory: windowObj.DHHistory };
}

async function runAllTests() {
  // -------------------------------------------------------------------------
  // Case 1, 6, 11: Submit form Food -> Loading -> chặn gửi trùng -> chuyển sang Success
  // -------------------------------------------------------------------------
  {
    let resolveRequest;
    const { els, apiCalls } = createFoodRecommendHarness(
      () =>
        new Promise((resolve) => {
          resolveRequest = resolve;
        }),
    );

    // Kiểm tra empty form khi chưa nhập ngân sách: không nhầm với Backend Empty State
    els["food-max-budget"].value = "";
    els["food-recommend-form"].trigger("submit");
    assert(
      "Form chưa nhập ngân sách: báo nhắc nhập liệu trên Form, không nhầm với Empty State từ API",
      els["food-max-budget-error"].textContent.includes("ngân sách tối đa") &&
        !els["results-initial-state"].classList.contains("d-none") &&
        els["results-empty-state"].classList.contains("d-none") &&
        apiCalls.length === 0,
    );

    // Nhập dữ liệu hợp lệ và submit
    els["food-max-budget"].value = "45000";
    els["food-meal-type"].value = "lunch";
    els["food-recommend-form"].trigger("submit");

    // Case 1: Hiển thị Loading, disable nút submit, giữ nguyên dữ liệu đã nhập
    assert(
      "Case 1: Submit form Food hiển thị Loading ở cả Form và khu vực Kết quả, giữ nguyên input",
      els["btn-food-recommend-submit"].disabled === true &&
        els["btn-food-recommend-submit"].innerHTML.includes("Đang tìm kiếm món ăn phù hợp...") &&
        !els["results-loading-state"].classList.contains("d-none") &&
        els["food-max-budget"].value === "45000" &&
        countVisibleResultStates(els).length === 1,
    );

    // Case 6: Submit liên tục nhiều lần trong khi đang xử lý -> không gửi request trùng
    els["food-recommend-form"].trigger("submit");
    els["food-recommend-form"].trigger("submit");
    assert(
      "Case 6: Submit liên tục nhiều lần không tạo request trùng ngoài ý muốn",
      apiCalls.length === 1,
    );

    // Hoàn tất request thành công có dữ liệu (Case 2 & Case 11)
    resolveRequest({
      success: true,
      message: "Đánh giá thành công 1 phương án.",
      items: [
        {
          id: 2,
          food_id: 2,
          name: "Bún chả Hà Nội",
          price: 35000,
          prep_time: 15,
          meal_type: "lunch",
          score: 82.5,
          total_score: 82.5,
          rank: 1,
          criteria_scores: { price: 80, preference: 90, prep_time: 75 },
          reasons: ["Giá hợp lý trong ngân sách"],
        },
      ],
      excluded_items: [],
    });
    await new Promise((r) => setTimeout(r, 10));

    assert(
      "Case 2 & Case 11: Recommend thành công hiển thị kết quả, Loading biến mất hoàn toàn và nút Submit được khôi phục",
      els["results-loading-state"].classList.contains("d-none") &&
        !els["results-success-content"].classList.contains("d-none") &&
        els["btn-food-recommend-submit"].disabled === false &&
        els["results-top-name"].textContent === "Bún chả Hà Nội" &&
        countVisibleResultStates(els).length === 1,
    );
  }

  // -------------------------------------------------------------------------
  // Case 3 & Case 12: Recommend thành công nhưng không có dữ liệu -> Empty State (không chồng giao diện)
  // -------------------------------------------------------------------------
  {
    const { els, DHFoodRecommend } = createFoodRecommendHarness(async () => ({
      success: true,
      has_valid_candidates: false,
      items: [],
      excluded_items: [
        {
          id: 1,
          name: "Phở bò",
          exclusion_reason: "Vượt quá ngân sách tối đa",
        },
      ],
      message: "Không có phương án hợp lệ.",
    }));

    await DHFoodRecommend.executeRecommendation({ budget_max: 10000, meal_type: "lunch", limit: 5 });

    assert(
      "Case 3 & Case 12: API trả về 0 món hợp lệ -> hiển thị Empty State rõ ràng, không chồng lên Loading/Success/Error",
      !els["results-empty-state"].classList.contains("d-none") &&
        els["results-empty-title"].textContent.includes("Không tìm thấy món ăn phù hợp") &&
        countVisibleResultStates(els).length === 1,
    );
  }

  // -------------------------------------------------------------------------
  // Case 4, Case 5 & Case 12: Recommend API lỗi -> Error State -> Nhấn Thử lại -> Phục hồi thành công
  // -------------------------------------------------------------------------
  {
    let attempt = 0;
    const { els, apiCalls } = createFoodRecommendHarness(async () => {
      attempt += 1;
      if (attempt === 1) {
        const err = new Error("Traceback: OperationalError pymysql connection refused");
        err.status = 500;
        throw err;
      }
      return {
        success: true,
        items: [
          {
            id: 5,
            food_id: 5,
            name: "Cơm chiên đậu hũ nấm",
            price: 30000,
            prep_time: 12,
            meal_type: "lunch",
            score: 76.0,
            total_score: 76.0,
            rank: 1,
            criteria_scores: { price: 90, preference: 60, prep_time: 80 },
            reasons: ["Phù hợp ngân sách"],
          },
        ],
        excluded_items: [],
      };
    });

    els["food-max-budget"].value = "40000";
    els["food-meal-type"].value = "lunch";
    els["food-recommend-form"].trigger("submit");
    await new Promise((r) => setTimeout(r, 10));

    // Case 4: Hiển thị Error State, ẩn thông báo kỹ thuật thô (Traceback / pymysql)
    assert(
      "Case 4 & Case 12: API Recommend lỗi hiển thị Error State thân thiện, không lộ stack trace kỹ thuật và không chồng giao diện",
      !els["results-error-state"].classList.contains("d-none") &&
        !els["results-error-desc"].textContent.includes("Traceback") &&
        countVisibleResultStates(els).length === 1,
    );

    // Case 5: Nhấn nút Thử lại -> gọi lại API đúng payload đã nhập (budget_max = 40000) và cập nhật sang Success
    els["btn-results-retry-error"].trigger("click");
    await new Promise((r) => setTimeout(r, 10));

    assert(
      "Case 5: Nhấn Thử lại gọi lại API với đúng dữ liệu người dùng đã nhập và cập nhật trạng thái sang Success",
      apiCalls.length === 2 &&
        apiCalls[1].body.budget_max === 40000 &&
        apiCalls[1].body.meal_type === "lunch" &&
        !els["results-success-content"].classList.contains("d-none") &&
        els["results-error-state"].classList.contains("d-none") &&
        els["results-top-name"].textContent === "Cơm chiên đậu hũ nấm",
    );
  }

  // -------------------------------------------------------------------------
  // Case 7, 8, 9, 10: Lịch sử quyết định Food (Success, Empty, Error + Retry, Auth 401, Chống gọi trùng)
  // -------------------------------------------------------------------------
  {
    // Case 7: Tải lịch sử có dữ liệu & chặn gọi trùng liên tiếp
    let resolveHist;
    const { els, apiCalls, DHHistory } = createHistoryHarness({
      loggedIn: true,
      apiGetImpl: () =>
        new Promise((resolve) => {
          resolveHist = resolve;
        }),
    });

    const p1 = DHHistory.loadHistoryList({ offset: 0 });
    const p2 = DHHistory.loadHistoryList({ offset: 0 }); // Gọi trùng khi đang loading
    assert(
      "History Loading: Hiển thị loading và chặn tạo nhiều request trùng khi thao tác liên tục",
      !els["history-loading"].classList.contains("d-none") && apiCalls.length === 1,
    );

    resolveHist({
      success: true,
      total: 1,
      data: [
        {
          id: 11,
          user_id: 1,
          domain: "food",
          created_at: "2026-11-26T09:00:00",
          input_snapshot: { budget_max: 50000, meal_type: "lunch" },
          result_snapshot: {
            total: 1,
            total_excluded: 0,
            items: [{ id: 2, name: "Bún chả Hà Nội", total_score: 85.0, price: 35000 }],
          },
        },
      ],
    });
    await Promise.all([p1, p2]);

    assert(
      "Case 7: Tải lịch sử có dữ liệu -> ẩn Loading, hiển thị danh sách quyết định Food",
      els["history-loading"].classList.contains("d-none") &&
        !els["history-cards-container"].classList.contains("d-none") &&
        els["history-cards-container"].innerHTML.includes("Bún chả Hà Nội"),
    );
  }

  {
    // Case 8: Tải lịch sử nhưng chưa có dữ liệu -> Empty State chuẩn nội dung Food
    const { els, DHHistory } = createHistoryHarness({
      loggedIn: true,
      apiGetImpl: async () => ({ success: true, total: 0, data: [] }),
    });
    await DHHistory.loadHistoryList({ offset: 0 });

    assert(
      "Case 8: Chưa có lịch sử quyết định -> hiển thị Empty State 'Bạn chưa có quyết định món ăn nào.' và nút 'Tìm món ăn ngay'",
      !els["history-empty"].classList.contains("d-none") &&
        els["history-empty-title"].textContent.includes("Bạn chưa có quyết định món ăn nào") &&
        historyHtml.includes("Tìm món ăn ngay") &&
        historyHtml.includes('href="food-results.html"'),
    );
  }

  {
    // Case 9: API lịch sử bị lỗi -> Hiển thị Error và nút Retry hoạt động
    let callCount = 0;
    const { els, DHHistory } = createHistoryHarness({
      loggedIn: true,
      apiGetImpl: async () => {
        callCount += 1;
        if (callCount === 1) {
          const err = new Error("Network failure");
          err.status = 0;
          throw err;
        }
        return { success: true, total: 0, data: [] };
      },
    });
    DHHistory.initHistoryPage();
    await new Promise((r) => setTimeout(r, 10));

    assert(
      "Case 9: API lịch sử lỗi -> hiển thị Error State thân thiện kèm nút Thử lại",
      !els["history-error"].classList.contains("d-none") &&
        els["history-loading"].classList.contains("d-none"),
    );

    els["btn-retry-history"].trigger("click");
    await new Promise((r) => setTimeout(r, 10));
    assert(
      "Case 9 (Retry): Nhấn Thử lại trên trang Lịch sử gọi lại API và chuyển sang trạng thái hợp lệ",
      callCount === 2 &&
        els["history-error"].classList.contains("d-none") &&
        !els["history-empty"].classList.contains("d-none"),
    );
  }

  {
    // Case 10: Chưa đăng nhập hoặc token hết hạn -> xử lý theo cơ chế auth hiện có
    const { els, DHHistory } = createHistoryHarness({
      loggedIn: false,
      apiGetImpl: async () => ({}),
    });
    await DHHistory.loadHistoryList({ offset: 0 });

    assert(
      "Case 10: Token hết hạn hoặc chưa đăng nhập -> hiển thị khu vực yêu cầu xác thực (#history-auth-required)",
      !els["history-auth-required"].classList.contains("d-none") &&
        els["history-list-view"].classList.contains("d-none"),
    );
  }

  // -------------------------------------------------------------------------
  // Case 13: Responsive & Chuẩn HTML/CSS của luồng Food
  // -------------------------------------------------------------------------
  assert(
    "Case 13: Responsive trên màn hình nhỏ & không chứa dummy card hay inline onclick",
    resultsCss.includes("@media (max-width: 575.98px)") &&
      !foodHtml.includes("Some quick example text") &&
      !/\sonclick\s*=/i.test(foodResultsHtml) &&
      !/\sonclick\s*=/i.test(foodHtml) &&
      !/\sonclick\s*=/i.test(historyHtml),
  );

  const failed = results.filter((r) => !r.ok);
  results.forEach((r) => {
    console.log(`${r.ok ? "PASS" : "FAIL"} - ${r.name}${r.detail ? " (" + r.detail + ")" : ""}`);
  });
  process.exit(failed.length > 0 ? 1 : 0);
}

runAllTests();

