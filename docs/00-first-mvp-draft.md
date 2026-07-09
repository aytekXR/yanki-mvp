**Yanki MVP \- draft**

People ask ChatGPT, Gemini and Perplexity what to buy and which brand to trust, and brands see none of it. We are building the rank tracker for AI answers. Enter your brand, approve a list of the questions your buyers actually ask, and watch every week how often the engines mention you, where you sit in their shortlists, how they talk about you, and who they cite. Self serve, first result in about 10 minutes, plans from free to $129/mo. English and Turkish at launch, Arabic later.

**Why now**

Semrush already proved people pay for this. Their AI Visibility Toolkit is $99/mo for one domain and 25 prompts, bundled into Semrush One from $199. Good news for us: the category has a price anchor and a real buyer.

The gaps are where we live. Four things come up again and again in reviews and agency conversations:

**1\. Expensive at scale.** Extra domains are $99 each, extra prompts $60 per pack of 50, extra seats cost too. An agency with 20 clients does the math and walks away.

**2\. Black box numbers.** Users literally call the data probabilistic guesswork. The score is opaque and the raw answers are hard to reach.

**3\. Small brands get junk.** Tools built on big prompt databases produce thin, erratic reports when the brand is small.

**4\. English only.** Turkish has zero tooling. Not weak tooling, zero.

So we build the opposite. Flat pricing agencies can actually scale on. A public methodology page that shows everything: the prompt list, sample counts, the score formula, every raw answer one click away. Prompt panels generated from the customer's own site so small brands get real signal. And Turkish as a first class language.

**Who it's for**

Three people, in this order:

- Agency owner with 15-30 clients. Needs client ready numbers without per domain fees. He is the multiplier, if it works for him across ten clients it works.

- In-house SEO lead whose VP keeps asking how the company looks in ChatGPT. Needs one score, a trend, and screenshots for a deck.

- Founder who just found out an AI recommends his competitor. Wants a free check first, a cheap plan second, in his own language.

All three buy the same way: self serve. No sales calls, no demos.

**How it works**

Sign up, enter brand \+ site \+ up to 5 competitors. We generate 30-60 prompts from the site and category (brand questions, category best-of, comparisons, use cases). User edits and approves. We run the panel across ChatGPT, Gemini (with search grounding), Perplexity and Claude. First snapshot lands in about ten minutes. After that: priority prompts weekly, full panel monthly, and you recieve a weekly digest email plus an alert when something actually moves.

Everything else exists to make this loop fast and trustworthy.

**What we're building**

**1\. Onboarding wizard.** Brand, site, category, competitors, language. First run kicks off immediately with live progress.

**2\. Prompt engine.** Our version of keyword research. Suggestions come from the customer's own content so even a small brand gets a meaningful panel. Turkish prompts written the way Turkish users actually ask, not translated. Panels are versioned, changes get annotated on charts.

**3\. Tracking pipeline.** 4 engines, 2 samples per prompt, search/grounding always on. Raw answers stored with engine, model, citations, timestamps. Identical prompt+engine pairs cached across accounts within 24h, big cost lever. Every account has a cost budget with auto pause.

**4\. Scores people can defend.** AI Visibility Score 0-100 with the formula published: mention (1/0) x position weight (first 1.0, second-third 0.7, later 0.4) x sentiment (positive 1.0, neutral 0.9, negative 0.5), averaged, x100. Plus share of voice, mention rate per engine, average position, sentiment, and citations split into own pages vs third party. That third party citation list is quietly the best screen in the product, it tells you exactly which reddit threads and review sites the engines trust in your category.

**5\. Answers explorer.** Every metric links to the the raw answers behind it. No dead ends. This is the trust feature.

**6\. Digest \+ alerts.** Weekly mail, three triggers: score moves 10+ points, a competitor enters a priority answer, you disappear from one. Max one alert mail a day.

**7\. Billing.** Free / $49 / $129 via Stripe from day one of public launch. Hard limits, upgrade offered right when someone hits a cap.

**8\. The free checker** (below). Ships before the app.

**What we're NOT building (v1)**

- Google AI Overviews tracking. Needs SERP scraping or a paid SERP API. Gemini with grounding stands in for Google for now. This is our biggest gap vs Semrush, we say it out loud on the comparison page and close it around day 60-90. Hiding it would cost us the transparency story.

- Content generation. Everyone already has a writing tool.

- We dont ship an AI recommendation engine. Generic advice is the most mocked feature in this category. Specific findings instead: this prompt, this engine, this competitor, these cited sources.

- Attribution / analytics integrations. Not needed to prove people will pay.

- White label, API, SSO, mobile, more engines. Later, when someone asks and pays.

**The free checker**

Public page, no signup. Type a brand and category, we run 12 fixed prompts across the 4 engines live. You get a score, an engine by engine presence map, the compeitors that showed up, and at least one full raw answer, not a teaser. Full report costs an email address. Results cached 24h per brand, rate limited, English and Turkish.

This ships weeks before the app. Demand test, lead magnet and launch asset in one. Semrush has a checker too, ours has to be more generous and it has to exist in Turkish, theirs doesn't.

**Pricing**

- Free: 1 project, 10 prompts, 2 competitors, monthly scan

- Starter $49/mo: 1 project, 50 prompts, 5 competitors. Top 15 prompts weekly, full panel monthly

- Pro $129/mo: 3 projects (kept fully seperate), 150 prompts total, CSV export. Top 50 weekly, full panel monthly

- Agency \~$299/mo: later, 10 projects \+ white label reports. Day 60-90 decision.

Anchor for every comparison page: $49 buys 50 prompts here, Semrush charges $99 for 25\.

Now the uncomfortable part. Search enabled API calls are not cheap. Working estimate is $0.015-0.035 per probe (one prompt, one engine, one sample, plus the analysis pass). At 2 samples with weekly priorities \+ monthly full scan, Starter costs us roughly $13-31/mo against $49 and Pro roughly $42-98 against $129. Workable but thin at the top of the range. Three protections: the cross account cache, a cheap model for the analysis pass, hard prompt caps. Week 1 is partly a finance exercise, run real volume and read real invoices (need to verify actual per call pricing before anything goes public). If costs land high, Starter becomes $59 and Pro $149 before launch, not after. No lifetime deals ever, annual \= 2 months free.

**Keeping the numbers honest**

LLM answers wobble. Same prompt, different day, different answer. Pretending otherwise is how this category earned its guesswork reputation. So: 2 samples per prompt, frequencies not single observations, trends smoothed over 4 week windows, and an annotation on the chart whenever an engine ships a model update. The methodology page is public and it's a feature, not a disclaimer.

Turkish gets real treatment, not translation. Native prompt generation, brand matching that handles Turkish suffixes, and the extraction model tested on a labelled Turkish set before launch. If the Turkish numbers are wrong the whole differentiation story dies on day one, so this is not the corner we cut.

**Build plan**

3 engineers \+ me, 8 weeks to public launch. Python workers, Postgres, Next.js, Stripe. Nothing exotic.

Week 1: Launch 1

Weeks 1-2: pipeline core, cost validation, ToS review for all 4 APIs, checker skeleton.

Weeks 3-4: checker live in EN \+ TR. Recruit 5 agencies as design partners on free Pro.

Week 5: Launch 2

Weeks 5-6: app beta with partners, billing in test, draft the Turkish benchmark report.

Weeks 7: public launch 3\.

Scope frozen until day 60\. New ideas go to the backlog, not the sprint. With a team this size thats the difference between shipping in 8 weeks and never.

**Launch**

1\. Checker first, weeks before the app. Every run is a demand signal and a lead.

2\. Launch loud: Product Hunt, LinkedIn, SEO/GEO communities. The pitch writes itself, the numbers Semrush sells at half the price with the methodology shown.

3\. Own Turkish: publish the AI visibility benchmark of the top 50 Turkish ecommerce and SaaS brands. Nobody has this data. PR \+ SEO \+ proof of product in one document.

4\. Honest comparison pages: vs Semrush AI Toolkit, vs Otterly, vs Peec, including our own AIO gap. Tools that get cited win the AI answers about tools, so we practice what we sell.

5\. The 5 design partner agencies pressure test multi client use and will pull the agency plan out of us when its time.

**First 90 days**

- 3000 checker runs, 600 signups, 40 paying, $2.5-4k MRR. Ranges not promises, recalibrate after 2 weeks of real data.

- Activation: 60% of signups see their first snapshot, median under 10 minutes.

- Month 2 logo churn under 8%. This is the number I will actually stare at. Monitoring tools die of curiosity churn.

- Run reliability 95%+, API cost per paying customer under 35% of plan price.

**Risks**

- API costs move against us. Week 1 validation, aggressive caching, right to reprice before launch.

- Semrush cuts price or bundles harder. Price is only one of three wedges, transparency and Turkish do not ship from a feature sprint in Boston.

- Curiosity churn. If month 2 churn is ugly we fix retention before building anything else.

- Extraction errors in Turkish. Labelled test set, precision bar before launch, weekly human spot checks in beta.

- Checker abuse. Caching, rate limits, email gate, fixed prompt set, daily cost check.

**Day 90 decisions**

- Agencies dominate paying accounts: build the agency plan next (workspaces, white label PDF).

- Turkey delivers 20%+ of signups organically: ship Arabic, double the local content.

- Regulated / enterprise brands come inbound asking about accuracy and audit trails: add a compliance grade tier at $500+/mo, the pipeline already supports it.

- Free to paid under 2%: stop building, fix packaging and pricing first.

**Bottom line**

We win on three things: showing our work, pricing agencies can scale on, and a language nobody else speaks. Ship the checker, read the numbers, decide at day 90\.