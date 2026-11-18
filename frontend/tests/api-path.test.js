// Kiem thu nhanh cho js/api.js (khong can browser): kiem tra duong dan tuong doi
// va vong doi phien dang nhap.
//
// Chay: node frontend/tests/api-path.test.js

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const apiSource = fs.readFileSync(
  path.join(__dirname, "..", "js", "api.js"),
  "utf8",
);

// Thay the phan khoi tao axios bang stub de chay duoc trong Node.
const stub = `
const axios = { create: () => ({ interceptors: { request: { use: () => {} }, response: { use: () => {} } }, request: () => Promise.resolve({ data: {} }) }) };
const CONFIG = { API_BASE_URL: "http://127.0.0.1:8000" };
const localStorage = (() => { let store = {}; return { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; } }; })();
globalThis.localStorage = localStorage;
const window = { location: { pathname: __PATH__, search: __SEARCH__ }, atob: (s) => Buffer.from(s, "base64").toString("binary") };
globalThis.window = window;
`;

const results = [];
function check(name, actual, expected) {
  const ok = actual === expected;
  results.push({ ok, name, actual, expected });
}

// Chay lai api.js voi cac duong dan khac nhau.
function loadApi(pathname, search) {
  const context = vm.createContext({
    console,
    Buffer,
    setTimeout,
    URLSearchParams,
    __PATH__: pathname,
    __SEARCH__: search || "",
  });
  vm.runInContext(stub + apiSource + "\nglobalThis.__api = api;\nglobalThis.__session = session;", context);
  return context;
}

// Trang trong frontend/pages/
let ctx = loadApi("/frontend/pages/profile.html");
check(
  "pages/profile.html -> pages/signup.html",
  ctx.appUrl("pages/signup.html"),
  "signup.html",
);
check(
  "pages/profile.html -> demo-design-system.html",
  ctx.appUrl("demo-design-system.html"),
  "../demo-design-system.html",
);

// Trang o thu muc goc frontend/
ctx = loadApi("/frontend/demo-design-system.html");
check(
  "root -> pages/signup.html",
  ctx.appUrl("pages/signup.html"),
  "pages/signup.html",
);
check(
  "root -> demo-design-system.html",
  ctx.appUrl("demo-design-system.html"),
  "demo-design-system.html",
);

// frontend phuc vu o thu muc con (vi du /web/frontend/)
ctx = loadApi("/web/frontend/pages/food.html");
check(
  "nested frontend pages/food.html -> pages/signup.html",
  ctx.appUrl("pages/signup.html"),
  "signup.html",
);
check(
  "nested frontend pages/food.html -> demo-design-system.html",
  ctx.appUrl("demo-design-system.html"),
  "../demo-design-system.html",
);

// Token het han -> session.isLoggedIn() false
ctx = loadApi("/frontend/pages/profile.html");
const expiredJwt =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." +
  Buffer.from(JSON.stringify({ sub: "1", exp: 1000 })).toString("base64url") +
  ".sig";
ctx.localStorage.setItem("token", expiredJwt);
check("token het han -> isLoggedIn false", ctx.__session.isLoggedIn(), false);
check("token het han -> isExpired true", ctx.__session.isExpired(expiredJwt), true);

// Token con han -> isLoggedIn true
const validJwt =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." +
  Buffer.from(
    JSON.stringify({ sub: "1", exp: Math.floor(Date.now() / 1000) + 3600 }),
  ).toString("base64url") +
  ".sig";
ctx.localStorage.setItem("token", validJwt);
check("token con han -> isLoggedIn true", ctx.__session.isLoggedIn(), true);

// clear() xoa token
ctx.__session.clear();
check("clear() xoa token", ctx.localStorage.getItem("token"), null);
check("clear() -> isLoggedIn false", ctx.__session.isLoggedIn(), false);

const failed = results.filter((r) => !r.ok);
results.forEach((r) => {
  console.log(
    (r.ok ? "PASS" : "FAIL") +
      " - " +
      r.name +
      (r.ok ? "" : ` (expected: ${r.expected}, actual: ${r.actual})`),
  );
});
process.exit(failed.length ? 1 : 0);
