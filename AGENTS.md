# AGENTS.md — Coding Agent Instructions

## Role

You are implementing Birge, a hackathon MVP.

Act as a careful senior engineer. Do not overscope. Do not invent features. Do not change architecture without approval.

## Non-negotiable product positioning

Birge is not a marketplace.

Birge is a demand aggregator.

The product collects buying intents and groups similar demand into city-level pools.

## Architecture

Use only this architecture unless explicitly changed by the human:

- Next.js
- TypeScript
- Tailwind CSS
- Supabase Postgres
- pgvector later
- Claude API later for intent parsing
- cached parser fallback
- Vercel

Do not introduce:

- FastAPI
- Flask
- Python backend
- Express backend
- duplicate API service
- another database unless explicitly approved

## How to work

Before editing code:

1. Read `QWEN.md`.
2. Read `MODEL_SPEC.md`.
3. Read `API_CONTRACT.md`.
4. Inspect existing files.
5. Follow the current phase only.

Do not perform tasks outside the current prompt.

## File safety

Do not delete files to make tests pass.

Do not rename public API routes without approval.

Do not change response schemas without updating `API_CONTRACT.md` and getting approval.

Do not commit secrets.

Do not add real `.env` values.

Use `.env.example` later when environment variables are needed.

## Product language

Forbidden user-facing terms:

- marketplace
- product feed
- catalog of discounts

Preferred user-facing terms:

- demand aggregator
- demand pooling
- intent
- pool
- forming pool
- city demand pulse
- demand cluster
- group deal
- eSIM identity profile
- C2M

Forbidden terms may appear only inside developer documentation as forbidden terminology.

## AI honesty

The system may use:

- LLM parsing
- cached LLM fallback
- embeddings
- pgvector similarity
- rule-based price forecast
- synthetic demo seed data

Do not claim:

- trained neural network
- real demand prediction model
- real user data
- real carrier integration
- real eSIM provisioning
- real scraping
- production-grade pricing accuracy

unless implemented and evaluated.

## Demo data

Synthetic data must be labeled internally as demo data.

Do not present demo seed data as real users.

Use phrases like:

- synthetic demo intents
- demo pools
- benchmark-based estimate

## Testing expectations

For every implementation task, add or run relevant checks.

Expected later commands may include:

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

If a command cannot run because the project is not scaffolded yet, state that clearly.

## Output after each task

Always report:

1. Summary
2. Files changed
3. Commands run
4. Test results
5. Risks/limitations
6. Next recommended task

Do not claim success without evidence.

## Strict rejection triggers

The work should be rejected if it:

- creates a FastAPI or Flask backend
- mixes unrelated architectures
- builds UI during a logic/API-only task
- changes public API schemas without approval
- deletes tests to pass
- commits API keys
- claims fake AI/ML accuracy
- presents synthetic data as real users
- builds checkout/payment/chat/admin features without approval
- uses forbidden product language in user-facing UI
