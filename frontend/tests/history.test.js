// Kiểm thử tự động cho giao diện Lịch sử quyết định & Modal Xem lại chi tiết
// (frontend/js/pages/history.js, frontend/pages/history.html, frontend/css/history.css).
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
// 1. Kiểm tra cấu trúc HTML, CSS Guidelines, Light Overlay/Blur & Responsive
// ---------------------------------------------------------------------------
function testStaticHtmlAndCss() {
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

  assert(
    "Không sử dụng thuộc tính inline onclick/onerror trong history.html",
    !/\son(click|error)\s*=/i.test(htmlSource),
  );

  assert(
    "Có cấu trúc Modal Chi tiết quyết định căn giữa với role='dialog' và aria-modal='true'",
    htmlSource.includes('id="history-detail-modal"') &&
      htmlSource.includes('role="dialog"') &&
      htmlSource.includes('aria-modal="true"') &&
      htmlSource.includes("Chi tiết quyết định"),
  );

  assert(
    "Overlay sử dụng nền xám nhạt trong suốt kèm backdrop-filter: blur() và vùng cuộn độc lập",
    cssSource.includes("backdrop-filter: blur") &&
      cssSource.includes("overflow-y: auto") &&
      cssSource.includes("overscroll-behavior: contain") &&
      cssSource.includes(".history-page.history-modal-open"),
  );

  // Kiểm tra mọi selector trong history.css đều có namespace .history-page
  const strippedCss = cssSource
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/@media[^{]+\{/g, "")
    .trim();
  const selectorBlocks = strippedCss
    .split("}")
    .map((b) => b.trim())
    .filter(Boolean);
  const nonNamespaced = selectorBlocks.filter((block) => {
    const selPart = block.split("{")[0];
    if (!selPart) return false;
    const selectors = selPart
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    return selectors.some((s) => !s.startsWith(".history-page"));
  });
  assert(
    "Mọi selector trong history.css đều có namespace .history-page",
    nonNamespaced.length === 0,
    nonNamespaced.join(" | "),
  );

  assert(
    "Có responsive media queries cho Tablet (<992px), Mobile ngang (<768px) và Mobile nhỏ (<576px)",
    cssSource.includes("991.98px") &&
      cssSource.includes("767.98px") &&
      cssSource.includes("575.98px"),
  );
}

// ---------------------------------------------------------------------------
// 2. Stub DOM để kiểm thử đầy đủ hành vi Modal, Scroll Lock, ESC, Backdrop
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
    "history-detail-modal",
    "history-detail-view",
    "history-modal-subtitle",
    "history-modal-body",
    "btn-close-detail-modal",
    "btn-footer-close-modal",
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
      scrollTop: 0,
      offsetWidth: 860,
      style: {},
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
        if (!listeners[ev]) listeners[ev] = [];
        listeners[ev].push(fn);
      },
      dispatchEvent: (evName, eventPayload = {}) => {
        (listeners[evName] || []).forEach((fn) => fn(eventPayload));
      },
      querySelectorAll: () => [],
    };
  }

  elementIds.forEach((id) => {
    elements[id] = makeEl(id);
  });

  // Mặc định listView, modalBody và nút đóng hiển thị bên trong khung
  elements["history-list-view"].classList.remove("d-none");
  elements["history-modal-body"].classList.remove("d-none");
  elements["btn-close-detail-modal"].classList.remove("d-none");
  elements["btn-footer-close-modal"].classList.remove("d-none");

  const filterChipEls = ["all", "food", "travel"].map((type) => {
    const chip = makeEl("chip-" + type);
    chip.classList.remove("d-none");
    if (type === "all") chip.classList.add("active");
    chip.dataset.type = type;
    return chip;
  });
  elements["history-filter-chips"].querySelectorAll = () => filterChipEls;

  return { elements, makeEl };
}

function createHarness({ loggedIn = true, initialScrollY = 0, apiGetImpl }) {
  const { elements, makeEl } = createMockDom();
  const apiCalls = [];
  const docListeners = {};
  const bodyEl = makeEl("body");
  bodyEl.classList.remove("d-none");
  bodyEl.classList.add("history-page");

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
    innerWidth: 1280,
    scrollY: initialScrollY,
    pageYOffset: initialScrollY,
    scrollTo: (_x, y) => {
      windowObj.scrollY = y;
      windowObj.pageYOffset = y;
    },
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
      replaceState: (_state, _title, newUrl) => {
        const parsed = new URL(newUrl);
        windowObj.location.href = parsed.toString();
        windowObj.location.search = parsed.search;
      },
    },
    addEventListener: () => {},
  };

  const documentObj = {
    readyState: "complete",
    body: bodyEl,
    documentElement: { clientWidth: 1265, scrollTop: initialScrollY },
    getElementById: (id) => elements[id] || null,
    querySelector: () => null,
    addEventListener: (ev, fn) => {
      if (!docListeners[ev]) docListeners[ev] = [];
      docListeners[ev].push(fn);
    },
    dispatchDocumentEvent: (evName, payload = {}) => {
      (docListeners[evName] || []).forEach((fn) => fn(payload));
    },
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
    formatDateTime: () => "16:00 23/11/2026",
  });

  vm.runInContext(jsSource, context);
  return {
    elements,
    bodyEl,
    documentObj,
    apiCalls,
    DHHistory: windowObj.DHHistory,
    windowObj,
  };
}

const SAMPLE_FOOD_DECISION = {
  id: 101,
  user_id: 1,
  domain: "food",
  created_at: "2026-11-23T16:00:00",
  input_snapshot: {
    budget_max: 50000,
    people_count: 2,
    meal_type: "lunch",
    max_prep_time: 25,
    excluded_ingredients: ["Đậu phộng"],
    preferred_tags: ["truyền thống"],
    special_requirements: "Ít dầu mỡ",
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
        description: "Thịt nướng than hoa ăn kèm bún tươi và nước chấm chua ngọt.",
        image_url: "../assets/images/foods/buncha.jpg",
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

const SAMPLE_SPARSE_DECISION = {
  id: 105,
  user_id: 1,
  domain: "food",
  created_at: "2026-11-24T12:00:00",
  input_snapshot: {
    budget_max: 40000,
  },
  result_snapshot: {
    success: true,
    total: 1,
    total_excluded: 0,
    items: [
      {
        food_id: 9,
        name: "Bánh mì thịt nguội",
        // Cố tình thiếu image_url, description, score, reasons để kiểm tra fallback an toàn
      },
    ],
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
  // Trường hợp 1, 3, 8: Danh sách lịch sử, nút "Xem lại", Phân trang & Lọc
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
      "TH1: Hiển thị danh sách card quyết định kèm nút 'Xem lại'",
      !elements["history-cards-container"].classList.contains("d-none") &&
        elements["history-cards-container"].innerHTML.includes("Bún chả Hà Nội") &&
        elements["history-cards-container"].innerHTML.includes("Xem lại"),
    );
    assert(
      "TH3: Hiển thị thanh phân trang khi total > limit",
      !elements["history-pagination"].classList.contains("d-none") &&
        elements["history-page-info"].textContent.includes("25"),
    );

    DHHistory.setFilter("food");
    assert(
      "TH8: Lọc Food chỉ hiển thị quyết định Food",
      elements["history-cards-container"].innerHTML.includes("Bún chả Hà Nội") &&
        !elements["history-cards-container"].innerHTML.includes("Quần thể danh thắng Tràng An"),
    );
  }

  // -------------------------------------------------------------------------
  // Trường hợp 2: Empty state khi chưa có lịch sử
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
  // Trường hợp 4: Bấm "Xem lại" mở Modal chính giữa, giữ danh sách phía sau,
  // khóa scroll nền, hiển thị đầy đủ thông tin và đóng bằng X / Đóng / ESC / Backdrop
  // -------------------------------------------------------------------------
  {
    const { elements, bodyEl, documentObj, windowObj, apiCalls, DHHistory } = createHarness({
      loggedIn: true,
      initialScrollY: 420,
      apiGetImpl: async (url) => {
        if (url === "/decisions/history/101") {
          return {
            success: true,
            message: "OK",
            data: SAMPLE_FOOD_DECISION,
            ...SAMPLE_FOOD_DECISION,
          };
        }
        return {
          success: true,
          data: [SAMPLE_FOOD_DECISION, SAMPLE_TRAVEL_DECISION],
          total: 2,
        };
      },
    });

    await DHHistory.loadHistoryList({ offset: 0 });
    elements["history-modal-body"].scrollTop = 180;

    let focusedBack = false;
    const fakeTriggerBtn = {
      focus: () => {
        focusedBack = true;
      },
    };

    await DHHistory.openDecisionDetail(101, fakeTriggerBtn);

    const detailCall = apiCalls.find((c) => c.url === "/decisions/history/101");
    assert(
      "TH4.1: Gọi đúng endpoint GET /decisions/history/101 với authMode='required'",
      Boolean(detailCall) && detailCall.options.authMode === "required",
    );
    assert(
      "TH4.2: Mở Modal (.is-open, không .d-none) NHƯNG vẫn giữ nguyên danh sách lịch sử phía sau",
      !elements["history-detail-modal"].classList.contains("d-none") &&
        elements["history-detail-modal"].classList.contains("is-open") &&
        !elements["history-list-view"].classList.contains("d-none") &&
        !elements["history-cards-container"].classList.contains("d-none"),
    );
    assert(
      "TH4.3: Khóa scroll trang nền (body.history-modal-open) và đưa scroll bên trong Modal về đầu",
      bodyEl.classList.contains("history-modal-open") &&
        elements["history-modal-body"].scrollTop === 0,
    );

    const html = elements["history-detail-content"].innerHTML;
    assert(
      "TH4.4: Hiển thị đầy đủ Món nổi bật (ảnh, mô tả, điểm, hạng), Lý do đề xuất, Đầu vào (ngân sách, số người, yêu cầu đặc biệt) và Danh sách xếp hạng",
      !elements["history-detail-content"].classList.contains("d-none") &&
        html.includes("Bún chả Hà Nội") &&
        html.includes("Thịt nướng than hoa") &&
        html.includes("../assets/images/foods/buncha.jpg") &&
        html.includes("2 người") &&
        html.includes("Ít dầu mỡ") &&
        html.includes("Phở bò tái") &&
        html.includes("is-top-rank") &&
        html.includes("Giá 35.000đ nằm trong ngân sách tối đa 50.000đ") &&
        html.includes("Cơm tấm sườn bì chả") &&
        html.includes("budget_max"),
    );

    const listCallsBeforeClose = apiCalls.filter((c) => c.url === "/decisions/history").length;

    // Giả lập scroll bị lệch trong lúc mở, sau đó đóng bằng nút X
    windowObj.scrollY = 0;
    elements["btn-close-detail-modal"].dispatchEvent("click");

    assert(
      "TH4.5: Đóng Modal bằng nút X khôi phục scroll về đúng 420px, mở khóa nền, trả focus và không tải lại danh sách",
      elements["history-detail-modal"].classList.contains("d-none") &&
        !bodyEl.classList.contains("history-modal-open") &&
        windowObj.scrollY === 420 &&
        focusedBack === true &&
        apiCalls.filter((c) => c.url === "/decisions/history").length === listCallsBeforeClose,
    );

    // Mở lại và đóng bằng phím ESC
    await DHHistory.openDecisionDetail(101);
    let escPrevented = false;
    documentObj.dispatchDocumentEvent("keydown", {
      key: "Escape",
      preventDefault: () => {
        escPrevented = true;
      },
    });
    assert(
      "TH4.6: Đóng Modal bằng phím ESC hoạt động chính xác",
      escPrevented && elements["history-detail-modal"].classList.contains("d-none"),
    );

    // Mở lại và đóng bằng nút Đóng ở Footer
    await DHHistory.openDecisionDetail(101);
    elements["btn-footer-close-modal"].dispatchEvent("click");
    assert(
      "TH4.7: Đóng Modal bằng nút 'Đóng' ở Footer hoạt động chính xác",
      elements["history-detail-modal"].classList.contains("d-none"),
    );

    // Mở lại và bấm ra vùng backdrop bên ngoài Modal để đóng
    await DHHistory.openDecisionDetail(101);
    elements["history-detail-modal"].dispatchEvent("click", {
      target: elements["history-detail-modal"],
    });
    assert(
      "TH4.8: Bấm ra ngoài vùng overlay đóng Modal chính xác",
      elements["history-detail-modal"].classList.contains("d-none"),
    );
  }

  // -------------------------------------------------------------------------
  // Trường hợp 5: Fallback an toàn khi thiếu ảnh, mô tả, điểm số, lý do
  // -------------------------------------------------------------------------
  {
    const { elements, DHHistory } = createHarness({
      loggedIn: true,
      apiGetImpl: async (url) => {
        if (url === "/decisions/history/105") {
          return { success: true, data: SAMPLE_SPARSE_DECISION };
        }
        return { success: true, data: [SAMPLE_SPARSE_DECISION], total: 1 };
      },
    });

    await DHHistory.openDecisionDetail(105);
    const sparseHtml = elements["history-detail-content"].innerHTML;
    assert(
      "TH5: Xử lý an toàn dữ liệu thiếu ảnh, thiếu mô tả, thiếu điểm số mà không lỗi hoặc hiện NaN/undefined",
      !elements["history-detail-content"].classList.contains("d-none") &&
        sparseHtml.includes("Bánh mì thịt nguội") &&
        sparseHtml.includes("history-dish-fallback-icon") &&
        !sparseHtml.includes("NaN") &&
        !sparseHtml.includes("undefined"),
    );
  }

  // -------------------------------------------------------------------------
  // Trường hợp 6: ID quyết định không tồn tại (404) hiển thị ngay trong Modal
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
      "TH6: Hiển thị trạng thái không tìm thấy quyết định bên trong Modal khi API trả về 404",
      !elements["history-detail-modal"].classList.contains("d-none") &&
        !elements["history-detail-not-found"].classList.contains("d-none") &&
        elements["history-detail-not-found-text"].textContent.includes("9999"),
    );
  }

  // -------------------------------------------------------------------------
  // Trường hợp 7: API danh sách bị lỗi hoặc chưa đăng nhập (401)
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
      "TH7.1: Hiển thị trạng thái lỗi danh sách khi mất kết nối API",
      !elements["history-error"].classList.contains("d-none") &&
        elements["history-error-message"].textContent.includes("Không kết nối được backend"),
    );
  }

  {
    const { elements, DHHistory } = createHarness({
      loggedIn: false,
      apiGetImpl: async () => ({}),
    });

    await DHHistory.loadHistoryList();

    assert(
      "TH7.2: Hiển thị yêu cầu đăng nhập khi chưa đăng nhập",
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
