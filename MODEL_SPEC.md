# MODEL_SPEC.md — Birge Intelligence Layer

## Purpose

Birge uses an intelligence layer to convert fragmented buying wishes into structured demand pools.

The intelligence layer must be:

- honest
- explainable
- demo-reliable
- simple enough for a hackathon MVP

It has three components:

1. Intent parsing
2. Demand clustering
3. Rule-based group price forecast

## Component 1 — Intent parsing

### Type

LLM parsing with cached fallback.

### Input

The parser accepts either:

- a product URL
- free-text buying intent

Supported languages:

- Kazakh
- Russian
- English

Examples:

```txt
https://example.com/headphones-demo
Хочу беспроводные наушники до 15000 тенге
Маған үйге ауа ылғалдатқыш керек
I want a cheap portable projector
```

### Output

The parser returns a structured intent:

```ts
type ParsedIntent = {
  inputType: "url" | "text";
  sourceText: string;
  normalizedTitle: string;
  localizedTitle: string;
  language: "kk" | "ru" | "en" | "unknown";
  category: IntentCategory;
  specs: Record<string, string | number | boolean>;
  estimatedUnitPriceKzt: number | null;
  budgetMinKzt: number | null;
  budgetMaxKzt: number | null;
  confidence: number;
  parserMode: "live_llm" | "cache_fallback" | "rule_based_fallback";
  explanation: string;
};
```

### Categories

Initial allowed categories:

```ts
type IntentCategory =
  | "electronics"
  | "home"
  | "fashion"
  | "beauty"
  | "sports"
  | "kids"
  | "auto"
  | "books"
  | "other";
```

### Parser rules

- If URL parsing is not possible, infer only from URL text or cached examples.
- Do not rely on real scraping for demo success.
- Do not invent exact product specs if unavailable.
- Use confidence score honestly.
- If uncertain, category should be `"other"` and confidence should be low.
- Parser must never claim it bought, ordered, or reserved anything.

## Component 2 — Demand clustering

### Type

Embedding similarity plus deterministic business rules.

### Goal

Find whether a new intent belongs to an existing city-level demand pool.

### Pool matching rules

An intent can match a pool only if:

1. City matches.
2. Category matches.
3. Budget range overlaps.
4. Similarity is above threshold.
5. Pool status is open/forming.

### Similarity

Preferred implementation later:

- text embedding for `normalizedTitle + specs + category`
- stored vector in Supabase pgvector
- cosine similarity against pool centroid

Fallback implementation for MVP:

- deterministic keyword similarity
- category match
- budget overlap
- city match

### Thresholds

Default demo threshold:

```txt
cosine similarity >= 0.78
```

Fallback keyword threshold:

```txt
keyword similarity >= 0.45
```

These are demo thresholds, not validated production metrics.

## Pool object

```ts
type DemandPool = {
  id: string;
  city: string;
  category: IntentCategory;
  title: string;
  localizedTitle: string;
  status: "forming" | "ready" | "deal_formed" | "closed";
  currentIntentCount: number;
  moq: number;
  missingToMoq: number;
  estimatedRetailPriceKzt: number;
  estimatedGroupPriceKzt: number;
  estimatedSavingsPercent: number;
  savingsIntervalPercent: {
    min: number;
    max: number;
  };
  benchmarkSource: "demo_category_benchmark";
  isDemoData: boolean;
};
```

## Component 3 — Rule-based group price forecast

### Type

Rule-based heuristic.

This is not a trained demand prediction model.

### Category benchmark savings

Initial demo benchmarks:

```ts
const CATEGORY_SAVINGS_BENCHMARKS = {
  electronics: { min: 28, max: 36, default: 34 },
  home: { min: 30, max: 42, default: 38 },
  fashion: { min: 20, max: 35, default: 29 },
  beauty: { min: 18, max: 30, default: 24 },
  sports: { min: 22, max: 34, default: 28 },
  kids: { min: 20, max: 32, default: 26 },
  auto: { min: 15, max: 28, default: 21 },
  books: { min: 10, max: 22, default: 16 },
  other: { min: 12, max: 25, default: 18 }
};
```

### Pricing formula

```txt
estimatedGroupPriceKzt = estimatedRetailPriceKzt * (1 - defaultSavingsPercent / 100)
```

Round to nearest 100 KZT for demo readability.

### Landed cost estimate

Landed cost is a demo estimate:

```txt
landedCostKzt = productPriceKzt + cargoEstimateKzt + dutyEstimateKzt
```

Initial rule:

- `cargoEstimateKzt`: category-based fixed demo estimate
- `dutyEstimateKzt`: 0 for low-value demo goods unless explicitly configured later

Do not claim this is customs-accurate.

## Demo seed data

Seed data should include approximately 200 synthetic demo intents later.

Required demo pool:

```txt
city: Almaty
category: electronics
title: wireless headphones
currentIntentCount: 24
moq: 25
```

This pool exists so a jury member can add one intent and trigger deal formation.

Synthetic data must include:

- city
- category
- title
- budget range
- created time
- isDemoData: true

## Deal formation logic

When a pool reaches MOQ:

```txt
if currentIntentCount >= moq:
  pool.status = "deal_formed"
```

Demo banner copy:

```txt
Pool reached 25 participants.
Birge formed a group deal.
```

Do not implement payments.

Do not implement real ordering.

Do not claim supplier confirmation.

## Honest pitch explanation

Use this explanation:

> The LLM normalizes a wish into a structured intent. Embeddings find similar demand. City and budget rules decide whether it joins a pool. The price forecast is based on category wholesale benchmarks; in production, it would be replaced by regression on completed deals.

## Known limitations

- Parser can be wrong.
- URL parsing is fallback-based during demo.
- Seed intents are synthetic demo data.
- Price forecast is benchmark-based.
- eSIM flow is a product demo animation, not real carrier provisioning.
- No payment or fulfillment in MVP.
