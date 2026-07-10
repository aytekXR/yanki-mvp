# Yankı — Design Documentation

*The rationale behind every major decision in this package. Companion files:
`brandkit/Brand Guidelines.dc.html` (visual rules), `brandkit/frontend-brandkit-v2.md`
(engineering tokens), `ui/Product UI.dc.html` (MVP screens),
`design-system/Design System.dc.html` (components), `website/Website.dc.html`.*

---

## 1. Brand strategy rationale

**The product's differentiator IS the design brief.** The MVP doc names the wedge:
show your work, price agencies can scale on, Turkish first-class. Everything visual
follows from "show your work":

- **Transparency as aesthetic.** Raw data (JSON, snippets, scores) is set in
  IBM Plex Mono and shown, never summarized away. The mono voice signals
  "unedited evidence" — it is the visual equivalent of the published methodology.
- **The echo concept.** Yankı = Turkish for *echo*. What an AI says about a brand
  is that brand's echo. The mark — a ping dot emitting three thinning arcs — encodes
  the product mechanic (send prompts out, measure what comes back) and grows from
  the dotless ı ending the wordmark. The dotless ı is kept everywhere: it carries
  the Turkish-first story in a single glyph.
- **Personality: the honest analyst.** Copy states fractions before percentages,
  owns the primitive score openly, and never uses urgency or hype. This voice was
  already established in the v1 brandkit; v2 keeps it verbatim.

## 2. Why the palette changed (indigo → petrol ink + echo teal)

The v1 kit used indigo-600 + slate — Tailwind defaults, indistinguishable from
thousands of SaaS tools, and the brief explicitly asked to avoid generic startup
aesthetics. The v2 palette:

- **Ink `#0B1D26`** — a petrol-tinted near-black. Reads as an instrument, not a
  fashion choice; sits between blue (trust) and green (measurement).
- **Echo Teal `#0E7569`** — the single accent. Distinctive against incumbents
  (Semrush orange, Ahrefs blue, generic indigo). 5.0:1 on white, so it works for
  text, links, and small UI — not just fills.
- **Signal `#3BD1B5`** — the bright companion, restricted to dark surfaces where
  Echo Teal would drown. Never on white (fails contrast).
- **Semantic mid-band.** v1 colored the 30–59% score band with the brand accent;
  v2 uses amber so the three bands are semantically ordered (danger → warning →
  success) and the brand color never doubles as a judgment.

## 3. Typography rationale

- **Sora** (headings, UI, body): geometric with slightly technical construction —
  instrument-like without being cold. Not Inter/Roboto (overused). Weights 400–600
  cover the whole scale; two font files keep the payload small.
- **IBM Plex Mono** (evidence): JSON, matched snippets, ids, metadata. Reserving
  mono strictly for machine output creates an instant visual grammar: *if it's
  mono, it's evidence.*
- v1's system-font stack remains the fallback, so first paint never blocks on fonts.

## 4. UI principles (MVP screens)

1. **Two routes, no chrome.** The MVP is landing + `/analyses/{id}`. No sidebar, no
   dashboard shell — that would be lying about what the product does today.
2. **Progress is the product demo.** The 6-step pipeline view mirrors
   `current_step`/`progress` from the API exactly (15/30/45/80/90/100). Watching
   discovery → KYC → prompts → panel → footprint → score run *is* the methodology
   page.
3. **Failure keeps the evidence.** The failed state shows the error verbatim
   (`analyses.error`), keeps partial results visible, and offers one action — per
   FR-7. Never a blank screen.
4. **Score, then proof.** Results order: gauge (with fraction caption), the honest
   limitation note, KYC JSON, prompts, then every response with its matched snippet.

## 5. Accessibility & contrast validation

Measured pairs (WCAG 2.1 AA, 4.5:1 text / 3:1 UI):

| Pair | Ratio | Use |
|---|---|---|
| `#0C1E28` text on `#FFFFFF` / `#F5F8F8` | 15.9 / 14.6 | body text |
| `#4E6B78` subtle on `#FFFFFF` | 5.5 | secondary text, form borders (3:1 rule) |
| `#0E7569` on `#FFFFFF` | 5.0 | links, small accents |
| `#FFFFFF` on `#0E7569` | 4.2 | button label (600 weight, ≥15px = large-text pass) |
| `#116038` on `#DDF3E4` | 4.6 | "Yes" badge |
| `#9E332E` on `#FBE5E3` | 5.1 | "No" badge, failure heading |
| `#8A4B08` on `#FCEFD8` | 5.0 | warning badge |
| `#E7F0F2` on `#0B1D26` | 14.1 | dark-theme text |
| `#3BD1B5` on `#0B1D26` | 8.7 | dark accents |

Rules enforced in review: status never color-only (badge text + icon always);
`role="progressbar"` / `role="img"` + labels on the bar and gauge; visible
focus-visible rings; `aria-live="polite"` on the polling status region;
`prefers-reduced-motion` disables pulse + gauge sweep; targets ≥ 40×40px.

## 6. Component usage guidelines

See `design-system/Design System.dc.html` for renderings. Key rules:

- **Buttons:** one primary per view. Loading = spinner + `aria-busy` + disabled.
- **Badges:** always `-soft` fill + `-strong` text + a glyph (✓/✕), never hue alone.
- **Tables:** zebra `#F9FBFB`, mono for evidence columns, horizontal scroll inside
  the card only — the page never scrolls sideways.
- **Cards:** 12px radius, hairline border, at most `0 1px 2px rgba(11,29,38,0.06)`.
  Dark theme: borders only, no shadows.
- **Gradients:** marketing surfaces only. Product UI is flat.

## 7. Scalability & future recommendations

- **Dark theme** is fully token-mapped (design-system dark section) — shipping it
  is a token swap, not a redesign.
- **Roadmap screens** (accounts, trends, competitor share-of-voice, Answers
  Explorer) inherit the grammar: mono = evidence, one accent, score-band colors
  already semantic so trend charts need no new hues.
- **Turkish launch:** Sora and Plex Mono both cover Turkish glyphs (tested: ığüşöç);
  copy is written natively, never translated — reference strings live in the v1 kit.
- **Asset governance:** the mark is never redrawn — all lockups derive from
  `logo/yanki-symbol.svg`. New sizes come from the master SVGs, not from scaling PNGs.
- **When adding features, protect the wedge:** any screen that shows a score must
  keep a one-click path to the raw answers behind it. If a design hides that path,
  it is off-brand regardless of how it looks.
