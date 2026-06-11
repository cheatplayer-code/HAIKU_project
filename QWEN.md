# QWEN.md — Birge Development Rules

## Project

Birge is a hackathon MVP for AI-powered demand aggregation.

First pitch line:

> We are not a marketplace.

Slogan:

> Demand is the new wholesale.

Birge does not show a normal product catalog. Users express what they want to buy by pasting a product link or writing a buying intent. The system parses the intent, localizes it, estimates landed cost in KZT, matches it with similar city-level demand, and places it into a forming demand pool. When the pool reaches MOQ, Birge forms a group deal.

## Source of truth

These files are the source of truth:

- `QWEN.md`
- `AGENTS.md`
- `MODEL_SPEC.md`
- `API_CONTRACT.md`

If implementation conflicts with these files, stop and report the conflict before changing architecture.

## Target architecture

Use:

- FastAPI
- Python
- Pydantic models
- pytest tests
- in-memory demo repository first
- optional vector similarity later
- optional LLM parser later
- cached parser fallback for demo reliability

Do not use:

- Next.js
- TypeScript
- Tailwind CSS
- Supabase as current requirement
- pgvector as current requirement
- Vercel as current requirement
- duplicate frontend/backend systems
- real scraping as a required demo dependency
- committed API keys
- fake ML claims

## Product positioning

Birge is not a marketplace.

Birge is a demand aggregator.

The product collects fragmented buying wishes and turns them into city-level demand pools.

User journey:

1. User receives an eSIM identity profile demo.
2. User selects interests.
3. User sees city demand pulse.
4. User pastes a link or writes an intent.
5. AI parser converts the input into a structured intent.
6. System searches similar demand.
7. User joins a pool.
8. If MOQ is reached, Birge forms a group deal.

## Product language rules

Forbidden user-facing words:

- marketplace
- product feed
- catalog of discounts

Allowed user-facing words:

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

The main screen is not a product feed. It is the city demand pulse with forming pools.

Forbidden words may appear only in developer documentation when explaining what not to say.

## Main demo story

The 90-second demo should eventually work like this:

1. Start with: “We are not a marketplace.”
2. Show eSIM-first onboarding animation.
3. Open the “I want” screen.
4. Jury pastes a link or writes a buying intent.
5. Visible AI pipeline runs:
   - Recognize product
   - Translate/localize
   - Estimate landed cost
   - Search similar demand
6. System finds similar intents in Almaty.
7. User joins the pool.
8. Demo pool reaches MOQ.
9. Full-screen banner appears:
   - “Pool reached 25 participants.”
   - “Birge formed a group deal.”
10. Closing:
   - “Today we collect groups. Tomorrow we sell aggregated demand directly to factories.”

## Main wow feature

The main wow feature is the AI intent parser with cached fallback.

The parser must accept:

- product URL
- free text in Kazakh
- free text in Russian
- free text in English

The parser returns a structured intent.

Do not make extra features more important than this.

## AI / ML honesty rules

Always distinguish:

- LLM parsing
- cached LLM fallback
- embedding similarity
- rule-based price forecast
- synthetic demo data
- future production ML

Do not claim:

- trained neural network
- collaborative filtering
- demand prediction model
- 95% accuracy
- production user data
- real carrier integration
- real eSIM provisioning
- real supplier confirmation

unless actually implemented and verified.

## Demo reliability

Live Claude parsing is allowed later, but the demo must not depend on it.

Required fallback later:

- at least 10 cached demo parser responses
- if Claude API fails, return cached parser result
- cached results must be clearly marked internally as fallback/demo data
- code/docs must not pretend fallback is live parsing

## Scope control

Build in small phases.

Approved phase order:

1. Context files
2. Minimal FastAPI scaffold
3. Pydantic domain models
4. Pure intent parsing logic
5. Pure pool matching logic
6. Demo seed data
7. API endpoints
8. Tests/evals
9. Audit/fix pass
10. Optional UI later

Never build everything in one task.

## Forbidden features unless explicitly approved

Do not build:

- checkout
- payments
- chat between users
- full product catalog
- seller dashboard before core demo works
- B2B dashboard before core user demo works
- real scraping without fallback
- real carrier billing
- real eSIM provisioning
- complex production authentication
- admin panel
- native mobile app
- trained neural network
- collaborative filtering
- complex recommendation engine
- production analytics

## Required screens later

The final demo should eventually include:

1. eSIM-first onboarding
2. Interest selection
3. City demand pulse
4. “I want” intent input screen
5. Pool card / join screen
6. Auto deal formation banner
7. Profile / My intents
8. How it works / Level 1 to Level 2 eSIM/C2M explanation

Do not create UI until the current task explicitly asks for UI.

## Verification rule

After every coding task, report:

- files changed
- commands run
- command output summary
- tests passed or failed
- known limitations
- any unverified claims

Never say “tests pass” without showing the command that was run.
