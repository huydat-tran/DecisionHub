# DecisionHub Design System
**Theme:** Green · **Style:** Modern SaaS Dashboard  
**Stack:** HTML, CSS, JavaScript, Bootstrap 5.0.2, Roboto

## Quick start
1. Extract this folder.
2. Open it with VS Code.
3. Run a local server from this folder (VS Code Live Server is fine).
4. Open `demo/index.html`.
5. Each member should copy the shared CSS imports and use the documented tokens/components.

## Folder structure
```text
decisionhub-design-system/
├── docs/
│   └── UI-GUIDELINES.md
├── assets/
│   ├── css/
│   │   ├── variables.css
│   │   ├── common.css
│   │   └── components.css
│   └── js/
│       └── app.js
├── components/
│   ├── navbar.html
│   └── sidebar.html
└── demo/
    └── index.html
```

## Required CSS imports
Every page should load Bootstrap first, then shared tokens, common rules, and component rules:
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="../../assets/css/variables.css">
<link rel="stylesheet" href="../../assets/css/common.css">
<link rel="stylesheet" href="../../assets/css/components.css">
```
Adjust relative paths according to the page's location. In `demo/index.html`, paths are `../assets/...`.

## Team rule
Do not copy or redefine global colors, typography, spacing, shadows, button styles, or card styles inside module CSS. Use the shared CSS variables and component classes. Module-specific CSS must be namespaced, e.g. `.food-page .food-result-card`.

## Notes
- The demo is a static UI shell; connect it to real FastAPI endpoints later.
- The navbar/sidebar snippets are reusable HTML fragments. With plain HTML, either copy them into pages initially or load them using `fetch()` from a local server.
- Do not use `file://` to test `fetch()` component loading; use Live Server or another local HTTP server.
