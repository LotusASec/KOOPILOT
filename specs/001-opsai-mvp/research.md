# Research & Technology Decisions: OpsAI MVP

**Phase**: Phase 0 (Research & Unknowns Resolution)  
**Date**: 2026-05-11  
**Status**: ✅ Complete  

---

## Research Overview

This document consolidates all technical decisions made for OpsAI MVP based on the specification, constitution, and hackathon constraints. All decisions are documented with rationale and alternatives considered.

---

## 1. Gemini API Integration

### Decision
Use Google's `google-generativeai` Python SDK for intent classification and response generation. Configure with:
- **Temperature**: 0.3 (low variance for deterministic behavior)
- **Max Tokens**: 500 per response
- **Model**: `gemini-pro` (or latest available)
- **Timeout**: 10 seconds (fail gracefully if API is slow)

### Rationale
- **Mandatory**: Constitution specifies Gemini API as the AI engine
- **Deterministic**: Temperature 0.3 ensures same input → consistent output (critical for demo reproducibility)
- **Concise Responses**: 500-token limit keeps responses brief and human-reviewable
- **Built-in SDK**: google-generativeai provides idiomatic Python integration with error handling

### Alternatives Considered
1. **Direct REST calls to Gemini API** — More verbose; SDK handles auth and retries
2. **OpenAI API** — Not specified in constraints; would violate constitution
3. **Local LLM (LLaMA, etc.)** — No GPU available for hackathon; Gemini API is cloud-based and instant
4. **No AI, hardcoded responses** — Defeats purpose; not a demo-worthy solution

### Implementation Notes
- API key stored in `.env` (never in code)
- Wrapper function in `shared/gemini_client.py` for:
  - Retries with exponential backoff
  - Error handling (timeout → generic response)
  - Logging for debugging
  - Request/response serialization

---

## 2. PostgreSQL Schema Design

### Decision
4-table normalized relational schema:

| Table | Purpose | Key Fields |
|-------|---------|-----------|
| `customers` | Customer profiles | `id` (PK), `phone` (unique), `name`, `created_at` |
| `orders` | Purchase history | `id` (PK), `customer_id` (FK), `status`, `estimated_delivery`, `product_id` |
| `stock` | Inventory | `id` (PK), `product_name`, `sku`, `quantity_available`, `size`, `color` |
| `conversations` | Message log | `id` (PK), `customer_id` (FK), `intent_classified`, `confidence_score`, `draft_response`, `approval_status`, `final_response`, `sent_at` |

### Rationale
- **Normalized**: Avoids data duplication, prevents inconsistency (e.g., changing customer name in one place)
- **Indexed for Performance**: Indexes on `phone`, `customer_id`, `status`, `approval_status` for fast queries
- **Audit Trail**: Conversations table logs every interaction (immutable records for compliance)
- **Simple for Hackathon**: No complex joins; queries are straightforward and fast
- **PostgreSQL Native**: Supports JSONB for flexible lookup data storage without schema changes

### Alternatives Considered
1. **Denormalized Schema** — Redundant data (customer name in orders table); harder to maintain; risk of inconsistency
2. **NoSQL (MongoDB, DynamoDB)** — Violates constitution (PostgreSQL only); harder to enforce referential integrity
3. **In-Memory Database (Redis)** — Violates constitution (PostgreSQL only); data lost on restart; not suitable for audit trail
4. **Single Monolithic Table** — All data in one table; inefficient queries; hard to scale if needed later

### Implementation Notes
- Use Alembic for migrations (or manual SQL scripts if Alembic setup is too complex)
- All tables use `TIMESTAMPTZ` for UTC timestamps
- Foreign keys enforce referential integrity
- Conversations table uses ENUM for intent and status (prevents typos)
- See `data-model.md` for complete DDL and migration scripts

---

## 3. Microservices Communication Pattern

### Decision
Synchronous REST/JSON calls between services with:
- **Timeout**: 5 seconds for inter-service calls
- **Timeout**: 10 seconds for external APIs (Gemini)
- **Error Response**: Always return JSON with `status: "error"` and message
- **HTTP Status Codes**: 200 OK, 400 Bad Request, 404 Not Found, 500 Internal Server Error (only these 4)
- **No Retries**: Simpler logic for hackathon; fail fast and let Gateway handle escalation
- **Connection Pool**: Reuse HTTP client connections (via httpx or requests sessions)

### Rationale
- **Synchronous**: No async workers, no message queues → simpler debugging and demo walkthrough
- **Request-Response**: Each call completes before next step → deterministic flow (good for demo)
- **REST + JSON**: Standard protocol; easy to test with curl/Postman; universally understood
- **Short Timeouts**: Fail fast if service is unresponsive; prevent hanging
- **Consistent Error Format**: All services follow same schema → Gateway can handle errors uniformly

### Alternatives Considered
1. **Asynchronous with Queues (Kafka, RabbitMQ)** — Requires message broker infrastructure; complex to debug; overkill for demo
2. **gRPC** — Faster, but more complex setup; requires protobuf; harder to test manually
3. **GraphQL** — Violates constitution (REST only); adds query language complexity
4. **WebSockets** — Not needed; demo doesn't require real-time streaming
5. **No Communication** — Single monolithic service; violates contract-first principle and team parallel work

### Implementation Notes
- API Gateway is the routing layer (no direct service-to-service calls except via Gateway)
- Shared `shared/http_client.py` for all inter-service calls
- Health checks: `GET /health` on all services (200 OK = healthy)
- Shared error models in `shared/models.py` for consistent responses

---

## 4. Web UI for Human Approval

### Decision
Simple HTML + vanilla JavaScript (no frameworks), hosted by API Gateway:
- **HTML**: Single-page form showing one pending message at a time
- **JavaScript**: Fetch API for approval/rejection, polling for new messages
- **Styling**: Minimal CSS (or Bootstrap CDN for basic styling)
- **No Build Step**: HTML/JS served as static files; no webpack/Vite complexity

### Rationale
- **Fast Development**: Vanilla JS requires no build tooling; HTML/CSS is straightforward
- **No Dependencies**: Reduces bundle size and deployment complexity
- **Easy to Understand**: Any engineer can read and modify in 30 minutes
- **Sufficient for Demo**: Single approval flow doesn't need rich interactivity
- **Hackathon Context**: 8 hours per person; complex UI framework is not the bottleneck

### Alternatives Considered
1. **React/Vue/Svelte** — Overkill; adds 30+ min setup time; requires Node.js build pipeline
2. **Admin Dashboard (Django Admin, Flask-Admin)** — Too feature-rich; not needed for MVP
3. **CLI Only** — Less impressive for demo; harder for non-technical stakeholders to use
4. **No UI, Curl Only** — Not demo-friendly; tedious for human approval workflow

### Implementation Notes
- Hosted at `http://localhost:8000/ui` (served by API Gateway)
- Polling interval: 2 seconds (check for new pending messages)
- Approval form: Radio buttons for Approve/Reject/Edit, Submit button
- On submit: Call `POST /api/conversations/{id}/approve` with action and optional edits
- Display: Original message, classified intent, confidence, draft, lookup data

---

## 5. Authentication & Security

### Decision
No authentication/authorization for MVP. Security approach:
- **API Keys**: Optional, stored in `.env` for future use (not enforced in MVP)
- **No JWT/OAuth**: Skip for hackathon; adds 4+ hours of implementation
- **No RBAC**: Single "ops team" role; no role-based access control
- **HTTPS**: Not required for demo (localhost or internal network)
- **CORS**: Allow requests from `http://localhost:*` (demo UI origin)
- **Secret Management**: `.env` file for API keys; `.gitignore` to prevent leakage

### Rationale
- **Hackathon Environment**: Demo runs on localhost or internal network; no public exposure
- **Time Constraint**: 8 hours per person; auth is not the feature being demoed
- **Pragmatism**: Build feature first; add security later if needed
- **Constitution Approved**: "Security Minimal, Pragmatism Maximal" principle allows this

### Alternatives Considered
1. **JWT Tokens** — 3–4 hours to implement; overkill for single ops team
2. **OAuth 2.0** — Even more complex; unnecessary for internal demo
3. **API Key Validation** — Adds 30 min; minimal security benefit for internal network
4. **Hardcoded Secrets** — Bad practice; violates security principle

### Implementation Notes
- `shared/config.py` loads `.env` file using `python-dotenv`
- Gemini API key: `GEMINI_API_KEY` in `.env`
- Database URL: `DATABASE_URL` in `.env`
- Example: `.env.example` provided (all values commented with instructions)
- See `README.md` for setup instructions

---

## 6. Testing Strategy

### Decision
Tiered testing approach:
- **Unit Tests**: Gemini client (mock Gemini API), Pydantic models, error handling
- **Integration Tests**: Service-to-service REST calls (mock external APIs), database operations
- **End-to-End Tests**: Full flow from message ingestion to approval (mock WhatsApp only)
- **Tool**: pytest for all test layers
- **Coverage Target**: >80% for business logic (classification, lookup, response generation)

### Rationale
- **Unit Tests First**: Fastest feedback loop; catch bugs early (Gemini classification rules, validation)
- **Integration Tests Second**: Ensure services work together (API contracts, error propagation)
- **E2E Tests**: Validate complete flow works (message → classification → lookup → draft → approval → sent)
- **Mock External APIs**: No real Gemini calls in tests (unreliable, slow, costly)
- **>80% Coverage**: Ensures critical paths are tested; not obsessive about 100%

### Alternatives Considered
1. **E2E Only** — Slow to run; hard to isolate failures; tight coupling to real Gemini API
2. **No Tests** — Risky for demo; one bug breaks the entire flow
3. **Manual Testing Only** — Not scalable; hard to reproduce bugs
4. **100% Coverage** — Time-consuming; diminishing returns; not necessary for MVP

### Implementation Notes
- Test structure:
  - `tests/unit/test_gemini_client.py` — Mock Gemini API, test classification/generation logic
  - `tests/unit/test_models.py` — Pydantic validation, error schemas
  - `tests/integration/test_api_gateway.py` — Mock AI/Order/Stock services, test routing
  - `tests/integration/test_*_service.py` — Mock database, test service endpoints
  - `tests/integration/test_end_to_end.py` — Full flow with mocked external APIs
- Fixtures in `tests/conftest.py` for database setup, mock Gemini client, sample data
- Run tests before every demo: `pytest -v`

---

## 7. Deployment & Local Development

### Decision
Local development environment only (no production deployment for MVP):
- **Docker Compose**: Single `docker-compose.yml` for PostgreSQL + 4 services
- **Alternative**: Native PostgreSQL + manual service startup (for minimal Docker knowledge)
- **Seed Data**: SQL scripts in `seed_data/` directory
- **Helper Script**: `run_services.sh` to start all 4 services with one command

### Rationale
- **Docker Compose**: Reproducible environment; everyone has same setup
- **No Kubernetes**: Overkill for single-instance hackathon demo
- **No CI/CD**: GitHub Actions not needed; manual testing sufficient
- **Local-Only**: No cloud deployment (no AWS/GCP/Azure setup)
- **Fast Iteration**: Services restart in < 5 seconds

### Alternatives Considered
1. **Kubernetes**: Too complex; 6+ hours to learn and setup
2. **Manual Server Setup**: Brittle; environment differences between team members
3. **Cloud Deployment (AWS)**: Adds cost, latency, setup complexity; not needed for demo
4. **Single Service (no Docker)**: Works, but less reproducible; risk of "it works on my machine" issues

### Implementation Notes
- `docker-compose.yml`: PostgreSQL (port 5432), 4 services on ports 8001–8004
- `run_services.sh`: Starts all services in parallel (or sequentially for simpler debugging)
- `.env.example`: Template for developers; copy to `.env` and fill in values
- `README.md`: Setup instructions (install Docker, clone repo, `docker-compose up`, run seed script)

---

## Best Practices Applied

### ✅ Stateless Services
- No in-process state; all data in PostgreSQL
- Each request is independent
- Services can be restarted without losing data

### ✅ Contract-First APIs
- All REST endpoints documented before implementation
- Request/response schemas defined in code (Pydantic models)
- Breaking changes forbidden during hackathon

### ✅ Human-in-the-Loop
- All AI responses require human approval
- No autonomous message dispatch
- Audit trail for compliance

### ✅ Synchronous Request-Response
- No queues, no async workers
- Simpler debugging, deterministic flow
- All requests complete in < 5 seconds

### ✅ Single Source of Truth
- PostgreSQL only, no caching
- Direct queries, no eventual consistency issues
- Indexed for performance

### ✅ Error Handling
- All errors return JSON with `status: "error"` and message
- No 500 errors in normal operation (caught and handled)
- Graceful degradation (e.g., classification timeout → mark as `other`, escalate)

### ✅ Security Pragmatism
- Secrets in `.env`, not in code
- No auth for internal demo
- Can be added later if needed

---

## Summary

All technical decisions are documented, justified, and aligned with:
- ✅ OpsAI Constitution (7 core principles, 7 architecture rules)
- ✅ OpsAI Specification (functional & non-functional requirements)
- ✅ Hackathon Constraints (48 hours, 5 people, 8 hours max per person)

**Status**: ✅ All unknowns resolved. Ready to proceed to Phase 1 (Design & Contracts).

---

**Version**: 1.0.0 | **Created**: 2026-05-11 | **Status**: Complete
