# Tasks: OpsAI MVP

**Input**: Design documents from `/specs/001-opsai-mvp/`  
**Prerequisites**: 
- ✅ plan.md (implementation plan with 4 services)
- ✅ spec.md (user stories and requirements)
- ✅ research.md (technology decisions)
- ✅ data-model.md (database schema with 4 entities)
- ✅ contracts/ (11 REST endpoints across 4 services)
- ✅ quickstart.md (local dev setup)

**Status**: Ready for Implementation | **Total Tasks**: 22 | **Estimated Duration**: 40 hours (8 hours × 5 people)

**Organization**: Tasks grouped by user story to enable independent implementation. Each user story is independently testable and deployable.

---

## Format Reference

- **[P]**: Task can run in parallel (independent files, no blocking dependencies)
- **[US#]**: User story label (US1–US5); setup/polish have no labels
- **File paths**: Exact paths for each task (relative to `backend/` directory)

---

## Phase 1: Setup & Infrastructure (3 tasks)

**Purpose**: Project initialization, scaffolding, and shared dependencies

- [ ] T001 Create project structure per plan.md (backend/ with services/, shared/, tests/, migrations/, seed_data/, web_ui/)

- [ ] T002 [P] Initialize Python 3.11+ environment with FastAPI, Pydantic, psycopg2-binary, google-generativeai, uvicorn, pytest in requirements.txt

- [ ] T003 [P] Create .env.example template with GEMINI_API_KEY, DATABASE_URL, service ports (8000-8003)

---

## Phase 2: Foundational Infrastructure (5 tasks)

**Purpose**: Core infrastructure that blocks all user story work

⚠️ **CRITICAL**: No user story tasks can start until ALL foundational tasks are complete

- [ ] T004 Create PostgreSQL schema with CREATE TYPE statements (order_status, intent_type, approval_status_enum) in backend/migrations/001_initial_schema.sql

- [ ] T005 [P] Create CREATE TABLE statements for customers, orders, stock, conversations in backend/migrations/001_initial_schema.sql

- [ ] T006 [P] Create indexes (phone, customer_id, status, approval_status, intent) in backend/migrations/001_initial_schema.sql

- [ ] T007 [P] Implement shared Pydantic models (request/response schemas, enums) in backend/shared/models.py

- [ ] T008 Implement PostgreSQL connection, session management, and connection pooling in backend/shared/database.py

**Checkpoint**: Database ready, shared models defined, Python environment ready. User story work can now begin in parallel.

---

## Phase 3: User Story 1 – AI Intent Classification (P1) 🎯 MVP

**Goal**: Receive customer messages and classify intent (order_lookup, stock_check, complaint, inquiry, other) using Gemini API with confidence scoring

**Independent Test**: Send test message via POST /api/messages → receive classification with confidence score; if confidence > 0.7, draft response generated

### Tests for User Story 1

- [ ] T009 [P] [US1] Create unit test for Gemini client classification in tests/unit/test_gemini_client.py (mock Gemini API, verify intent and confidence extraction)

- [ ] T010 [P] [US1] Create contract test for POST /api/classify endpoint in tests/contract/test_ai_service.py (mock Gemini, verify response schema)

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement Gemini API wrapper (classify method with error handling, retries, timeout) in backend/shared/gemini_client.py

- [ ] T012 [US1] Implement AI Service FastAPI app with POST /api/classify endpoint (call Gemini, return {intent, confidence}) in backend/services/ai_service/main.py

- [ ] T013 [US1] Implement API Gateway message ingestion endpoint (POST /api/messages: validate input, store in conversations table, call AI Service classify) in backend/services/api_gateway/routes/messages.py

- [ ] T014 [US1] Add error handling for low-confidence classifications: if confidence ≤ 0.7, set intent="other", set approval_status="escalated", skip lookup and draft generation in backend/services/api_gateway/routes/messages.py

- [ ] T015 [US1] Add logging for all classification calls (input, intent, confidence) in backend/shared/logging.py

**Checkpoint**: Message ingestion + intent classification working. Next: data lookup for each intent type.

---

## Phase 4: User Story 2 – Order Lookup (P1)

**Goal**: For order_lookup intent, retrieve order data from PostgreSQL and generate AI response draft

**Independent Test**: Send "Where is my order?" → classify as order_lookup → lookup order → generate draft response with tracking info

### Tests for User Story 2

- [ ] T016 [P] [US2] Create contract test for GET /api/orders/{order_id} in tests/contract/test_order_service.py (mock database, verify response schema with order details)

- [ ] T017 [P] [US2] Create contract test for GET /api/orders/by-phone/{phone} in tests/contract/test_order_service.py (mock database, verify array response)

- [ ] T018 [P] [US2] Create integration test for order_lookup flow (message → classify → lookup → draft) in tests/integration/test_end_to_end.py

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement Order Service FastAPI app with GET /api/orders/{order_id} endpoint (join customers + stock, return order details) in backend/services/order_service/main.py

- [ ] T020 [P] [US2] Implement GET /api/orders/by-phone/{phone} endpoint in backend/services/order_service/main.py

- [ ] T021 [US2] Implement order lookup logic in API Gateway (extract phone or order_id from message, call Order Service, handle 404) in backend/services/api_gateway/dependencies.py

- [ ] T022 [US2] Implement response draft generation for order_lookup via Gemini (POST /api/generate with intent + order data) in backend/services/ai_service/routes/generate.py

- [ ] T023 [US2] Update API Gateway to call AI Service generate endpoint after order lookup in backend/services/api_gateway/routes/messages.py

**Checkpoint**: Order lookup working end-to-end. User can send "Where is my order?" and receive draft response.

---

## Phase 5: User Story 3 – Stock Check (P1)

**Goal**: For stock_check intent, retrieve stock data and generate AI response draft

**Independent Test**: Send "Do you have size XL in blue?" → classify as stock_check → lookup stock → generate draft response

### Tests for User Story 3

- [ ] T024 [P] [US3] Create contract test for GET /api/stock/{product_id} in tests/contract/test_stock_service.py (mock database, verify product details with variants)

- [ ] T025 [P] [US3] Create contract test for GET /api/stock/search in tests/contract/test_stock_service.py (mock database, verify search results)

- [ ] T026 [P] [US3] Create integration test for stock_check flow in tests/integration/test_end_to_end.py

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement Stock Service FastAPI app with GET /api/stock/{product_id} endpoint (return product with quantity, variants) in backend/services/stock_service/main.py

- [ ] T028 [P] [US3] Implement GET /api/stock/search endpoint (query by product_name, SKU, color, size) in backend/services/stock_service/main.py

- [ ] T029 [US3] Implement stock lookup logic in API Gateway (parse message for product, call Stock Service search, handle 404) in backend/services/api_gateway/dependencies.py

- [ ] T030 [US3] Implement response draft generation for stock_check via Gemini in backend/services/ai_service/routes/generate.py

- [ ] T031 [US3] Update API Gateway to call Stock Service for stock_check intent in backend/services/api_gateway/routes/messages.py

**Checkpoint**: Stock check working end-to-end. User can send "Do you have XL in blue?" and receive draft response.

---

## Phase 6: User Story 4 – Human Approval & Dispatch (P1)

**Goal**: Display pending conversations in web UI, allow Ops team to approve/reject/edit responses, and dispatch approved responses

**Independent Test**: Retrieve pending messages via GET /api/conversations → approve one via POST /api/conversations/{id}/approve → response marked sent and logged

### Tests for User Story 4

- [ ] T032 [P] [US4] Create contract test for GET /api/conversations in tests/contract/test_api_gateway.py (mock database, verify pending messages with intent, draft, lookup data)

- [ ] T033 [P] [US4] Create contract test for POST /api/conversations/{id}/approve in tests/contract/test_api_gateway.py (mock database, verify approval status update and response logging)

- [ ] T034 [P] [US4] Create integration test for approval flow in tests/integration/test_end_to_end.py

### Implementation for User Story 4

- [ ] T035 [P] [US4] Create simple web UI (HTML + vanilla JS) at backend/web_ui/index.html (form showing pending message, intent, confidence, lookup data, draft response, approve/reject/edit buttons)

- [ ] T036 [P] [US4] Implement JavaScript API calls (fetch pending messages every 2s, submit approval) in backend/web_ui/app.js

- [ ] T037 [US4] Implement GET /api/conversations endpoint in API Gateway (query conversations table, return messages with approval_status IN ('pending','escalated','approved','rejected'); filter by query params if provided) in backend/services/api_gateway/routes/conversations.py

- [ ] T038 [US4] Implement POST /api/conversations/{id}/approve endpoint in API Gateway (request body: {action: 'approve'|'reject'|'edit', final_response: optional}; response: update approval_status, populate sent_at=NOW() on approve, return updated conversation JSON) in backend/services/api_gateway/routes/conversations.py

- [ ] T039 [US4] Implement mock WhatsApp dispatch: on approval, update conversations.sent_at=NOW(), log to stdout: "Sent to {phone}: {response_text}"; no Twilio/WhatsApp API calls; < 100ms latency in backend/services/api_gateway/dependencies.py

- [ ] T040 [US4] Implement GET /ui route to serve web UI in API Gateway in backend/services/api_gateway/main.py

**Checkpoint**: End-to-end flow complete! Message → classify → lookup → draft → approve → logged.

---

## Phase 7: User Story 5 – Conversation History & Metrics (P2)

**Goal**: Query conversation history and basic metrics (approval rate, message count)

**Independent Test**: Retrieve conversation history via GET /api/conversations?status=approved → verify paginated results with approval stats

### Tests for User Story 5

- [ ] T041 [P] [US5] Create integration test for conversation history query in tests/integration/test_end_to_end.py

### Implementation for User Story 5

- [ ] T042 [P] [US5] Extend GET /api/conversations to support filtering by status, pagination (limit, offset) in backend/services/api_gateway/routes/conversations.py

- [ ] T043 [P] [US5] Implement basic metrics endpoint (GET /api/metrics) returning total messages, approved count, rejected count, approval rate in backend/services/api_gateway/routes/metrics.py

- [ ] T044 [US5] Add metrics display to web UI (show approval rate, message count in header) in backend/web_ui/index.html and backend/web_ui/app.js

**Checkpoint**: Ops team can review conversation history and see approval metrics.

---

## Phase 8: Data Seeding & Demo Setup (3 tasks)

**Purpose**: Populate database with realistic test data and prepare for demo

- [ ] T045 [P] Create seed data for customers (5 realistic profiles with E.164 phone numbers) in backend/seed_data/customers.sql

- [ ] T046 [P] Create seed data for stock (10 products with variants: size, color) in backend/seed_data/stock.sql

- [ ] T047 [P] Create seed data for orders (5 orders linked to customers with various statuses: pending, processing, shipped, delivered) in backend/seed_data/orders.sql

---

## Phase 9: Testing & Quality Assurance (3 tasks)

**Purpose**: Validate all services work together and demo is reliable

- [ ] T048 [P] Run all unit tests (test_gemini_client.py, test_models.py) to verify business logic in backend/tests/unit/

- [ ] T049 [P] Run all contract tests to verify API schemas (test_api_gateway.py, test_ai_service.py, test_order_service.py, test_stock_service.py) in backend/tests/contract/

- [ ] T050 Run full end-to-end integration test (5 test messages, verify classification, lookup, draft, approval, logging) in backend/tests/integration/test_end_to_end.py

---

## Phase 10: Polish & Demo (2 tasks)

**Purpose**: Final cleanup, documentation, and demo script preparation

- [ ] T051 Create README.md with setup instructions (Docker Compose option), API overview, quickstart for running services in backend/README.md

- [ ] T052 Create demo script (memorized flow: send message → view pending → approve → show logged response) with timing notes (target 2–3 minutes) in docs/DEMO_SCRIPT.md

---

## Dependency Graph & Parallel Execution

### Critical Path (Blocking)
```
T001 (Setup) 
  → T002 (Python env) 
  → T003 (.env)
  → T004–T008 (Foundation: DB schema, models, connection)
  → T009–T015 (US1: Classification)
  → T016–T023 (US2: Order lookup)
  → T024–T031 (US3: Stock check)
  → T032–T040 (US4: Approval & dispatch)
```

### Parallel Opportunities
After T008 (Foundation complete):
- **Engineer 1**: T009–T015 (US1: AI Classification) → 2–3 hours
- **Engineer 2**: T016–T023 (US2: Order Lookup) → 2–3 hours
- **Engineer 3**: T024–T031 (US3: Stock Check) → 2–3 hours
- **Engineer 4**: T032–T040 (US4: Approval) → 2–3 hours
- **Demo Lead**: T035–T036 (Web UI), T045–T047 (Seed data), T051–T052 (Demo prep) → 2–3 hours

After US1–US4 complete:
- T041–T044 (US5: History & Metrics) → 1 hour
- T048–T050 (Testing) → 1–2 hours

### Time Estimate by Phase

| Phase | Tasks | Est. Time | Notes |
|-------|-------|-----------|-------|
| Phase 1: Setup | T001–T003 | 30 min | Sequential; unblock everything |
| Phase 2: Foundation | T004–T008 | 1.5 hours | Sequential; critical gate |
| Phase 3: US1 Classification | T009–T015 | 2 hours | Parallel possible on tests |
| Phase 4: US2 Order Lookup | T016–T023 | 2 hours | Parallel possible on tests |
| Phase 5: US3 Stock Check | T024–T031 | 2 hours | Parallel possible on tests |
| Phase 6: US4 Approval | T032–T040 | 2.5 hours | UI + endpoints; partially parallel |
| Phase 7: US5 History | T041–T044 | 1 hour | Low priority; can slip if time tight |
| Phase 8: Data Seeding | T045–T047 | 30 min | Parallel; low risk |
| Phase 9: Testing | T048–T050 | 1.5 hours | Parallel; can run in parallel |
| Phase 10: Polish | T051–T052 | 1 hour | Final; low risk |
| **TOTAL** | **22 tasks** | **~15 hours sequential** | **~40 hours parallel (8 hrs × 5 people)** |

---

## Success Criteria Checklist

### Must-Have (MVP Demo)
- [ ] All 4 services running without errors
- [ ] PostgreSQL populated with seed data
- [ ] Message ingestion works (POST /api/messages)
- [ ] Intent classification returns correct intent & confidence
- [ ] Order lookup returns order data
- [ ] Stock lookup returns product data
- [ ] Response draft generation works for all intents
- [ ] Web UI displays pending messages
- [ ] Approval updates conversations table
- [ ] All endpoints return JSON (no 500 errors)
- [ ] End-to-end flow: message → classify → lookup → draft → approve → logged (< 2 minutes)
- [ ] Demo script memorized and rehearsed

### Nice-to-Have (If Time Permits)
- [ ] Conversation history query works
- [ ] Metrics endpoint returns stats
- [ ] 80%+ test coverage
- [ ] Admin CLI to seed/reset database
- [ ] Confidence scores displayed in UI
- [ ] Response templates for common intents

### Out of Scope (Not for MVP)
- Real WhatsApp integration
- Authentication/authorization
- Production deployment
- Advanced analytics
- Multi-language support

---

## Definition of Done

### Per Task
- [ ] Code written to contract specification
- [ ] At least 1 peer reviewed the code
- [ ] All tests pass locally
- [ ] No hardcoded secrets; uses .env
- [ ] Code follows Python conventions (PEP 8)

### Per User Story
- [ ] All tasks completed
- [ ] Integration test passes (end-to-end for story)
- [ ] Demonstrated working on localhost
- [ ] Database changes applied
- [ ] No blocking bugs

### For Hackathon Release
- [ ] All 4 services running
- [ ] End-to-end flow testable in 2 minutes
- [ ] Web UI functional (no JavaScript errors)
- [ ] All critical bugs fixed
- [ ] Demo script ready

---

## Implementation Notes

### File Paths (Backend Structure)
```
backend/
├── services/
│   ├── api_gateway/
│   │   ├── main.py
│   │   └── routes/
│   │       ├── messages.py
│   │       ├── conversations.py
│   │       └── metrics.py
│   ├── ai_service/
│   │   ├── main.py
│   │   └── routes/
│   │       ├── classify.py
│   │       └── generate.py
│   ├── order_service/
│   │   ├── main.py
│   │   └── routes/
│   │       └── orders.py
│   └── stock_service/
│       ├── main.py
│       └── routes/
│           └── stock.py
├── shared/
│   ├── models.py
│   ├── database.py
│   ├── gemini_client.py
│   ├── logging.py
│   └── errors.py
├── web_ui/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── migrations/
│   └── 001_initial_schema.sql
├── seed_data/
│   ├── customers.sql
│   ├── orders.sql
│   └── stock.sql
├── tests/
│   ├── unit/
│   ├── contract/
│   └── integration/
├── requirements.txt
├── .env.example
├── README.md
└── pytest.ini
```

### Environment Variables (.env)
```
GEMINI_API_KEY=your-key-here
DATABASE_URL=postgresql://opsai:opsai@localhost:5432/opsai_db
API_GATEWAY_PORT=8000
AI_SERVICE_PORT=8001
ORDER_SERVICE_PORT=8002
STOCK_SERVICE_PORT=8003
DEBUG=false
```

### Task Assignment Recommendation
- **AI/Gemini Expert**: T009–T015 (US1: Classification)
- **Backend Engineer 1**: T016–T023 (US2: Order Service)
- **Backend Engineer 2**: T024–T031 (US3: Stock Service)
- **Backend Engineer 3**: T032–T040 (US4: Approval UI)
- **Demo Lead**: T035–T036 (UI polish), T045–T047 (Seed), T051–T052 (Demo)

---

## Quality Gates

- ✅ Phase 1: Setup complete before proceeding
- ✅ Phase 2: Foundation complete before any user story
- ✅ User Story 1 (Classification) must work before US2 & US3
- ✅ All 4 services must communicate without errors before final testing
- ✅ Demo script must be rehearsed and timed (target: 2–3 minutes)

---

**Task List Version**: 1.0.0 | **Generated**: 2026-05-11 | **Status**: Ready for Implementation

**Next**: Assign tasks to team members and begin Phase 1 (Setup).
