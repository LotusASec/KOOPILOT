# OpsAI MVP Specification

**Feature**: AI-Powered Operations Assistant for E-Commerce WhatsApp  
**Version**: 1.0.0  
**Status**: In Specification  
**Ratified**: 2026-05-11  

---

## Product Overview

OpsAI is an AI-powered operations assistant that helps small e-commerce businesses handle customer inquiries over WhatsApp. When a customer sends a message, OpsAI intelligently classifies the intent (order lookup, stock check, complaint, or general inquiry), retrieves relevant data from the business database, generates a human-readable draft response using AI, and waits for human approval before sending. This reduces ops team workload while maintaining quality and accuracy for each customer interaction.

---

## Problem Statement

Small e-commerce businesses spend significant time manually answering repetitive customer questions about orders and stock availability on WhatsApp. Common tasks include:
- "When will my order arrive?" → manually look up order status
- "Do you have size XL in blue?" → manually check inventory
- "Can I return this?" → manually check return policy

These queries are routine but time-consuming, pulling ops staff away from higher-value work. Businesses need a way to handle these inquiries at scale without hiring additional staff or sacrificing response quality.

**OpsAI solves this by**: Automating inquiry classification and data lookup, providing instant draft responses for human review, and logging all interactions for accountability.

---

## User Roles

### 1. **Ops Team Member** (Primary User)
- Monitors incoming customer messages
- Reviews AI-generated responses in an approval interface
- Approves, rejects, or edits draft responses
- Handles escalations (complaints, complex queries)
- Goal: Process 10+ inquiries in <30 minutes with 95%+ accuracy

### 2. **Business Owner** (Secondary User)
- Views aggregate metrics (messages processed, approval rate)
- Seeds customer/order/stock data
- Manages bot configuration (intents, response templates)
- Goal: Quick overview of bot health and customer satisfaction

### 3. **System** (Non-Human Actor)
- Listens for incoming WhatsApp messages
- Classifies intent using Gemini API
- Looks up order and stock data from PostgreSQL
- Generates response drafts
- Logs interactions for audit trail

---

## Core User Journey

### Primary Flow: Message → Classification → Lookup → Draft → Approval → Send

**Step 1: Customer Message Received**
- Customer sends WhatsApp message: "Can I cancel order #12345?"
- Message ingested and stored in `conversations` table
- Message is assigned a unique conversation ID

**Step 2: AI Intent Classification**
- Gemini API receives message and classification prompt
- Gemini returns: `{ intent: "order_lookup", confidence: 0.92 }`
- System stores classification result in database
- Confidence > 0.7 → proceed; else → escalate to human

**Step 3: Data Lookup**
- If `order_lookup`: Query `orders` table for order #12345
- If `stock_check`: Query `stock` table for matching product
- If `complaint`: Flag for human review
- If `inquiry`: Return generic response template
- Return: Order status, stock level, or escalation flag

**Step 4: AI Response Draft Generation**
- Gemini API receives intent, customer data, and retrieved order data
- Gemini generates draft: "Your order #12345 is en route and will arrive on May 15th. Tracking: [link]"
- System stores draft with confidence score in `conversations` table

**Step 5: Human Approval**
- Ops team opens web form showing:
  - Original customer message
  - Classified intent
  - Draft response with confidence score
  - Relevant customer/order data
- Ops team can: **Approve**, **Reject + Escalate**, or **Edit + Approve**

**Step 6: Response Dispatch**
- On approval, response is sent via WhatsApp (mock or real)
- Status logged as `sent` in conversations table
- Conversation marked complete
- UI refreshes to show next pending message

**Expected Cycle Time**: < 2 minutes per message (classification + lookup + approval)

---

## Functional Requirements

1. **WhatsApp Message Ingestion** (REST API)
   - Accept incoming WhatsApp messages via `/api/messages` POST endpoint
   - Store message in `conversations` table with `received_at` timestamp
   - Return 200 OK immediately (non-blocking)

2. **Intent Classification** (AI Service)
   - Use Gemini API to classify intent into 4 categories: `order_lookup`, `stock_check`, `complaint`, `inquiry`
   - Return confidence score (0–1)
   - Threshold: confidence > 0.7 → proceed; else → mark as `other` and escalate
   - Temperature: 0.3 (deterministic)

3. **Order Data Lookup** (Order Service)
   - Endpoint: `/api/orders/{order_id}` or `/api/orders/by-phone/{phone}`
   - Return: order ID, customer name, status, estimated delivery date, tracking link
   - Handle 404: Order not found

4. **Stock Data Lookup** (Stock Service)
   - Endpoint: `/api/stock/{product_id}` 
   - Return: product name, quantity available, size/color variants (if applicable)
   - Handle 404: Product not found

5. **Response Draft Generation** (AI Service)
   - Use Gemini API to generate 2–3 sentence response based on classified intent and lookup data
   - Embed confidence score in draft for human reviewer
   - Max tokens: 500; temperature: 0.3
   - No promises or guarantees; focus on facts from database only

6. **Human Approval Interface** (Web UI)
   - Display pending and escalated messages in chronological order
   - For `pending` messages: Show original message, classified intent, confidence score, lookup data, draft response; Approve, Reject, Edit buttons
   - For `escalated` messages: Show original message, intent=other, confidence score, NO lookup data, NO draft; read-only (manual handling only)
   - On approve: update approval_status = `approved`, populate final_response and sent_at = NOW()
   - On reject: update approval_status = `rejected`
   - On edit: allow inline editing of draft_response, then update approval_status = `edited`, populate sent_at = NOW()

7. **Conversation Logging** (API Gateway)
   - Store every interaction: message, classification, confidence, lookup data, draft, approval status, final response
   - Enable audit trail for compliance and debugging
   - Query: `/api/conversations?limit=50&offset=0` for historical view

---

## Non-Functional Requirements

### Performance
- Message ingestion: < 100ms
- Intent classification: < 2 seconds (Gemini API latency)
- Order/stock lookup: < 500ms (PostgreSQL indexed query)
- Response generation: < 2 seconds
- **Total end-to-end time**: < 5 seconds from message to draft (excluding human approval time)

### Reliability
- Graceful error handling: all failures return JSON with `status: "error"` and descriptive message
- No 500 errors in normal operation; catch and log all exceptions
- Database connection pooling: reuse connections, no connection exhaustion
- Gemini API timeout: 10 seconds; fail gracefully with generic response

### Security (Pragmatic, Non-Production)
- API keys stored in `.env` file (not in code)
- No authentication/authorization for hackathon demo (all endpoints public)
- No encryption required; demo runs on localhost or internal network only
- CORS: allow requests from demo UI origin only

### Simplicity
- Single PostgreSQL database; no caching, no Redis
- Synchronous request-response only; no background workers or queues
- Four services max; clear REST API contracts between services
- Deterministic AI responses (temperature 0.3); no non-deterministic behavior

### Data Integrity
- No partial updates; all writes are atomic
- Conversation log is append-only (no deletes/updates)
- Order and stock data are read-only during demo

---

## System Boundaries

### What OpsAI **DOES**
✅ Receive WhatsApp messages (mock for demo, real via API for production)  
✅ Classify intent using AI  
✅ Retrieve customer, order, and stock data from PostgreSQL  
✅ Generate draft responses using AI  
✅ Require human approval before sending  
✅ Log all interactions for audit trail  
✅ Provide web UI for human reviewers  
✅ Return consistent REST JSON responses  

### What OpsAI **DOES NOT** (Out of Scope)

❌ **Multi-Channel Integration**: Only WhatsApp; no email, SMS, Telegram, or Slack  
❌ **Autonomous Message Sending**: All responses require human approval first  
❌ **AI Learning/Model Training**: Use Gemini API as-is; no fine-tuning or custom models  
❌ **Advanced Analytics**: No dashboards, charts, or ML-powered insights  
❌ **Authentication/Authorization**: No user roles, permissions, or multi-tenant support  
❌ **Message Queues or Background Jobs**: No Kafka, RabbitMQ, Celery, or async workers  
❌ **Caching or Redis**: Direct PostgreSQL queries only  
❌ **API Versioning Beyond REST**: No GraphQL, gRPC, or WebSocket  
❌ **Mobile App**: Web UI only; no iOS/Android native app  
❌ **Real-Time Notifications**: No push notifications, webhooks, or live updates  
❌ **Scalability**: Single-instance deployment; no load balancing or horizontal scaling  
❌ **Data Export or Backup**: No CSV exports, scheduled backups, or data warehousing  
❌ **Multi-Language Support**: English only  
❌ **Integration with External CRMs**: No Shopify, Salesforce, or HubSpot sync  
❌ **Customer Segmentation**: No targeting rules, A/B testing, or audience filters  
❌ **Production Compliance**: No GDPR, HIPAA, SOC2, or compliance audit  

---

## Data Model

### Core Entities

#### **customers**
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `phone` | VARCHAR(20) | WhatsApp phone number, unique |
| `name` | VARCHAR(255) | Customer name |
| `created_at` | TIMESTAMP | Account creation time |

#### **orders**
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `customer_id` | UUID | Foreign key → customers |
| `product_id` | UUID | Foreign key → stock |
| `quantity` | INT | Number of units |
| `status` | ENUM | `pending`, `processing`, `shipped`, `delivered`, `cancelled` |
| `estimated_delivery` | DATE | Expected delivery date |
| `tracking_url` | TEXT | Tracking link (nullable) |
| `created_at` | TIMESTAMP | Order placement time |
| `updated_at` | TIMESTAMP | Last status update |

#### **stock**
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `product_name` | VARCHAR(255) | Product name |
| `sku` | VARCHAR(50) | Stock keeping unit |
| `quantity_available` | INT | Units in stock |
| `size` | VARCHAR(50) | Size (nullable, e.g., "XL") |
| `color` | VARCHAR(50) | Color (nullable, e.g., "blue") |
| `created_at` | TIMESTAMP | Product creation time |
| `updated_at` | TIMESTAMP | Last inventory update |

#### **conversations**
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `customer_id` | UUID | Foreign key → customers (nullable if new customer) |
| `phone` | VARCHAR(20) | Sender phone number |
| `message_text` | TEXT | Original customer message |
| `intent_classified` | ENUM | `order_lookup`, `stock_check`, `complaint`, `inquiry`, `other` |
| `confidence_score` | DECIMAL(3,2) | Classification confidence (0.0–1.0) |
| `lookup_data` | JSONB | Retrieved order/stock data (dict) |
| `draft_response` | TEXT | AI-generated response |
| `draft_confidence` | DECIMAL(3,2) | Response generation confidence (0.0–1.0) |
| `approval_status` | ENUM | `pending`, `approved`, `rejected`, `edited` |
| `final_response` | TEXT | Human-approved (or edited) response (nullable until approved) |
| `sent_at` | TIMESTAMP | Time response was sent (nullable until sent) |
| `created_at` | TIMESTAMP | Message receipt time |

### Relationships
- `orders.customer_id` → `customers.id` (many-to-one)
- `orders.product_id` → `stock.id` (many-to-one)
- `conversations.customer_id` → `customers.id` (many-to-one, nullable)

### Indexes
- `customers(phone)` — unique, for quick lookup by WhatsApp phone
- `orders(customer_id)` — for customer order history
- `orders(status)` — for filtering orders by status
- `stock(sku)` — for product lookup
- `conversations(customer_id)` — for conversation history
- `conversations(approval_status)` — for filtering pending messages

---

## AI Behavior Specification

### Intent Classification Rules

**Input**: Customer message (text)  
**Output**: `{ intent: enum, confidence: float }`

**Intent Categories**:
1. **order_lookup**: Customer asks about order status, tracking, or cancellation
   - Examples: "Where's my order?", "Can I cancel?", "When will it arrive?"
   
2. **stock_check**: Customer asks about availability, size, color, or specs
   - Examples: "Do you have XL in blue?", "Is this in stock?", "What colors are available?"
   
3. **complaint**: Customer reports issue, damage, or dissatisfaction
   - Examples: "I received the wrong item", "This is broken", "Poor quality"
   
4. **inquiry**: General question about policy, shipping, or business
   - Examples: "Do you ship internationally?", "What's your return policy?", "Delivery time?"
   
5. **other**: Unclear, spam, or out-of-scope
   - Examples: "Hello", "Random text", "Unclear request"

**Classification Confidence Threshold**: 
- Confidence > 0.7 → Proceed with lookup and draft generation
- Confidence ≤ 0.7 → Mark as `other` intent, set approval_status to `escalated`, NO lookup or draft generation; route to human reviewer only

**AI Constraints**:
- Use Gemini API with temperature 0.3 (low variance)
- Classify in < 2 seconds or timeout
- Return JSON with `intent` and `confidence` keys only
- No multi-intent classification; pick the single best fit

### Response Generation Rules

**Input**: 
- Classified intent
- Retrieved data (customer info, order status, or stock availability)
- Confidence score from classification

**Output**: 
- Draft response (2–3 sentences, max 500 tokens)
- Final response includes confidence score for human reviewer

**Response Guidelines by Intent**:

| Intent | Content | Tone | Example |
|--------|---------|------|---------|
| `order_lookup` | Order status, tracking link, delivery date | Professional, factual | "Your order #12345 is shipped and will arrive by May 15th. Tracking: [link]" |
| `stock_check` | Product availability, variants, restock date | Helpful, concise | "We have XL in blue (5 units available). Would you like me to place a hold?" |
| `complaint` | Escalate; no automated response | N/A | "[ESCALATION: Customer reported issue. Flagging for ops team review.]" |
| `inquiry` | Policy summary or standard response | Welcoming, brief | "We offer 14-day returns on unused items. Would you like more info?" |
| `other` | Polite request for clarification | Neutral | "I didn't understand your message. Could you provide more details?" |

**AI Limitations**:
- ✅ Read from database (queries only, no writes)
- ✅ Summarize factual data (order status, stock levels)
- ✅ Generate professional, courteous responses
- ❌ Make promises or guarantees not in database
- ❌ Commit to return dates, discounts, or refunds
- ❌ Write to database or approve orders autonomously
- ❌ Handle payment or sensitive financial information
- ❌ Resolve complaints without human involvement

**Draft Confidence Score**: 
- High confidence (0.8–1.0): AI is confident in response quality
- Medium confidence (0.6–0.8): Response is reasonable but may need tweaks
- Low confidence (< 0.6): Response is generic or uncertain; human should review carefully

---

## System Architecture (Logical)

### Services & Components

```
┌─────────────────────────────────────────────────────┐
│  Client Layer                                       │
├─────────────────────────────────────────────────────┤
│  - Web UI (Approval Interface)                      │
│  - WhatsApp Gateway (Webhook)                       │
└─────────────────────────────────────────────────────┘
                        ↓ REST APIs (JSON)
┌─────────────────────────────────────────────────────┐
│  API Gateway (FastAPI)                              │
│  - Route messages → AI Service                      │
│  - Route approvals → response dispatch              │
│  - Serve web UI                                     │
│  - Auth (API keys from .env)                        │
│  Endpoints:                                         │
│    POST   /api/messages        (ingest)             │
│    GET    /api/conversations   (list pending)       │
│    POST   /api/conversations/{id}/approve           │
│    GET    /api/health          (liveness)           │
└─────────────────────────────────────────────────────┘
         ↓                              ↓ (HTTP)
    ┌─────────────────────────────────────────────┐
    │  AI Service (FastAPI)                       │
    │  - Intent classification                    │
    │  - Response generation                      │
    │  Endpoints:                                 │
    │    POST   /api/classify      (Gemini call)  │
    │    POST   /api/draft         (Gemini call)  │
    └─────────────────────────────────────────────┘
         ↓ (HTTP)
    ┌──────────────────────────────────────────────────┐
    │  Order Service (FastAPI)                         │
    │  - Order lookup by ID or customer phone          │
    │  - Order status retrieval                        │
    │  Endpoints:                                      │
    │    GET    /api/orders/{order_id}                 │
    │    GET    /api/orders/by-phone/{phone}           │
    │    GET    /api/health                            │
    └──────────────────────────────────────────────────┘
         ↓ (HTTP)
    ┌──────────────────────────────────────────────────┐
    │  Stock Service (FastAPI)                         │
    │  - Stock availability lookup                     │
    │  - Product info retrieval                        │
    │  Endpoints:                                      │
    │    GET    /api/stock/{product_id}                │
    │    GET    /api/stock/search?q=blue-shirt         │
    │    GET    /api/health                            │
    └──────────────────────────────────────────────────┘
         ↓ (SQL)
┌─────────────────────────────────────────────────────┐
│  PostgreSQL Database                                │
│  - customers, orders, stock, conversations          │
│  - Indexes on phone, customer_id, status            │
└─────────────────────────────────────────────────────┘
```

### Communication Flow

**Incoming Message Sequence**:
1. WhatsApp → API Gateway (`/api/messages` POST)
2. Gateway stores message in DB, returns 200 OK (non-blocking)
3. Gateway calls AI Service (`/api/classify` POST)
4. AI Service calls Gemini API, returns intent + confidence
5. If confidence > 0.7:
   - Gateway calls Order Service or Stock Service (depending on intent)
   - Service queries PostgreSQL, returns data
   - Gateway calls AI Service (`/api/draft` POST with lookup data)
   - AI Service generates response, returns draft
6. Gateway stores classification, draft, and lookup data in DB
7. Web UI polls for pending conversations and displays draft for approval

**Approval Sequence**:
1. Ops team clicks Approve on web UI
2. UI calls API Gateway (`POST /api/conversations/{id}/approve`)
3. Gateway marks as `approved`, stores final response
4. Gateway sends response via WhatsApp (mock or real)
5. Gateway stores `sent_at` timestamp
6. UI refreshes to show next pending message

### Service Responsibilities (No Database Sharing)

| Service | Owns | Queries | Writes |
|---------|------|---------|--------|
| **API Gateway** | Message ingestion, routing, approval workflow | conversations (read/write), customers (read) | conversations, approvals |
| **AI Service** | Intent classification, response generation | None (stateless) | None |
| **Order Service** | Order data retrieval | orders, customers | None (read-only) |
| **Stock Service** | Stock data retrieval | stock | None (read-only) |

---

## Success Criteria

### Minimum Criteria (Demo Must-Have)
1. ✅ **Message Ingestion**: Customer message received and stored in PostgreSQL
2. ✅ **Intent Classification**: Gemini API classifies message into one of 5 categories with confidence > 0.7
3. ✅ **Order Lookup**: System retrieves order data (status, tracking, delivery date) accurately
4. ✅ **Stock Lookup**: System retrieves stock data (availability, variants) accurately
5. ✅ **Response Draft Generation**: Gemini API generates coherent, relevant draft response (2–3 sentences)
6. ✅ **Human Approval Interface**: Ops team can view draft, approve/reject/edit in web UI
7. ✅ **Response Logging**: Final response and approval status logged to PostgreSQL
8. ✅ **End-to-End Demo**: Complete flow executable in 2 minutes (message → approval → logged)
9. ✅ **Deterministic Behavior**: Same message produces same classification (confidence) every time
10. ✅ **Error Handling**: All errors return JSON with `status: "error"` and message, no 500 errors

### Nice-to-Have (If Time Permits)
- Multiple customer profiles in seed data for realistic demo
- Admin CLI to seed data, query logs, and reset conversations
- Response confidence score displayed in approval UI
- Template-based responses for common inquiries (faster approval)
- Conversation history UI (last 10 messages per customer)
- Metrics endpoint (`/api/metrics`) showing total messages, approval rate, avg response time

### Demo Success Checklist
- [ ] All 4 services running locally without errors
- [ ] PostgreSQL seeded with sample customers, orders, stock
- [ ] All REST endpoints return valid JSON
- [ ] Web UI loads without JavaScript errors
- [ ] Demo message flows through classification → lookup → draft → approval → logged
- [ ] Ops team can approve/reject/edit response in < 30 seconds
- [ ] No hardcoded secrets in code (all in `.env`)
- [ ] Demo script memorized and timed (target: 2–3 minutes)

---

## Assumptions & Notes

### Assumptions Made (Documented)
1. **WhatsApp Integration**: For MVP demo, messages are ingested via mock HTTP endpoint (can be upgraded to real WhatsApp API later)
2. **Customer Lookup**: Phone number is the unique identifier (assumption: one WhatsApp per customer)
3. **Deterministic Responses**: Using temperature 0.3 ensures reproducible AI behavior for demo purposes
4. **Simple Approval Workflow**: Single-step approval (approve/reject/edit) is sufficient; no multi-level escalation
5. **PostgreSQL Availability**: Assumes local PostgreSQL instance or Docker Compose available for team
6. **Gemini API Quota**: Assumes sufficient API quota for demo day (est. 100–200 API calls total)

### Constraints Acknowledged
- 8 hours per person (5 people = 40 total hours available)
- Max 4 backend services enforces strict scope
- REST-only architecture eliminates need for message brokers or async workers
- Human approval requirement means no fully autonomous operation (by design)

---

**Document Status**: Ready for Planning  
**Next Step**: Run `/speckit.plan` to create implementation roadmap  
**Associated Assets**: 
- Constitution: [.specify/memory/constitution.md](.specify/memory/constitution.md)
- Architecture Diagram: See System Architecture (Logical) section above
