# GEO MVP - User Story Flow

## Overview

The goal of the MVP is to measure a company's visibility across Generative AI models.

A user submits a company website URL. The platform analyzes the website, generates a structured company profile (KYC), creates prompts from that profile, executes those prompts across multiple AI models, and calculates a primitive GEO score based on whether the company appears in the generated responses.

---

# User Flow

```text
User
    │
    ▼
Enter Company Website URL
    │
    ▼
Create Analysis Job
    │
    ▼
Website Discovery
    │
    ▼
Generate KYC JSON
    │
    ▼
Generate XX Prompts
    │
    ▼
Execute Prompts on YY AI Models
    │
    ▼
Collect Responses
    │
    ▼
Detect Company Footprint
    │
    ▼
Calculate GEO Score
    │
    ▼
Display Results
```

---

# Step 1 — Submit Website

The user enters a company website URL from the landing page.

Example:

```
https://example-company.com
```

The backend validates the URL and creates a new GEO analysis job.

---

# Step 2 — Website Discovery

The system crawls and analyzes the submitted website.

The purpose of this step is to collect publicly available information about the company that will later be used for prompt generation.

Potential sources include:

- Homepage
- About page
- Product pages
- Blog
- Documentation
- Contact page
- Metadata
- Structured data (Schema.org)

---

# Step 3 — Generate KYC JSON

The discovered information is transformed into a structured company profile (KYC JSON).

Example fields:

- Company name
- Description
- Industry
- Products
- Services
- Target audience
- Competitors
- Locations
- Technologies
- Keywords
- Entities
- Brand attributes

Example:

```json
{
  "company": "...",
  "industry": "...",
  "products": [],
  "services": [],
  "keywords": [],
  "locations": []
}
```

This JSON becomes the single source of truth for all downstream processing.

---

# Step 4 — Prompt Generation

Using the generated KYC JSON, the system automatically creates **XX prompts**.

The prompts should evaluate the company's visibility from different perspectives.

Examples:

- recommendation
- comparison
- alternatives
- best providers
- market leaders
- industry expertise
- product discovery

The prompts are generated dynamically based on the company's profile.

---

# Step 5 — Execute on Multiple AI Models

Each generated prompt is executed against **YY different Generative AI models**.

Example:

```
Prompt 1
    → Model A
    → Model B
    → Model C

Prompt 2
    → Model A
    → Model B
    → Model C

...
```

Every response is stored together with:

- prompt
- model
- timestamp
- raw response

---

# Step 6 — Footprint Detection

Each response is analyzed.

The MVP only answers a simple question:

> Does the generated response contain the target company?

Result:

```
Yes
```

or

```
No
```

This creates a binary footprint value.

```
Yes → 1

No → 0
```

---

# Step 7 — Primitive GEO Score

The first version of GEO Score is intentionally simple.

Formula:

```
GEO Score =
Footprint Count
------------------------
Total Responses
```

or

```
Footprint / All Responses
```

Example:

```
30 prompts

5 models

150 responses

Company appears in 63 responses

GEO Score = 63 / 150 = 42%
```

---

# Step 8 — Results

The user receives:

- Generated KYC JSON
- Generated prompts
- AI responses
- Footprint detection results
- Primitive GEO Score

---

# Future Improvements

The MVP focuses only on company presence.

Future versions may include:

- Entity recognition
- Citation detection
- Ranking position
- Brand sentiment
- Competitor comparison
- Weighted GEO scoring
- Visibility by model
- Visibility by prompt category
- Historical GEO trends
- Weekly GEO reports
- Actionable optimization recommendations