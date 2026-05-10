# OpsAI Constitution

<!-- Sync Impact Report: Version 1.0.0 (Initial) | Ratified: 2026-05-11 | New Project Constitution -->
<!-- Sections: Project Vision, Core Principles (7), Architecture Rules, AI Usage Rules, MVP Scope, Data Principles, Team Rules, Definition of Done, Success Criteria -->

## Project Vision

**OpsAI**: AI-powered operations assistant for small e-commerce businesses. WhatsApp messages → AI intent classification → order/stock lookup → AI draft reply → human approval → response delivery. Built for a 24–48 hour hackathon by a 5-person team with 8 hours max per person.

**Success is shipping a working end-to-end flow that a human can demo in 2 minutes.**

---

## Core Principles

### I. Hackathon-First (MANDATORY)
Every decision optimizes for shipping a working demo in 48 hours. No long-term scalability work. No architectural over-engineering. No speculative features. Build only what's required for the demo.

### II. Python + FastAPI (MANDATORY TECH STACK)
- Backend: Python 3.11+, FastAPI framework
- Database: PostgreSQL only (no alternatives, no in-memory tricks)
- APIs: REST only (no GraphQL, no gRPC)
- No message queues, Redis, Kafka, or async workers
- Max 4 backend microservices total

### III. Contract-First REST (NON-NEGOTIABLE)
Every REST API must define its request/response schema before implementation. All endpoints must return consistent JSON with a `status` field (`success` or `error`). Breaking changes are forbidden mid-hackathon; extend, don't replace.

### IV. AI-Centric, Not Infrastructure-Centric
Gemini API is the central intelligence. Investment goes into prompt engineering and classification logic, not deployment infrastructure. No Kubernetes, no Docker Compose complexity beyond local dev.

### V. Single Database Source of Truth
All state: customers, orders, stock, conversation logs → PostgreSQL only. No caching layers, no eventual consistency tricks. Query PostgreSQL directly. Use indexes if slow.

### VI. Security Minimal, Pragmatism Maximal
MVP does NOT require authentication/authorization beyond basic API keys (store in `.env`). No JWT tokens, OAuth, role-based access control. Keep it simple enough to build in 8 hours per person.

### VII. Human-in-the-Loop Approval (PRODUCT REQUIREMENT)
Every AI-generated response MUST be reviewed by a human before sending. No autonomous message dispatch. This is non-negotiable for a first version.

---

## Architecture Rules

1. **Max 4 Backend Services**: Define them upfront; no seventh service mid-project
2. **Synchronous Request-Response Only**: No background jobs, no webhooks, no async pipelines
3. **PostgreSQL Single Database**: One connection string, one schema. No sharding, no read replicas
4. **REST Endpoints Only**: No WebSockets, no Server-Sent Events
5. **Stateless Services**: Each request is independent; no in-process state
6. **No External Message Broker**: HTTP calls between services only
7. **Local Docker or Native PostgreSQL**: Hackathon doesn't require production deployment

---

## Gateway Contract-First Rule

All services expose versioned REST endpoints with:
- **Request schema**: Documented input fields, types, required vs. optional
- **Response schema**: `{ status: "success"|"error", data: {...}, error: "..." }`
- **Status codes**: 200 OK, 400 Bad Request, 404 Not Found, 500 Internal Server Error (only these four)

Before writing any service code, document:
1. Endpoint path and method (GET/POST/PUT)
2. Expected request body
3. Expected 200 response body
4. Expected error responses

No service touches another service's database. Use REST calls only.

---

## AI Usage Rules

### Gemini API Integration
- Single Gemini API client, shared across all AI tasks
- Prompts must be deterministic and testable (same input → same classification or reasoning)
- Temperature: 0.3 (low variance for hackathon)
- Max tokens: 500 per response (keep responses concise)

### Classification Pipeline
- Intent: `order_lookup`, `stock_check`, `complaint`, `inquiry`, `other`
- Confidence threshold: > 0.7 (else classify as `other`, escalate to human)
- Classify first, then fetch data, then generate response

### Response Generation
- Generate human-readable, concise drafts (2–3 sentences max)
- Include confidence score in draft (for human reviewer)
- No marketing fluff, no false promises

---

## MVP Scope

### INCLUDE (Required for Demo)
- WhatsApp message ingestion (fake for now; store in DB)
- Intent classification (Gemini API)
- Order lookup by customer phone (PostgreSQL query)
- Stock check (PostgreSQL query)
- Response generation (Gemini API)
- Human approval UI (web form or CLI, not pixel-perfect)
- Response logging (store in PostgreSQL)
- End-to-end demo: Message → Classification → Lookup → Draft → Approval → Logged

### EXCLUDE (Out of Scope)
- Real WhatsApp integration (use mock data)
- Mobile app
- Advanced analytics, dashboards, reporting
- Authentication/authorization
- Multi-language support
- Webhook integrations
- Background processing
- Rate limiting, monitoring, alerting
- Deployment to production cloud
- Customer segmentation, ML model training
- Admin dashboards beyond basic query tool

---

## Data Principles

### Minimal Schema
- **Customers**: `id, phone, name, created_at`
- **Orders**: `id, customer_id, product, qty, status, created_at`
- **Stock**: `product_id, product_name, qty_available`
- **Conversations**: `id, customer_id, message, classification, draft_response, approved_response, created_at`

### No Denormalization
Keep data normalized; avoid redundant copies. If a query is slow, add an index, don't duplicate data.

### Audit Trail
Every conversation is logged: message in, classification, draft, approval status, response sent. Enough for a demo walkthrough.

### Data Retention
Local SQLite or PostgreSQL only. No backups beyond git. No data export required for MVP.

---

## Team Rules

### Team Size
- 5 people total
- 4 engineers (backend/full-stack focus)
- 1 demo lead (UI, approval interface, demo script)

### Time Constraint
- 8 hours max per person, 48 hours total
- Work sequentially or in parallel; agree on a schedule upfront
- Aim for a clear hand-off every 12 hours (checkpoint)

### Code Ownership
- Clear service/feature assignment (who owns what?)
- All PRs require at least 1 other engineer's approval before merge
- Demo lead has final say on UI/UX for demo presentation

### Daily Sync
- Day 1 start: Architecture sync, service design, API contracts
- Day 1 + 12h: Integration checkpoint (can services talk?)
- Day 2 start: End-to-end test, demo script walkthrough
- Day 2 + 24h: Final demo prep, edge case fixes

### Communication
- Slack/Discord for async chat
- 15-min standup every 12 hours (no longer)
- Shared GitHub repo; CI/CD via GitHub Actions (no deploy, just lint/test)

---

## Definition of Done

### For Each Service
- [ ] REST API contracts documented (request, response, status codes)
- [ ] Unit tests pass locally (>80% coverage of business logic)
- [ ] PostgreSQL schema created and migrations tested
- [ ] Service integrates with other services (no 500 errors)
- [ ] Handles errors gracefully (returns JSON error response, not 500)

### For Each Feature
- [ ] All tests pass
- [ ] Code reviewed and approved by 1+ peer
- [ ] Deployed to demo environment (localhost or staging VM)
- [ ] Works end-to-end with real (or realistic mock) data
- [ ] Demo script includes this feature

### For Hackathon Release
- [ ] All 4 services deployed
- [ ] End-to-end flow works: Message → Response → Logged
- [ ] Human approval interface functional
- [ ] Demo script memorized and timed (< 5 minutes)
- [ ] All critical bugs fixed or documented
- [ ] No hardcoded passwords; use `.env` for secrets

---

## Success Criteria

### Minimum (Must-Have for Demo)
1. ✅ WhatsApp message (mock) ingested and stored
2. ✅ Gemini intent classification working (≥3 intents)
3. ✅ Order lookup returns correct data from PostgreSQL
4. ✅ Stock check returns correct data from PostgreSQL
5. ✅ Response generation produces human-readable drafts
6. ✅ Human approval interface allows accept/reject/edit
7. ✅ Final response logged to PostgreSQL
8. ✅ End-to-end demo completable in 2 minutes

### Nice-to-Have (If Time Permits)
- Multiple customers in seed data
- Admin CLI to seed data and query logs
- Confidence scores displayed in approval UI
- Response templates for common intents
- Metrics endpoint (# messages processed, # approved, # rejected)

### Non-Goals
- Scalability beyond one demo environment
- Production-grade security
- Mobile responsiveness
- Multi-language NLP
- Machine learning model training

---

## Governance

### Constitution Override
This constitution supersedes all other guidance. If a best practice or feature request conflicts with the hackathon constraints, this constitution wins.

### Amendment Process
Changes to this constitution require unanimous team agreement and must be documented in Git with a commit message explaining the rationale. No silent changes.

### Compliance Review
Demo lead performs a final compliance check 2 hours before presentation:
- All 4 services are running
- All endpoints return expected JSON
- Database has seed data
- No hardcoded secrets in code
- Demo script has been rehearsed

### Guidance Documentation
This constitution is the source of truth. Additional runtime guidance (e.g., local dev setup, testing strategy) belongs in `README.md` or `docs/DEVELOPMENT.md`, not here.

---

**Version**: 1.0.0 | **Ratified**: 2026-05-11 | **Last Amended**: 2026-05-11
