// Kiểm thử tự động cho giao diện Lịch sử quyết định (frontend/js/pages/history.js,
// frontend/pages/history.html, frontend/css/history.css).
// Chạy: node frontend/tests/history.test.js

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const htmlSource = fs.readFileSync(
  path.join(__dirname, "..", "pages", "history.html"),
  "utf8",
);
const cssSource = fs.readFileSync(
  path.join(__dirname, "..", "css", "history.css"),
  "utf8",
);
const jsSource = fs.readFileSync(
  path.join(__dirname, "..", "js", "pages", "history.js"),
  "utf8",
);

const results = [];
function assert(name, condition, detail = "") {
  results.push({ ok: Boolean(condition), name, detail });
}

// ---------------------------------------------------------------------------
// 1. Kiểm tra cấu trúc HTML, CSS Guidelines & Responsive (Trường hợp 9)
// ---------------------------------------------------------------------------
function testStaticHtmlAndCss() {
  // Kiểm tra thứ tự import CSS bắt buộc: Bootstrap -> variables -> common -> components -> history
  const cssOrder = [
    "bootstrap.min.css",
    "../css/variables.css",
    "../css/common.css",
    "../css/components.css",
    "../css/history.css",
  ];
  let lastIdx = -1;
  let orderValid = true;
  for (const href of cssOrder) {
    const idx = htmlSource.indexOf(href);
    if (idx === -1 || idx <= lastIdx) {
      orderValid = false;
      break;
    }
    lastIdx = idx;
  }
  assert("Thứ tự import CSS đúng chuẩn UI Guidelines", orderValid);

  // Không có inline onclick trong HTML
  assert(
    "Không sử dụng thuộc tính inline onclick trong history.html",
    !/\sonclick\s*=/i.test(htmlSource),
  );

  // Kiểm tra tất cả rule CSS trong history.css đều nằm trong namespace .history-page
  const strippedCss = cssSource
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/@media[^{]+\{/g, "")
    .trim();
  const selectorBlocks = strippedCss.split("}").map((b) => b.trim()).filter(Boolean);
  const nonNamespaced = selectorBlocks.filter((block) => {
    const selPart = block.split("{")[0];
    if (!selPart) return false;
    const selectors = selPart.split(",").map((s) => s.trim()).filter(Boolean);
    return selectors.some((s) => !s.startsWith(".history-page"));
  });
  assert(
    "Mọi selector trong history.css đều có namespace .history-page",
    nonNamespaced.length === 0,
    nonNamespaced.join(" | "),
  );

  // Kiểm tra responsive breakpoints
  assert(
    "Có responsive media queries cho Tablet (<992px) và Mobile (<576px)",
    cssSource.includes("991.98px") && cssSource.includes("575.98px"),
  );
}

// ---------------------------------------------------------------------------
// 2. Stub DOM tối giản để chạy history.js trong Node.js
// ---------------------------------------------------------------------------
function createMockDom() {
  const elements = {};
  const elementIds = [
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

  function makeEl(id) {
    const classes = new Set(["d-none"]);
    const attrs = {};
    const listeners = {};
    return {
      id,
      textContent: "",
      innerHTML: "",
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
      getAttribute: (k) => attrs[k] || null,
      addEventListener: (ev, fn) => {
        listeners[ev] = fn;
      },
      querySelectorAll: () => [],
    };
  }

  elementIds.forEach((id) => {
    elements[id] = makeEl(id);
  });

  // Mặc định listView hiển thị
  elements["history-list-view"].classList.remove("d-none");

  const filterChipEls = ["all", "food", "travel"].map((type) => {
    const chip = makeEl("chip-" + type);
    chip.classList.remove("d-none");
    if (type === "all") chip.classList.add("active");
    chip.dataset.type = type;
    return chip;
  });
  elements["history-filter-chips"].querySelectorAll = () => filterChipEls;

  return elements;
}

function createHarness({ loggedIn = true, apiGetImpl }) {
  const elements = createMockDom();
  const apiCalls = [];

  const api = {
    session: {
      isLoggedIn: () => loggedIn,
    },
    get: async (url, params, options) => {
      apiCalls.push({ url, params, options });
      return apiGetImpl(url, params, options);
    },
  };

  const windowObj = {
    location: {
      href: "http://127.0.0.1:5500/frontend/pages/history.html",
      search: "",
    },
    history: {
      pushState: (_state, _title, newUrl) => {
        const parsed = new URL(newUrl);
        windowObj.location.href = parsed.toString();
        windowObj.location.search = parsed.search;
      },
    },
    addEventListener: () => {},
  };

  const documentObj = {
    readyState: "complete",
    getElementById: (id) => elements[id] || null,
    querySelector: () => null,
    addEventListener: () => {},
    createElement: () => {
      let txt = "";
      return {
        set textContent(v) {
          txt = String(v ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
        },
        get innerHTML() {
          return txt;
        },
      };
    },
  };

  const context = vm.createContext({
    window: windowObj,
    document: documentObj,
    api,
    URL,
    URLSearchParams,
    console,
    escapeHtml: (v) =>
      String(v ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;"),
    formatMoney: (v) => Number(v).toLocaleString("vi-VN") + " ₫",
    formatDateTime: (v) => "16:00 23/11/2026",
  });

  vm.runInContext(jsSource, context);
  return { elements, apiCalls, DHHistory: windowObj.DHHistory, windowObj };
}

// Dữ liệu mẫu đúng chuẩn Backend DecisionHistoryListResponse & DecisionHistoryDetailResponse
const SAMPLE_FOOD_DECISION = {
  id: 101,
  user_id: 1,
  domain: "food",
  created_at: "2026-11-23T16:00:00",
  input_snapshot: {
    budget_max: 50000,
    meal_type: "lunch",
    max_prep_time: 25,
    excluded_ingredients: ["Đậu phộng"],
    preferred_tags: ["truyền thống"],
    limit: 5,
    weights: null,
  },
  result_snapshot: {
    success: true,
    message: "Đánh giá thành công 2 phương án hợp lệ.",
    has_valid_candidates: true,
    total: 2,
    total_excluded: 1,
    limit: 5,
    items: [
      {
        food_id: 2,
        id: 2,
        name: "Bún chả Hà Nội",
        price: 35000,
        meal_type: "lunch",
        prep_time: 20,
        tags: ["truyền thống", "đậm đà"],
        score: 77.5,
        total_score: 77.5,
        rank: 1,
        criteria_scores: { price: 100.0, preference: 50.0, prep_time: 80.0 },
        criteria_details: {
          price: { normalized_score: 100.0, weight: 0.4, contribution: 40.0 },
          preference: { normalized_score: 50.0, weight: 0.35, contribution: 17.5 },
          prep_time: { normalized_score: 80.0, weight: 0.25, contribution: 20.0 },
        },
        reasons: [
          "Giá 35.000đ nằm trong ngân sách tối đa 50.000đ",
          "Phù hợp khẩu vị ưu tiên: truyền thống",
        ],
      },
      {
        food_id: 1,
        id: 1,
        name: "Phở bò tái",
        price: 45000,
        meal_type: "lunch",
        prep_time: 15,
        tags: ["truyền thống"],
        score: 62.0,
        total_score: 62.0,
        rank: 2,
        criteria_scores: { price: 50.0, preference: 50.0, prep_time: 100.0 },
        reasons: ["Giá 45.000đ nằm trong ngân sách tối đa 50.000đ"],
      },
    ],
    excluded_items: [
      {
        id: 4,
        name: "Cơm tấm sườn bì chả",
        status: "excluded",
        is_excluded: true,
        exclusion_reason: "Giá (55,000đ) vượt quá ngân sách tối đa (50,000đ).",
        exclusion_reasons: ["Giá (55,000đ) vượt quá ngân sách tối đa (50,000đ)."],
      },
    ],
    scoring: {
      method: "WSM",
      weights: { price: 0.4, preference: 0.35, prep_time: 0.25 },
    },
  },
};

const SAMPLE_TRAVEL_DECISION = {
  id: 102,
  user_id: 1,
  domain: "travel",
  created_at: "2026-11-23T18:30:00",
  input_snapshot: {
    budget_max: 2000000,
    region: "Bắc",
    max_duration: 24,
    activity_type: "Khám phá thiên nhiên",
    preferred_highlights: ["cáp treo"],
    limit: 5,
  },
  result_snapshot: {
    success: true,
    message: "Đánh giá thành công 1 phương án hợp lệ.",
    has_valid_candidates: true,
    total: 1,
    total_excluded: 0,
    limit: 5,
    items: [
      {
        destination_id: 2,
        id: 2,
        name: "Quần thể danh thắng Tràng An",
        province_city: "Ninh Bình",
        estimated_cost: 450000,
        estimated_duration: 6.0,
        score: 88.5,
        total_score: 88.5,
        rank: 1,
        criteria_scores: { estimated_cost: 100.0, estimated_duration: 100.0, activities: 61.67 },
        reasons: ["Chi phí tham khảo 450.000đ nằm trong ngân sách 2.000.000đ"],
      },
    ],
    excluded_items: [],
  },
};

async function runTests() {
  testStaticHtmlAndCss();

  // -------------------------------------------------------------------------
  // Trường hợp 1, 3, 8: Đã đăng nhập, có nhiều quyết định (Food + Travel) & Lọc
  // -------------------------------------------------------------------------
  {
    const { elements, apiCalls, DHHistory } = createHarness({
      loggedIn: true,
      apiGetImpl: async () => ({
        success: true,
        message: "OK",
        data: [SAMPLE_FOOD_DECISION, SAMPLE_TRAVEL_DECISION],
        items: [SAMPLE_FOOD_DECISION, SAMPLE_TRAVEL_DECISION],
        total: 25,
        limit: 10,
        offset: 0,
      }),
    });

    await DHHistory.loadHistoryList({ offset: 0 });

    assert(
      "TH1 & TH3: Gọi đúng endpoint GET /decisions/history với authMode='required'",
      apiCalls.length >= 1 &&
        apiCalls[0].url === "/decisions/history" &&
        apiCalls[0].options.authMode === "required",
    );
    assert(
      "TH1 & TH3: Hiển thị danh sách card quyết định",
      !elements["history-cards-container"].classList.contains("d-none") &&
        elements["history-cards-container"].innerHTML.includes("Bún chả Hà Nội") &&
        elements["history-cards-container"].innerHTML.includes("Quần thể danh thắng Tràng An"),
    );
    assert(
      "TH3: Hiển thị thanh phân trang khi total > limit",
      !elements["history-pagination"].classList.contains("d-none") &&
        elements["history-page-info"].textContent.includes("25"),
    );

    // Trường hợp 8: Lọc theo Food / Travel
    DHHistory.setFilter("food");
    assert(
      "TH8: Lọc Food chỉ hiển thị quyết định Food",
      elements["history-cards-container"].innerHTML.includes("Bún chả Hà Nội") &&
        !elements["history-cards-container"].innerHTML.includes("Quần thể danh thắng Tràng An"),
    );

    DHHistory.setFilter("travel");
    assert(
      "TH8: Lọc Travel chỉ hiển thị quyết định Travel",
      !elements["history-cards-container"].innerHTML.includes("Bún chả Hà Nội") &&
        elements["history-cards-container"].innerHTML.includes("Quần thể danh thắng Tràng An"),
    );
  }

  // -------------------------------------------------------------------------
  // Trường hợp 2: Người dùng chưa có lịch sử quyết định (Empty state)
  // -------------------------------------------------------------------------
  {
    const { elements, DHHistory } = createHarness({
      loggedIn: true,
      apiGetImpl: async () => ({
        success: true,
        message: "OK",
        data: [],
        items: [],
        total: 0,
        limit: 10,
        offset: 0,
      }),
    });

    await DHHistory.loadHistoryList({ offset: 0 });

    assert(
      "TH2: Hiển thị empty state khi chưa có lịch sử quyết định",
      !elements["history-empty"].classList.contains("d-none") &&
        elements["history-cards-container"].classList.contains("d-none"),
    );
  }

  // -------------------------------------------------------------------------
  // Trường hợp 4: Xem chi tiết một quyết định
  // -------------------------------------------------------------------------
  {
    const { elements, apiCalls, DHHistory } = createHarness({
      loggedIn: true,
      apiGetImpl: async (url) => {
        if (url === "/decisions/history/101") {
          return {
            success: true,
            message: "OK",
            data: SAMPLE_FOOD_DECISION,
            ...SAMPLE_FOOD_DECISION,
          };
        }
        return { success: true, data: [SAMPLE_FOOD_DECISION], total: 1 };
      },
    });

    await DHHistory.openDecisionDetail(101);

    const detailCall = apiCalls.find((c) => c.url === "/decisions/history/101");
    assert(
      "TH4: Gọi đúng endpoint GET /decisions/history/101 với authMode='required'",
      Boolean(detailCall) && detailCall.options.authMode === "required",
    );
    const html = elements["history-detail-content"].innerHTML;
    assert(
      "TH4: Hiển thị đầy đủ Input Snapshot, Bảng xếp hạng (Top 1 nổi bật vs Hạng 2), Điểm số, Lý do đề xuất và Phương án bị loại",
      !elements["history-detail-content"].classList.contains("d-none") &&
        html.includes("Bún chả Hà Nội") &&
        html.includes("Phở bò tái") &&
        html.includes("is-top-rank") &&
        html.includes("Giá 35.000đ nằm trong ngân sách tối đa 50.000đ") &&
        html.includes("Cơm tấm sườn bì chả") &&
        html.includes("budget_max"),
    );
  }

  // -------------------------------------------------------------------------
  // Trường hợp 5: ID quyết định không tồn tại (404)
  // -------------------------------------------------------------------------
  {
    const { elements, DHHistory } = createHarness({
      loggedIn: true,
      apiGetImpl: async () => {
        const err = new Error("Lỗi 404");
        err.status = 404;
        err.data = {
          success: false,
          message: "Lịch sử quyết định với mã 9999 không tồn tại.",
          error_code: "RESOURCE_NOT_FOUND",
        };
        throw err;
      },
    });

    await DHHistory.openDecisionDetail(9999);

    assert(
      "TH5: Hiển thị trạng thái không tìm thấy quyết định khi API trả về 404",
      !elements["history-detail-not-found"].classList.contains("d-none") &&
        elements["history-detail-not-found-text"].textContent.includes("9999"),
    );
  }

  // -------------------------------------------------------------------------
  // Trường hợp 6: API bị lỗi hoặc mất kết nối
  // -------------------------------------------------------------------------
  {
    const { elements, DHHistory } = createHarness({
      loggedIn: true,
      apiGetImpl: async () => {
        const err = new Error("Không kết nối được backend.");
        err.status = 0;
        throw err;
      },
    });

    await DHHistory.loadHistoryList();

    assert(
      "TH6: Hiển thị trạng thái lỗi và nút Thử lại khi mất kết nối API",
      !elements["history-error"].classList.contains("d-none") &&
        elements["history-error-message"].textContent.includes("Không kết nối được backend"),
    );
  }

  // -------------------------------------------------------------------------
  // Trường hợp 7: Người dùng chưa đăng nhập hoặc token hết hạn (401)
  // -------------------------------------------------------------------------
  {
    const { elements, DHHistory } = createHarness({
      loggedIn: false,
      apiGetImpl: async () => ({}),
    });

    await DHHistory.loadHistoryList();

    assert(
      "TH7: Hiển thị yêu cầu đăng nhập khi người dùng chưa đăng nhập hoặc token hết hạn",
      !elements["history-auth-required"].classList.contains("d-none") &&
        elements["history-list-view"].classList.contains("d-none"),
    );
  }

  // Tổng kết kết quả
  const failed = results.filter((r) => !r.ok);
  results.forEach((r) => {
    console.log(
      `${r.ok ? "PASS" : "FAIL"} - ${r.name}${r.detail ? " (" + r.detail + ")" : ""}`,
    );
  });
  process.exit(failed.length > 0 ? 1 : 0);
}

runTests();

