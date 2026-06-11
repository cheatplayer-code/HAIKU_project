# API_CONTRACT.md — Birge API Contract

## Purpose

This document defines the stable JSON API contract for the Birge MVP.

Target implementation later:

- Next.js Route Handlers
- TypeScript
- Supabase Postgres
- pgvector
- Claude API with cached fallback

No FastAPI.

No separate backend.

## General response format

Successful responses:

```ts
type ApiSuccess<T> = {
  ok: true;
  data: T;
  meta?: {
    requestId?: string;
    parserMode?: "live_llm" | "cache_fallback" | "rule_based_fallback";
    isDemoData?: boolean;
  };
};
```

Error responses:

```ts
type ApiError = {
  ok: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
};
```

All endpoints must return structured JSON.

Do not return unstructured text for API responses.

## Shared types

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

type ParserMode =
  | "live_llm"
  | "cache_fallback"
  | "rule_based_fallback";

type PoolStatus =
  | "forming"
  | "ready"
  | "deal_formed"
  | "closed";
```

---

# POST /api/intent/parse

## Purpose

Parse a product URL or free-text buying wish into a structured intent.

## Request

```ts
type ParseIntentRequest = {
  input: string;
  city: string;
  userLanguage?: "kk" | "ru" | "en";
};
```

## Response

```ts
type ParseIntentResponse = {
  intent: {
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
    parserMode: ParserMode;
    explanation: string;
  };
};
```

## Notes

- Live Claude parsing may be used later.
- Cached fallback must exist for demo reliability.
- No real scraping dependency.
- No fake exact specs.

---

# POST /api/pools/match

## Purpose

Match a parsed intent to an existing demand pool or propose a new pool.

## Request

```ts
type MatchPoolRequest = {
  city: string;
  intent: {
    normalizedTitle: string;
    localizedTitle: string;
    category: IntentCategory;
    specs: Record<string, string | number | boolean>;
    estimatedUnitPriceKzt: number | null;
    budgetMinKzt: number | null;
    budgetMaxKzt: number | null;
  };
};
```

## Response

```ts
type MatchPoolResponse = {
  match: {
    matchedExistingPool: boolean;
    similarityScore: number;
    ruleChecks: {
      cityMatched: boolean;
      categoryMatched: boolean;
      budgetOverlapped: boolean;
      similarityPassed: boolean;
    };
    pool: DemandPoolDto;
  };
};
```

---

# POST /api/intents

## Purpose

Create a user intent and attach it to a pool.

## Request

```ts
type CreateIntentRequest = {
  city: string;
  esimProfileId: string;
  input: string;
  parsedIntent: {
    normalizedTitle: string;
    localizedTitle: string;
    category: IntentCategory;
    specs: Record<string, string | number | boolean>;
    estimatedUnitPriceKzt: number | null;
    budgetMinKzt: number | null;
    budgetMaxKzt: number | null;
    parserMode: ParserMode;
  };
  poolId?: string;
};
```

## Response

```ts
type CreateIntentResponse = {
  intentId: string;
  pool: DemandPoolDto;
  dealFormed: boolean;
  dealBanner?: {
    title: string;
    message: string;
    estimatedGroupPriceKzt: number;
    estimatedSavingsPercent: number;
  };
};
```

## Deal formation rule

If adding the intent makes:

```txt
pool.currentIntentCount >= pool.moq
```

then response should include:

```ts
dealFormed: true
```

and a demo banner.

---

# GET /api/pools

## Purpose

Return forming demand pools for the city demand pulse screen.

## Query params

```txt
city=Almaty
category=electronics optional
limit=20 optional
```

## Response

```ts
type GetPoolsResponse = {
  city: string;
  totalFormingPools: number;
  pools: DemandPoolDto[];
};
```

---

# GET /api/pools/:id

## Purpose

Return detailed pool card data.

## Response

```ts
type GetPoolResponse = {
  pool: DemandPoolDto & {
    landedCostBreakdown: {
      productPriceKzt: number;
      cargoEstimateKzt: number;
      dutyEstimateKzt: number;
      totalLandedCostKzt: number;
      note: string;
    };
    timeline: Array<{
      step: string;
      status: "done" | "current" | "upcoming";
    }>;
    cityDemandPoints: Array<{
      lat: number;
      lng: number;
      weight: number;
      isSyntheticDemoPoint: boolean;
    }>;
  };
};
```

---

# GET /api/profile/intents

## Purpose

Return current demo user's intents.

## Query params

```txt
esimProfileId=demo-esim-profile
```

## Response

```ts
type GetProfileIntentsResponse = {
  esimProfileId: string;
  intents: Array<{
    id: string;
    title: string;
    localizedTitle: string;
    city: string;
    category: IntentCategory;
    poolId: string;
    poolStatus: PoolStatus;
    createdAt: string;
    isDemoData: boolean;
  }>;
};
```

---

# Shared DTO

```ts
type DemandPoolDto = {
  id: string;
  city: string;
  category: IntentCategory;
  title: string;
  localizedTitle: string;
  status: PoolStatus;
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

---

# Demo requirements

Required seeded pool later:

```json
{
  "city": "Almaty",
  "category": "electronics",
  "title": "wireless headphones",
  "currentIntentCount": 24,
  "moq": 25,
  "isDemoData": true
}
```

When a user adds the 25th intent, the API must return:

```json
{
  "dealFormed": true
}
```

## API rules

- Do not break these schemas without approval.
- Do not return fake production data.
- Do not claim real users.
- Do not require live Claude API for demo success.
- Do not require real scraping for demo success.
- Do not expose API keys.
- Do not implement payments.
- Do not implement real ordering.
- Do not implement real eSIM provisioning.

## Future environment variables

Later `.env.example` may include:

```txt
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
ANTHROPIC_API_KEY=
```

Never commit real values.
