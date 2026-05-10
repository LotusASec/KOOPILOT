# AI Service Contract

**Service**: AI Service (Internal, Port 8001)  
**Purpose**: Intent classification, response generation via Gemini API  
**Responsibility**: Call Gemini API, return structured responses  

---

## Endpoints

### 1. POST /api/classify

**Purpose**: Classify customer message intent using Gemini API.

**Request**:
```json
{
  "message": "Can I cancel order #12345?"
}
```

**Request Schema**:
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `message` | string | Yes | Customer message (non-empty, < 1000 chars) |

**Response (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "intent": "order_lookup",
    "confidence": 0.92
  }
}
```

**Response Schema**:
| Field | Type | Notes |
|-------|------|-------|
| `status` | "success" | Fixed; always present |
| `data.intent` | enum | One of: order_lookup, stock_check, complaint, inquiry, other |
| `data.confidence` | number (0.0–1.0) | Confidence score from Gemini (higher = more confident) |

**Error Response (400 Bad Request)**:
```json
{
  "status": "error",
  "error": "Message cannot be empty"
}
```

**Error Response (500 Internal Server Error)**:
```json
{
  "status": "error",
  "error": "Gemini API timeout after 10 seconds"
}
```

**Error Cases**:
- `message` empty or > 1000 chars → 400
- Gemini API timeout (> 10s) → 500
- Gemini API rate limit → 500 (retry backoff handled internally)
- Invalid API key → 500

**Gemini Prompt Template**:
```
You are an e-commerce operations assistant. Classify the following customer message into one of these intents:
- order_lookup: Customer asks about order status, tracking, or cancellation
- stock_check: Customer asks about product availability, size, color, or specs
- complaint: Customer reports issue, damage, or dissatisfaction
- inquiry: Customer asks about policy, shipping, or business
- other: Unclear or out-of-scope

Message: "{message}"

Respond with JSON only:
{
  "intent": "<one of the above>",
  "confidence": <0.0-1.0>
}
```

**Gemini Configuration**:
- Model: gemini-pro (or latest)
- Temperature: 0.3 (low variance)
- Max tokens: 100
- Timeout: 10 seconds

**Notes**:
- Deterministic; same message should produce same classification
- Confidence > 0.7 → proceed to lookup; else → escalate to human
- Service should retry on transient Gemini failures (exponential backoff)

---

### 2. POST /api/generate

**Purpose**: Generate human-readable response using Gemini API based on intent and lookup data.

**Request**:
```json
{
  "intent": "order_lookup",
  "customer_name": "Alice Johnson",
  "lookup_data": {
    "order_id": "ORD-12345",
    "status": "shipped",
    "tracking_url": "https://track.example.com/abc123",
    "estimated_delivery": "2026-05-15"
  }
}
```

**Request Schema**:
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `intent` | enum | Yes | One of: order_lookup, stock_check, complaint, inquiry, other |
| `customer_name` | string | No | Customer name for personalization |
| `lookup_data` | object | No | Retrieved data (order, stock, or null for escalation) |

**Response (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "draft_response": "Hi Alice! Your order #ORD-12345 is on the way. Expected delivery: May 15th. Tracking: https://track.example.com/abc123",
    "confidence": 0.95
  }
}
```

**Response Schema**:
| Field | Type | Notes |
|-------|------|-------|
| `status` | "success" | Fixed |
| `data.draft_response` | string | AI-generated response (2–3 sentences, < 500 tokens) |
| `data.confidence` | number (0.0–1.0) | Confidence of response quality |

**Error Response (400 Bad Request)**:
```json
{
  "status": "error",
  "error": "Invalid intent. Expected: order_lookup, stock_check, complaint, inquiry, or other"
}
```

**Error Response (500 Internal Server Error)**:
```json
{
  "status": "error",
  "error": "Gemini API unavailable"
}
```

**Error Cases**:
- Invalid intent → 400
- Gemini API timeout → 500
- Gemini API error → 500

**Gemini Prompt Template** (by intent):

**Order Lookup**:
```
Generate a friendly, concise customer response (2-3 sentences) about their order status.
Include tracking link if available. Do NOT make promises about delivery times not in the data.

Customer: {customer_name}
Order ID: {order_id}
Status: {status}
Tracking: {tracking_url}
Est. Delivery: {estimated_delivery}

Response:
```

**Stock Check**:
```
Generate a friendly, concise response about product availability.
If available, mention quantity and variants. If out of stock, suggest checking back later.

Product: {product_name}
Available Qty: {quantity_available}
Size: {size}
Color: {color}

Response:
```

**Complaint**:
```
Generate a compassionate escalation message. Do NOT attempt to resolve. 
Acknowledge the issue and assure the customer their concern will be reviewed.

Issue: [User's complaint summary]

Response:
```

**Inquiry**:
```
Generate a helpful response about e-commerce policies or business info.
Keep it brief and direct.

Question: [User's question summary]

Response:
```

**Other (Escalation)**:
```
Generate a polite message asking for clarification.

Response:
```

**Gemini Configuration**:
- Model: gemini-pro
- Temperature: 0.3 (low variance, deterministic)
- Max tokens: 500
- Timeout: 10 seconds

**Notes**:
- Response must be concise (2–3 sentences)
- No marketing fluff or false promises
- Confidence > 0.8 = high quality; 0.6–0.8 = medium; < 0.6 = needs review
- Service should log all requests/responses for debugging

---

### 3. GET /health

**Purpose**: Liveness check.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "service": "ai-service",
  "gemini_available": true,
  "timestamp": "2026-05-11T14:30:00Z"
}
```

**Notes**:
- Optionally check Gemini API connectivity
- Return 200 if AI Service is running

---

## Error Handling

### Standard Error Response Format

```json
{
  "status": "error",
  "error": "Human-readable error message"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Classification or generation complete |
| 400 | Bad Request | Invalid intent, empty message |
| 500 | Internal Server Error | Gemini API timeout, network error |

---

## Timeout & Retry

| Endpoint | Timeout | Retry Strategy |
|----------|---------|-----------------|
| POST /api/classify | 10 seconds | Exponential backoff (max 2 retries) |
| POST /api/generate | 10 seconds | Exponential backoff (max 2 retries) |

If all retries fail, return 500 with error message.

---

## Rate Limiting (Optional for MVP)

Not required for hackathon demo, but consider for future:
- Gemini API calls: max 60/min (check quota)
- Alert if approaching quota
- Fail gracefully if quota exceeded

---

**Contract Version**: 1.0.0 | **Status**: ✅ Ready for Implementation
