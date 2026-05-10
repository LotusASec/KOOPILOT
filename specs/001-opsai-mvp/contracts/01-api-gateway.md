# API Gateway Contract

**Service**: API Gateway (REST API, Port 8000)  
**Purpose**: Central routing, message ingestion, approval workflow, web UI serving  
**Responsibility**: Orchestrate AI Service, Order Service, Stock Service; manage conversations table  

---

## Endpoints

### 1. POST /api/messages

**Purpose**: Ingest incoming WhatsApp messages and start classification workflow.

**Request**:
```json
{
  "phone": "+1234567890",
  "message_text": "Can I cancel order #12345?"
}
```

**Request Schema**:
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `phone` | string | Yes | E.164 format; e.g., "+1234567890" |
| `message_text` | string | Yes | Customer message (non-empty, < 1000 chars) |

**Response (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "conversation_id": "uuid-12345",
    "intent": "order_lookup",
    "confidence": 0.92,
    "draft_response": "Your order #12345 is en route.",
    "approval_pending": true
  }
}
```

**Response Schema (200)**:
| Field | Type | Notes |
|-------|------|-------|
| `status` | "success" | Fixed; indicates success |
| `data.conversation_id` | UUID | Unique conversation ID for tracking |
| `data.intent` | enum | One of: order_lookup, stock_check, complaint, inquiry, other |
| `data.confidence` | number (0.0–1.0) | Classification confidence from AI Service |
| `data.draft_response` | string | AI-generated response (or escalation message if intent = complaint) |
| `data.approval_pending` | boolean | True if waiting for human approval |

**Error Response (400 Bad Request)**:
```json
{
  "status": "error",
  "error": "Invalid phone format. Expected E.164: +1234567890"
}
```

**Error Response (500 Internal Server Error)**:
```json
{
  "status": "error",
  "error": "Gemini API unavailable. Please try again."
}
```

**Error Cases**:
- `phone` not in E.164 format → 400
- `message_text` empty or > 1000 chars → 400
- AI Service timeout → 500 (Gemini API error)
- Database error → 500

**Flow**:
1. Validate request (phone, message_text)
2. Look up customer by phone (may not exist)
3. Call AI Service `POST /api/classify` with message_text
4. If confidence > 0.7:
   - Call Order Service or Stock Service (based on intent)
   - Call AI Service `POST /api/generate` with intent + lookup data
   - Store conversation in PostgreSQL with draft
5. Return 200 with draft response (waiting for approval)

**Notes**:
- Non-blocking; returns immediately after storing draft
- If AI Service timeout, return generic escalation message
- Conversation is stored even if lookup fails (for audit trail)

---

### 2. GET /api/conversations

**Purpose**: Retrieve pending messages for human review.

**Query Parameters**:
| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `status` | string | "pending" | Filter by approval_status (pending, approved, rejected, edited) |
| `limit` | integer | 50 | Max results to return |
| `offset` | integer | 0 | Pagination offset |

**Request Example**:
```
GET /api/conversations?status=pending&limit=10&offset=0
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "uuid-1",
      "phone": "+1234567890",
      "message_text": "Can I cancel order #12345?",
      "intent": "order_lookup",
      "confidence": 0.92,
      "lookup_data": {
        "order_id": "ORD-12345",
        "status": "shipped",
        "tracking_url": "https://..."
      },
      "draft_response": "Your order is on the way. Tracking: https://...",
      "draft_confidence": 0.95,
      "created_at": "2026-05-11T14:30:00Z"
    }
  ],
  "pagination": {
    "total": 5,
    "limit": 10,
    "offset": 0
  }
}
```

**Response Schema**:
| Field | Type | Notes |
|-------|------|-------|
| `status` | "success" | Fixed |
| `data` | array | List of conversations |
| `data[].id` | UUID | Conversation ID |
| `data[].phone` | string | Customer phone |
| `data[].message_text` | string | Original message |
| `data[].intent` | enum | Classification result |
| `data[].confidence` | number | Classification confidence |
| `data[].lookup_data` | object | Retrieved order/stock data (or null) |
| `data[].draft_response` | string | AI-generated response |
| `data[].draft_confidence` | number | Response generation confidence |
| `data[].created_at` | string | ISO 8601 timestamp |
| `pagination.total` | integer | Total matching conversations |
| `pagination.limit` | integer | Limit applied |
| `pagination.offset` | integer | Offset applied |

**Error Response (400 Bad Request)**:
```json
{
  "status": "error",
  "error": "Invalid limit. Max 250."
}
```

**Notes**:
- Default ordering: `created_at DESC` (newest first)
- Polling interval recommended: 2 seconds (for UI auto-refresh)

---

### 3. POST /api/conversations/{id}/approve

**Purpose**: Human approval/rejection/editing of AI-generated response.

**Path Parameters**:
| Param | Type | Notes |
|-------|------|-------|
| `id` | UUID | Conversation ID |

**Request**:
```json
{
  "action": "approve",
  "final_response": "Your order is on the way. Tracking: https://track.example.com/abc123"
}
```

**Request Schema**:
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `action` | enum | Yes | One of: approve, reject, edit |
| `final_response` | string | No | For "approve" or "edit" actions (human-edited response) |

**Response (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "conversation_id": "uuid-1",
    "approval_status": "approved",
    "final_response": "Your order is on the way. Tracking: https://...",
    "sent_at": "2026-05-11T14:32:15Z"
  }
}
```

**Response Schema**:
| Field | Type | Notes |
|-------|------|-------|
| `status` | "success" | Fixed |
| `data.conversation_id` | UUID | Conversation ID |
| `data.approval_status` | string | "approved", "rejected", or "edited" |
| `data.final_response` | string | Final response sent to customer (for "approve"/"edit" only) |
| `data.sent_at` | string | Timestamp when response was dispatched |

**Error Response (404 Not Found)**:
```json
{
  "status": "error",
  "error": "Conversation not found: uuid-1"
}
```

**Error Response (400 Bad Request)**:
```json
{
  "status": "error",
  "error": "final_response required for 'approve' action"
}
```

**Error Cases**:
- Conversation ID not found → 404
- Action = "approve" but no final_response → 400
- Conversation already approved → 400 (idempotent check)

**Flow**:
1. Validate conversation exists
2. Validate action (approve, reject, edit)
3. If action = "approve" or "edit":
   - Store final_response
   - Mock WhatsApp dispatch (or real API call)
   - Store sent_at timestamp
   - Mark approval_status as "approved"
4. If action = "reject":
   - Mark approval_status as "rejected"
   - Escalate to human team (flag for manual response)
5. Return 200 with result

**Notes**:
- Idempotent: approving twice returns same result
- If WhatsApp dispatch fails, mark as sent_at anyway (logged for audit)

---

### 4. GET /health

**Purpose**: Liveness check; used by load balancer or monitoring.

**Request Example**:
```
GET /health
```

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "timestamp": "2026-05-11T14:30:00Z"
}
```

**Notes**:
- Always returns 200 if API Gateway is running
- No database dependency check (assume PostgreSQL is up if queries work)

---

### 5. GET /ui

**Purpose**: Serve web UI for human approval interface.

**Response**: HTML page with approval form and JavaScript

**Notes**:
- Static files served from `web_ui/` directory
- No authentication required
- CORS allowed for localhost:*

---

## Error Handling

### Standard Error Response Format

All errors follow this schema:
```json
{
  "status": "error",
  "error": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Message accepted, pending approval |
| 400 | Bad Request | Invalid phone format, missing field |
| 404 | Not Found | Conversation ID doesn't exist |
| 500 | Internal Server Error | Gemini API timeout, database error |

### No Other Status Codes

API Gateway MUST NOT return:
- 201 Created
- 204 No Content
- 301/302 Redirects
- 503 Service Unavailable (return 500 instead)

---

## Request/Response Timeout

| Endpoint | Timeout | Behavior |
|----------|---------|----------|
| POST /api/messages | 10 seconds | If AI Service times out, return 500 |
| GET /api/conversations | 5 seconds | If database slow, return 500 |
| POST /api/conversations/{id}/approve | 5 seconds | If database/WhatsApp times out, return 500 |

---

**Contract Version**: 1.0.0 | **Status**: ✅ Ready for Implementation
