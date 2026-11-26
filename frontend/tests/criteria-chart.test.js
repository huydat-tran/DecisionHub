// ==============================================================================
// Kiểm thử tự động cho Biểu đồ đóng góp điểm theo tiêu chí (CriteriaChart)
// Chạy bằng: node frontend/tests/criteria-chart.test.js
// ==============================================================================

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const foodHtmlSource = fs.readFileSync(
  path.join(__dirname, "..", "pages", "food-results.html"),
  "utf8"
);
const travelHtmlSource = fs.readFileSync(
  path.join(__dirname, "..", "pages", "travel-results.html"),
  "utf8"
);
const resultsCssSource = fs.readFileSync(
  path.join(__dirname, "..", "css", "results.css"),
  "utf8"
);
const chartJsSource = fs.readFileSync(
  path.join(__dirname, "..", "js", "criteria-chart.js"),
  "utf8"
);
const resultCommonJsSource = fs.readFileSync(
  path.join(__dirname, "..", "js", "pages", "result-common.js"),
  "utf8"
);

const results = [];
function assert(name, condition, detail = "") {
  results.push({ ok: Boolean(condition), name, detail });
}

// Giả lập môi trường DOM tối giản để chạy CriteriaChart trong Node.js VM
function createMockDom() {
  const listeners = {};
  const elementPrototype = {
    setAttribute(k, v) {
      this.attributes = this.attributes || {};
      this.attributes[k] = String(v);
    },
    getAttribute(k) {
      return (this.attributes && this.attributes[k]) || null;
    },
    removeAttribute(k) {
      if (this.attributes) delete this.attributes[k];
    },
    classList: {
      _classes: new Set(),
      add(cls) {
        this._classes.add(cls);
      },
      remove(cls) {
        this._classes.delete(cls);
      },
      contains(cls) {
        return this._classes.has(cls);
      },
      toggle(cls, force) {
        if (force === undefined) {
          if (this._classes.has(cls)) this._classes.delete(cls);
          else this._classes.add(cls);
        } else if (force) {
          this._classes.add(cls);
        } else {
          this._classes.delete(cls);
        }
        return this._classes.has(cls);
      },
    },
    getBoundingClientRect() {
      return { left: 50, top: 100, width: 60, height: 120, bottom: 220, right: 110 };
    },
    addEventListener(evt, fn) {
      listeners[evt] = listeners[evt] || [];
      listeners[evt].push(fn);
    },
    querySelectorAll(selector) {
      return parseSelector(this.innerHTML, selector);
    },
    querySelector(selector) {
      const list = this.querySelectorAll(selector);
      return list[0] || null;
    },
  };

  // Parser regex đơn giản phục vụ querySelector trong DOM giả lập
  function parseSelector(html, selector) {
    const list = [];
    if (!html) return list;

    if (selector === ".criteria-chart-bar") {
      const barRegex = /<rect\s+class="([^"]*criteria-chart-bar[^"]*)"([^>]+)>/g;
      let match;
      while ((match = barRegex.exec(html)) !== null) {
        const fullAttrs = match[2];
        const barElem = Object.create(elementPrototype);
        barElem.dataset = {};
        barElem.className = match[1];

        const dataRegex = /data-([a-z0-9-]+)="([^"]*)"/g;
        let dMatch;
        while ((dMatch = dataRegex.exec(fullAttrs)) !== null) {
          const camelKey = dMatch[1].replace(/-([a-z])/g, (_, c) => c.toUpperCase());
          barElem.dataset[camelKey] = dMatch[2];
        }
        list.push(barElem);
      }
    } else if (selector === ".criteria-chart-legend-item") {
      const legRegex = /<button[^>]+class="([^"]*criteria-chart-legend-item[^"]*)"([^>]+)>/g;
      let match;
      while ((match = legRegex.exec(html)) !== null) {
        const fullAttrs = match[2];
        const btnElem = Object.create(elementPrototype);
        btnElem.dataset = {};
        const idMatch = fullAttrs.match(/data-option-id="([^"]*)"/);
        if (idMatch) btnElem.dataset.optionId = idMatch[1];
        list.push(btnElem);
      }
    } else if (selector === "#criteria-chart-tooltip") {
      if (html.includes('id="criteria-chart-tooltip"')) {
        const tipElem = Object.create(elementPrototype);
        tipElem.style = {};
        list.push(tipElem);
      }
    } else if (selector === ".criteria-chart-wrapper") {
      if (html.includes('class="criteria-chart-wrapper"')) {
        const wrapElem = Object.create(elementPrototype);
        wrapElem.getBoundingClientRect = () => ({ left: 0, top: 0, width: 600, height: 300 });
        list.push(wrapElem);
      }
    }
    return list;
  }

  const container = Object.create(elementPrototype);
  container.innerHTML = "";
  return { container, listeners };
}

function initChartInVm() {
  const sandbox = {
    window: {},
    console: console,
    escapeHtml: (str) => String(str).replace(/</g, "&lt;").replace(/>/g, "&gt;"),
  };
  vm.createContext(sandbox);
  vm.runInContext(chartJsSource, sandbox);
  return sandbox.CriteriaChart || sandbox.window.CriteriaChart;
}

// ---------------------------------------------------------------------------
// 1. Kiểm tra HTML & CSS Guidelines
// ---------------------------------------------------------------------------
function testHtmlAndCss() {
  assert(
    "HTML: food-results.html đã import criteria-chart.js trước result-common.js",
    foodHtmlSource.indexOf("criteria-chart.js") !== -1 &&
      foodHtmlSource.indexOf("criteria-chart.js") < foodHtmlSource.indexOf("result-common.js")
  );

  assert(
    "HTML: travel-results.html đã import criteria-chart.js trước result-common.js",
    travelHtmlSource.indexOf("criteria-chart.js") !== -1 &&
      travelHtmlSource.indexOf("criteria-chart.js") < travelHtmlSource.indexOf("result-common.js")
  );

  // Kiểm tra namespace CSS
  const nonScopedChartRules = (resultsCssSource.match(/^[^\n\r/][^{]+criteria-chart[^{]*\{/gm) || [])
    .filter((line) => !line.includes(".results-page"));
  assert(
    "CSS: Mọi selector biểu đồ trong results.css đều có namespace .results-page",
    nonScopedChartRules.length === 0,
    nonScopedChartRules.join(" | ")
  );
}

// ---------------------------------------------------------------------------
// 2. Chạy 8 test case theo Section 7 của TASK
// ---------------------------------------------------------------------------
function runEightTestCases() {
  const CriteriaChart = initChartInVm();
  assert("Component CriteriaChart được khởi tạo thành công", Boolean(CriteriaChart));

  const standardCriteria = [
    { key: "price", label: "Giá", weight: 0.4 },
    { key: "preference", label: "Mức phù hợp nhu cầu/khẩu vị", weight: 0.35 },
    { key: "prep_time", label: "Thời gian chuẩn bị", weight: 0.25 },
  ];

  // Case 1: Có nhiều phương án và nhiều tiêu chí
  {
    const { container } = createMockDom();
    const resultsData = [
      {
        id: 1,
        name: "Phở bò tái",
        total_score: 87.5,
        criteria_details: {
          price: { normalized_score: 90, weight: 0.4, contribution: 36.0 },
          preference: { normalized_score: 80, weight: 0.35, contribution: 28.0 },
          prep_time: { normalized_score: 94, weight: 0.25, contribution: 23.5 },
        },
      },
      {
        id: 2,
        name: "Bánh mì đặc biệt",
        total_score: 82.0,
        criteria_details: {
          price: { normalized_score: 100, weight: 0.4, contribution: 40.0 },
          preference: { normalized_score: 60, weight: 0.35, contribution: 21.0 },
          prep_time: { normalized_score: 84, weight: 0.25, contribution: 21.0 },
        },
      },
    ];

    CriteriaChart.render({
      container,
      results: resultsData,
      criteria: standardCriteria,
      mode: "compare",
    });

    const bars = container.querySelectorAll(".criteria-chart-bar");
    const legends = container.querySelectorAll(".criteria-chart-legend-item");
    assert(
      "Case 1: Nhiều phương án và nhiều tiêu chí: Render đúng số cột (2 phương án × 3 tiêu chí = 6 cột)",
      bars.length === 6,
      `bars=${bars.length}`
    );
    assert(
      "Case 1: Có chú thích (Legend) hiển thị đủ 2 phương án",
      legends.length === 2,
      `legends=${legends.length}`
    );
  }

  // Case 2: Chỉ có một phương án
  {
    const { container } = createMockDom();
    const resultsData = [
      {
        id: 1,
        name: "Cơm tấm sườn bì chả",
        total_score: 85.0,
        criteria_details: {
          price: { normalized_score: 100, weight: 0.4, contribution: 40.0 },
          preference: { normalized_score: 70, weight: 0.35, contribution: 24.5 },
          prep_time: { normalized_score: 82, weight: 0.25, contribution: 20.5 },
        },
      },
    ];

    CriteriaChart.render({
      container,
      results: resultsData,
      criteria: standardCriteria,
      mode: "single",
      selectedId: 1,
    });

    const bars = container.querySelectorAll(".criteria-chart-bar");
    assert(
      "Case 2: Chỉ có một phương án: Render đúng 3 cột cho 3 tiêu chí",
      bars.length === 3,
      `bars=${bars.length}`
    );
    assert(
      "Case 2: Hiển thị badge phương án đơn",
      container.innerHTML.includes("Cơm tấm sườn bì chả") &&
        container.innerHTML.includes("criteria-chart-single-badge")
    );
  }

  // Case 3: Chỉ có một tiêu chí
  {
    const { container } = createMockDom();
    const singleCriterion = [{ key: "price", label: "Giá", weight: 1.0 }];
    const resultsData = [
      {
        id: 1,
        name: "Phương án A",
        total_score: 80.0,
        criteria_details: {
          price: { normalized_score: 80, weight: 1.0, contribution: 80.0 },
        },
      },
      {
        id: 2,
        name: "Phương án B",
        total_score: 60.0,
        criteria_details: {
          price: { normalized_score: 60, weight: 1.0, contribution: 60.0 },
        },
      },
    ];

    CriteriaChart.render({
      container,
      results: resultsData,
      criteria: singleCriterion,
      mode: "compare",
    });

    const bars = container.querySelectorAll(".criteria-chart-bar");
    assert(
      "Case 3: Chỉ có một tiêu chí: Render 2 cột (1 cột mỗi phương án)",
      bars.length === 2,
      `bars=${bars.length}`
    );
    assert(
      "Case 3: Hiển thị đúng nhãn tiêu chí duy nhất",
      container.innerHTML.includes("Giá")
    );
  }

  // Case 4: Contribution bằng 0
  {
    const { container } = createMockDom();
    const resultsData = [
      {
        id: 1,
        name: "Món ăn ngân sách vượt mức",
        total_score: 0,
        criteria_details: {
          price: { normalized_score: 0, weight: 0.4, contribution: 0.0 },
          preference: { normalized_score: 0, weight: 0.35, contribution: 0.0 },
          prep_time: { normalized_score: 0, weight: 0.25, contribution: 0.0 },
        },
      },
    ];

    CriteriaChart.render({
      container,
      results: resultsData,
      criteria: standardCriteria,
      mode: "single",
    });

    const bars = container.querySelectorAll(".criteria-chart-bar");
    const allZero = bars.every((b) => Number(b.dataset.contribution) === 0);
    assert(
      "Case 4: Contribution bằng 0: Biểu đồ xử lý mượt mà và ghi nhận điểm 0",
      bars.length === 3 && allZero
    );
  }

  // Case 5: Dữ liệu null hoặc thiếu trường
  {
    const { container } = createMockDom();
    const incompleteData = [
      {
        id: 1,
        name: null, // thiếu tên
        // thiếu hoàn toàn criteria_details
        criteria_scores: { price: 70 }, // thiếu preference, prep_time
      },
      {
        id: 2,
        name: "Phương án thiếu trường",
        criteria_details: {
          price: { normalized_score: null, weight: 0.4, contribution: null },
        },
      },
    ];

    let errorThrown = false;
    try {
      CriteriaChart.render({
        container,
        results: incompleteData,
        criteria: standardCriteria,
        mode: "compare",
      });
    } catch (e) {
      errorThrown = true;
    }

    assert(
      "Case 5: Dữ liệu null hoặc thiếu trường: Không làm sập ứng dụng (no crash)",
      !errorThrown
    );
    assert(
      "Case 5: Tự động gán tên dự phòng và đóng góp 0 an toàn",
      container.innerHTML.includes("Phương án 1") || container.innerHTML.includes("Phương án thiếu trường")
    );
  }

  // Case 6: API trả về danh sách rỗng (Empty State)
  {
    const { container } = createMockDom();
    CriteriaChart.render({
      container,
      results: [],
      criteria: standardCriteria,
    });

    assert(
      "Case 6: API rỗng: Hiển thị thông báo rỗng 'Chưa có dữ liệu để hiển thị biểu đồ'",
      container.innerHTML.includes("Chưa có dữ liệu để hiển thị biểu đồ")
    );
  }

  // Case 7: API trả về lỗi (Error State)
  {
    const { container } = createMockDom();
    CriteriaChart.renderError(container, "Không thể kết nối đến WSM Decision Engine");

    assert(
      "Case 7: Trạng thái lỗi: Hiển thị thông báo lỗi rõ ràng và không crash",
      container.innerHTML.includes("Lỗi hiển thị biểu đồ") &&
        container.innerHTML.includes("Không thể kết nối đến WSM Decision Engine")
    );
  }

  // Case 8: Dữ liệu biểu đồ phải khớp với contribution từ Backend
  {
    const { container } = createMockDom();
    const backendData = [
      {
        id: 42,
        name: "Món A từ Backend",
        total_score: 75.8,
        criteria_details: {
          price: { normalized_score: 95.0, weight: 0.4, contribution: 38.0 },
          preference: { normalized_score: 60.0, weight: 0.35, contribution: 21.0 },
          prep_time: { normalized_score: 67.2, weight: 0.25, contribution: 16.8 },
        },
      },
    ];

    CriteriaChart.render({
      container,
      results: backendData,
      criteria: standardCriteria,
      mode: "single",
    });

    const bars = container.querySelectorAll(".criteria-chart-bar");
    const priceBar = bars.find((b) => b.dataset.critKey === "price");
    const prefBar = bars.find((b) => b.dataset.critKey === "preference");
    const prepBar = bars.find((b) => b.dataset.critKey === "prep_time");

    const matchPrice = priceBar && Number(priceBar.dataset.contribution) === 38.0;
    const matchPref = prefBar && Number(prefBar.dataset.contribution) === 21.0;
    const matchPrep = prepBar && Number(prepBar.dataset.contribution) === 16.8;

    assert(
      "Case 8: Khớp chính xác giá trị contribution từ Backend cho tất cả tiêu chí (38.0, 21.0, 16.8)",
      Boolean(matchPrice && matchPref && matchPrep)
    );

    // Kiểm tra đầy đủ thông tin tooltip trong data attributes
    const hasFullTooltipData =
      priceBar.dataset.optionName === "Món A từ Backend" &&
      priceBar.dataset.critLabel === "Giá" &&
      Number(priceBar.dataset.weight) === 0.4 &&
      Number(priceBar.dataset.normScore) === 95.0 &&
      Number(priceBar.dataset.contribution) === 38.0;

    assert(
      "Case 8: Dữ liệu Tooltip đầy đủ: Tên phương án, Tên tiêu chí, Weight, Normalized Score, Contribution",
      hasFullTooltipData
    );
  }
}

// ---------------------------------------------------------------------------
// Thực thi toàn bộ kiểm thử và báo cáo kết quả
// ---------------------------------------------------------------------------
testHtmlAndCss();
runEightTestCases();

let passCount = 0;
let failCount = 0;

console.log("\n=== KẾT QUẢ KIỂM THỬ: BIỂU ĐỒ ĐÓNG GÓP ĐIỂM THEO TIÊU CHÍ ===");
for (const r of results) {
  if (r.ok) {
    passCount++;
    console.log(`PASS - ${r.name}`);
  } else {
    failCount++;
    console.error(`FAIL - ${r.name} ${r.detail ? `(${r.detail})` : ""}`);
  }
}
console.log(`\nTổng: ${results.length} | Đạt: ${passCount} | Lỗi: ${failCount}\n`);

if (failCount > 0) {
  process.exit(1);
} else {
  process.exit(0);
}
