# Yankı — Frontend Brand Kit v2

*Audience: the frontend junior (there is no designer on call). This is the design
system: copy these tokens into `frontend/tailwind.config.ts` and build the five
components against them. When in doubt, prefer boring and consistent over clever.*

*v2 supersedes the indigo-based v1. The visual identity is now the "echo"
system: deep petrol ink + echo teal, Sora + IBM Plex Mono. Full rationale and
brand rules: `Brand Guidelines.dc.html`. Logo assets: `brand/logo/`, app icons:
`brand/icons/`.*

---

## 1. Design principles (unchanged)

1. **Show your work.** Every score links to the raw answers behind it;
   `matched_snippet` is shown in the MVP `ResultsTable`.
2. **Calm, confident, technical.** Restrained color, generous whitespace, one accent.
3. **Tokens, not hexes.** Always the Tailwind token, never a raw hex in a component.

---

## 2. Color palette

| Token (class) | Role | Hex | RGB |
|---|---|---|---|
| `primary` | Brand accent: buttons, links, active step | `#0E7569` | 14 117 105 |
| `primary-hover` | Button hover, link hover | `#0A5B51` | 10 91 81 |
| `primary-soft` | Selected rows, soft badges, hero pill | `#E2F3EF` | 226 243 239 |
| `primary-strong` (text on `primary-soft`) | Accessible teal text on the soft fill | `#0A5B51` | 10 91 81 |
| `signal` | Bright accent — **dark surfaces only** (charts, mark) | `#3BD1B5` | 59 209 181 |
| `ink` | Dark surfaces: KYC code block, footer, marketing dark sections | `#0B1D26` | 11 29 38 |
| `surface` | Card / panel background | `#FFFFFF` | 255 255 255 |
| `surface-muted` | Page + inset backgrounds | `#F5F8F8` | 245 248 248 |
| `surface-border` | Hairlines, dividers, card outlines (decorative only) | `#DCE6E9` | 220 230 233 |
| `surface-foreground` | Primary text | `#0C1E28` | 12 30 40 |
| `surface-subtle` | Secondary text, labels; form-control borders (3:1 vs white) | `#4E6B78` | 78 107 120 |
| `success` / `success-soft` | Footprint = yes, score ≥ 60% | `#177E4D` / `#DDF3E4` | 23 126 77 / 221 243 228 |
| `success-strong` (text on `-soft`) | "Yes" badge text, done check | `#116038` | 17 96 56 |
| `warning` / `warning-soft` | Score 30–59% | `#B45309` / `#FCEFD8` | 180 83 9 / 252 239 216 |
| `warning-strong` (text on `-soft`) | Warning badge text | `#8A4B08` | 138 75 8 |
| `danger` / `danger-soft` | Footprint = no, failed job, score 0–29% | `#C4403A` / `#FBE5E3` | 196 64 58 / 251 229 227 |
| `danger-strong` (text on `-soft`) | "No" badge text, failure heading | `#9E332E` | 158 51 46 |

Button text on `bg-primary` is `text-white`.

**Rules that carry over from v1, re-verified for the new hues:**

- Base status hues fail 4.5:1 on their own `-soft` fills — any **text or glyph on a
  `-soft` background uses the `-strong` shade**. Base hues are for solid fills,
  borders, and the gauge arc.
- `signal` `#3BD1B5` fails contrast on white — never use it on light backgrounds.
- **GEO score bands** (drives `ScoreGauge`): 0–29% → `danger`, 30–59% → `warning`
  (v1 used `primary` here; v2 makes the mid band semantic), 60–100% → `success`.
  Never color alone — always the numeric percentage and a label.
- Gradients are marketing-only; the product UI is flat.

---

## 3. Typography

Two webfonts (Google Fonts), system fallback:

```
font-sans: 'Sora', ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif
font-mono: 'IBM Plex Mono', ui-monospace, "SF Mono", Menlo, Consolas, monospace
```

Load Sora 400/500/600 (+300 for display on dark) and Plex Mono 400/500 with
`display=swap`. Mono is the "evidence" voice: KYC JSON, matched snippets, scores,
metadata, analysis ids.

| Step | Tailwind class | Size / line-height | Use |
|---|---|---|---|
| Display | `text-5xl font-semibold tracking-tight` | 48 / 1.15 | Landing headline |
| H1 | `text-3xl font-semibold tracking-tight` | 30 / 1.2 | Page titles |
| H2 | `text-xl font-semibold` | 20 / 1.4 | Section headers |
| Body | `text-base` | 16 / 1.5 | Default |
| Small | `text-sm` | 14 / 1.45 | Table cells, captions |
| Micro | `text-xs font-medium uppercase tracking-wider` | 12 / 1.35 | Labels, badges, step labels |
| Code | `text-sm font-mono` | 14 / 1.5 | KYC JSON, snippets |

---

## 4. Spacing, radius, shadow (unchanged except radius)

- **Spacing:** Tailwind default 4px base; reach for `2 3 4 6 8 12`. Gutter `px-4`
  mobile / `px-8` desktop; content `max-w-4xl mx-auto`.
- **Radius:** `rounded-xl` (12px) cards, `rounded-lg` (8px) inputs/insets,
  `rounded-md` (6px) buttons, `rounded-full` badges + gauge track.
- **Shadow:** `shadow-sm` (0 1px 2px rgba(11,29,38,0.06)) on raised cards;
  borders-only on dark surfaces.
- **Rhythm:** `space-y-8` between sections, `space-y-4` within a card.

## 5. Component specs

Unchanged from v1 (`Button`, `UrlForm`, `StepProgress`, `ScoreGauge`,
`ResultsTable`, failure state) with these token substitutions:

- `StepProgress` done check: `success-soft` circle + `success-strong` glyph;
  active step: solid `primary` circle, white number, soft pulse
  (`@keyframes` ping on box-shadow, disabled under `prefers-reduced-motion`).
- `ScoreGauge` arc: score-band color (§2); center number `text-4xl font-bold`;
  caption in `surface-subtle`.
- `ResultsTable` badges: "✓ Yes" on `success-soft`/`success-strong`,
  "✕ No" on `danger-soft`/`danger-strong`; zebra rows `#F9FBFB`.
- KYC JSON block: `bg-ink` with `#C7DBE0` mono text (7.9:1).

Reference renderings of all four screens: `Product UI.dc.html`.

## 6. Voice & tone, accessibility

Unchanged — see v1 §6–7 and `Brand Guidelines.dc.html` §06. Key re-verified
contrast pairs: `primary` on white 5.0:1; `surface-subtle` on white 5.5:1;
`-strong` shades on their `-soft` fills all ≥ 4.5:1.
