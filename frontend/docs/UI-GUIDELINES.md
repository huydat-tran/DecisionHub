# DecisionHub – UI Guidelines

## 1. Product feel
DecisionHub should feel calm, helpful, trustworthy, and intelligent. Use a clean SaaS dashboard rather than a flashy AI landing page.

**Design principles**
- Green is the primary action color, not a background color for every section.
- Keep most surfaces white or very light neutral.
- Use consistent spacing and alignment.
- Prefer clear labels and readable hierarchy over decoration.
- Use color to communicate state (success, warning, danger), not as decoration.

## 2. Brand tokens
| Token | Value | Usage |
|---|---|---|
| Primary | `#16845B` | Main actions, active navigation |
| Primary hover | `#116B49` | Hover/focus for primary actions |
| Primary soft | `#E8F5EF` | Soft highlights, selected backgrounds |
| App background | `#F5F8F6` | Page background |
| Surface | `#FFFFFF` | Cards, panels, navbar |
| Text primary | `#172B23` | Headings and body text |
| Text muted | `#66776F` | Hints, secondary text |
| Border | `#E3EBE6` | Card/input borders |
| Success | `#16845B` | Successful states |
| Warning | `#B7791F` | Warnings |
| Danger | `#C2413B` | Errors/destructive actions |
| Info | `#2876A8` | Informational states |

## 3. Typography
- Font: Roboto.
- Page title: 24–28px, weight 700.
- Section title: 18–20px, weight 600.
- Body: 14–16px, weight 400.
- Helper text: 12–13px.
- Use sentence case. Avoid all-caps labels except compact status tags.

## 4. Layout and spacing
- Desktop sidebar: 248px wide.
- Top navbar: 68px high.
- Main content max width: 1440px.
- Page padding: 28px desktop, 16px mobile.
- Use spacing increments of 4px: 4, 8, 12, 16, 20, 24, 32, 40.
- Card radius: 14px.
- Inputs/buttons radius: 9px.
- Use subtle shadows only for elevated surfaces.

## 5. Buttons
- `dh-btn dh-btn-primary`: primary action; one visually dominant action per section.
- `dh-btn dh-btn-secondary`: neutral secondary action.
- `dh-btn dh-btn-outline`: low-emphasis action.
- `dh-btn dh-btn-danger`: destructive action.
- Minimum height: 40px; compact variant: 34px.
- Include clear text labels. Do not rely on icons alone for important actions.

## 6. Inputs
- Use `.dh-label` for labels and `.dh-input` / `.dh-select` for controls.
- Always provide a visible label; placeholder is not a replacement.
- Use `.dh-help` for helper text and `.dh-error` for validation feedback.
- Keep input heights consistent (42px).

## 7. Cards
- Use `.dh-card` for standard content surfaces.
- Use `.dh-card-header` and `.dh-card-body` for consistent padding.
- Avoid nested cards unless there is a clear information hierarchy.

## 8. Navigation
- Navbar and sidebar are shared product chrome. Do not redesign them per module.
- Active sidebar item uses primary-soft background and primary text.
- Module-specific navigation belongs inside the page content, not in a second competing global sidebar.

## 9. Module CSS
Allowed:
```css
.food-page .food-result-card { ... }
.travel-page .destination-photo { ... }
```
Avoid:
```css
button { ... }
.card { ... }
body { ... }
:root { ... }
```
Do not redefine shared tokens in module stylesheets.

## 10. Responsive behavior
- At widths below 992px, sidebar becomes off-canvas/collapsible.
- At widths below 768px, page padding reduces to 16px.
- Tables should scroll horizontally rather than crush columns.
- Forms should stack into one column on mobile.

## 11. Accessibility and interaction
- Maintain readable contrast.
- Provide `:focus-visible` states.
- Buttons must have meaningful labels.
- Pair status colors with text, not color alone.
- Use `aria-label` for icon-only controls.
- Do not remove browser focus outlines without replacement.

## 12. Review checklist
Before merging a page, verify:
- Shared CSS files are imported in the correct order.
- The page uses the approved green palette and Roboto.
- Navbar/sidebar match the shared components.
- Buttons, inputs, and cards use shared classes.
- No global CSS selectors are redefined in module CSS.
- Layout works at desktop and mobile widths.
- No horizontal overflow at normal viewport sizes.
