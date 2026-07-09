# Yanki — MVP PRD

*Audience: PM / QA / founders + engineers. This document is the **scope
authority**: the in-scope flow below is the sole definition of done. If it isn't
here, it isn't in the MVP — it's in [roadmap.md](roadmap.md).*

See also: [architecture.md](architecture.md) (how it's built),
[test-suite.md](test-suite.md) (how "done" is verified).

---

## 1. Problem

People ask ChatGPT, Gemini, Perplexity, and Claude what to buy and which brand to
trust — and brands have no idea what those engines say about them. Semrush proved
people pay to track this, but their tooling is expensive at scale, a "black box"
about how the score is derived, thin for small brands, and English-only.

Yanki's wedge: **show your work** (published methodology, every raw answer one
click away), **price agencies can scale on**, and **Turkish as a first-class
language**. The MVP proves the core loop: *URL in → GEO score out in ~10 minutes,
with the raw answers behind it.*

---

## 2. Target users (in priority order)

1. **Agency owner** with 15–30 clients. Needs client-ready numbers without
   per-domain fees. The multiplier — if it works across ten clients, it works.
2. **In-house SEO lead** whose VP keeps asking "how do we look in ChatGPT?" Needs
   one score, a trend, and screenshots for a deck.
3. **Founder** who just learned an AI recommends a competitor. Wants a free check
   first, a cheap plan second, in their own language.

All three buy self-serve — no sales calls, no demos.

---

## 3. In-scope flow (the definition of done)

This is the entire MVP. Nothing more.

```
URL  →  discovery  →  KYC  →  prompts  →  multi-engine execution
     →  binary footprint  →  primitive GEO score  →  results
```

1. **Submit** a company URL from the landing page (anonymous — no login).
2. **Discovery**: crawl the homepage + a few links, extract main text.
3. **KYC**: turn that text into a structured company profile (JSON).
4. **Prompts**: generate N prompts from the KYC (recommendation, comparison,
   alternatives, best-of, etc.).
5. **Execution**: run every prompt across the panel engines (Claude + OpenAI real;
   Gemini + Perplexity stubbed).
6. **Footprint**: for each response, a binary yes/no — does the company appear?
   (real string matching on brand/domain/aliases).
7. **GEO score**: `footprints / total_responses`.
8. **Results**: show the KYC JSON, the generated prompts, every raw response with
   its footprint + matched snippet, and the GEO score.

---

## 4. Out of scope (explicitly NOT in the MVP)

These are real product features — just not now. Each maps to a phase in
[roadmap.md](roadmap.md). Listing them here stops scope creep.

- Auth, accounts, projects
- Billing / Stripe / plan limits
- Scheduling, recurring scans, weekly digests + alerts
- Sentiment analysis and position weighting (score stays binary)
- Google AI Overviews tracking
- Turkish language (native prompts + Turkish suffix matching)
- Cross-account cache (MVP caches within a job's own runs only, via `llm_cache`)
- Real Gemini + Perplexity engines (stubbed)
- 2-samples-per-prompt sampling
- Competitor comparison, share of voice, citations, Answers Explorer UI
- CSV export, historical trends

**Scope is frozen until day 60.** New ideas go to the backlog, not the sprint.

---

## 5. GEO score formula (MVP)

Intentionally primitive and fully transparent:

```
GEO Score = footprint_count / total_responses
```

Example: 10 prompts × 2 engines = 20 responses; the company appears in 9 →
`9 / 20 = 0.45 = 45%`.

The score is a **pure function** in `pipeline/scoring.py` (ADR-11), so it is
unit-tested and defensible. The weighted version (mention × position × sentiment)
is roadmap, not MVP.

---

## 6. Functional requirements

- **FR-1** `POST /api/v1/analyses` accepts a URL, validates it, creates a `queued`
  analysis, returns `{id}`.
- **FR-2** `GET /api/v1/analyses/{id}` returns status, progress (0–100), and — once
  `done` — the nested KYC, prompts, responses, and score.
- **FR-3** A background worker runs the 6 pipeline steps sequentially, persisting
  each step's output and advancing `status`/`progress`.
- **FR-4** Every provider call is logged as a `response` row with engine, model,
  raw text, footprint, matched snippet, and `cost_usd`.
- **FR-5** Footprint detection is real, deterministic string matching; the matched
  snippet is stored.
- **FR-6** The frontend has two routes: landing (submit) and
  `/analyses/{id}` (live progress → results / error).
- **FR-7** A failed job shows a clear error state; partial results remain queryable.
- **FR-8** Cost controls are enforced: `PROMPT_COUNT`, `PANEL_MODELS`,
  `MAX_RESPONSES_PER_JOB`, the `llm_cache` table, and `DRY_RUN` for zero-cost runs.

## 7. Non-functional requirements

- **NFR-1 Cost:** an MVP analysis stays within the configured caps; CI and tests
  cost **$0** (MockProvider / `DRY_RUN`). Week-1 invoice validation possible before
  going public. See `feasibility-report.md` (private; not in this repo).
- **NFR-2 Time-to-first-result:** target ~10 minutes for a real analysis.
- **NFR-3 Reliability:** a worker crash never loses or double-runs a job
  (`SKIP LOCKED` + stale-claim reaper); run reliability target 95%+.
- **NFR-4 Simplicity:** the whole stack is readable by a junior — sync Python, one
  Docker image for api/worker, Postgres-as-queue, no broker.
- **NFR-5 Security:** public repo; no secret ever committed; gitleaks in
  pre-commit + CI.
- **NFR-6 Contract safety:** the FE/BE contract cannot silently drift (OpenAPI is
  the single source; CI fails on drift).

---

## 8. Acceptance criteria (per pipeline step — for TDD / QA)

Each step has a testable "done" bar. See [test-suite.md](test-suite.md) for how
these become tests.

| Step | Acceptance criteria |
|---|---|
| **Submit** | A valid URL returns `202` + an `id`; an invalid URL returns `422`; the row exists with `status=queued`. |
| **Discovery** | Given a reachable site, extracted text is non-empty; an unreachable site fails the job with a clear `error` (not a crash). |
| **KYC** | Output validates against the KYC Pydantic model; required fields (company, industry, aliases) are populated for a real site. |
| **Prompts** | Exactly `PROMPT_COUNT` prompts are generated; each has non-empty `text` and a `category`. |
| **Execution** | Each prompt yields one `response` per panel engine; `llm_cache` is consulted before each call; `MAX_RESPONSES_PER_JOB` is never exceeded. |
| **Footprint** | For a response containing the brand/domain/alias, `footprint=true` and `matched_snippet` is set; otherwise `false`/null. Deterministic — same input, same output. |
| **Scoring** | `geo_score == footprints / total_responses`; `total_responses == 0` does not divide-by-zero. |
| **Results** | `GET` returns KYC + prompts + responses + score; the UI renders the `ScoreGauge`, `ResultsTable`, KYC, and prompts. |

**Definition of done for the MVP as a whole:** a user submits a real URL against a
live stack and, within a few minutes, sees a GEO score with every raw answer and
its footprint visible on the results screen. The Playwright happy-path (against
`DRY_RUN=1`) asserts a score renders.
