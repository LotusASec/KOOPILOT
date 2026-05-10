# Order Service Contract

**Service**: Order Service (Internal, Port 8002)  
**Purpose**: Order lookup and retrieval  
**Responsibility**: Query PostgreSQL orders/customers table, return structured order data  

---

## Endpoints

### 1. GET /api/orders/{order_id}

**Purpose**: Retrieve order details by order ID.

**Path Parameters**:
| Param | Type | Notes |
|-------|------|-------|
| `order_id` | UUID | Order ID (e.g., "550e8400-e29b-41d4-a716-446655440000") |

**Request Example**:
```
GET /api/orders/550e8400-e29b-41d4-a716-446655440000
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "order_id": "550e8400-e29b-41d4-a716-446655440000",
    "customer_name": "Alice Johnson",
    "product_name": "Blue T-Shirt",
    "quantity": 2,
    "status": "shipped",
    "estimated_delivery": "2026-05-15",
    "tracking_url": "https://track.example.com/abc123",
    "created_at": "2026-05-10T10:00:00Z",
    "updated_at": "2026-05-11T14:00:00Z"
  }
}
```

**Response Schema**:
| Field | Type | Notes |
|-------|------|-------|
| `status` | "success" | Fixed |
| `data.order_id` | UUID | Order ID |
| `data.customer_name` | string | Customer name (from customers table) |
| `data.product_name` | string | Product name (from stock table) |
| `data.quantity` | integer | Number of units |
| `data.status` | string | One of: pending, processing, shipped, delivered, cancelled |
| `data.estimated_delivery` | string | Date (YYYY-MM-DD format) or null |
| `data.tracking_url` | string | Tracking link or null |
| `data.created_at` | string | ISO 8601 timestamp |
| `data.updated_at` | string | ISO 8601 timestamp |

**Error Response (404 Not Found)**:
```json
{
  "status": "error",
  "error": "Order not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (400 Bad Request)**:
```json
{
  "status": "error",
  "error": "Invalid order_id format. Expected UUID."
}
```

**Error Cases**:
- order_id not in valid UUID format → 400
- order_id doesn't exist in database → 404
- Database connection error → 500

**Notes**:
- Fast lookup via index on orders(id)
- Includes joined data from customers and stock tables
- Expected latency: < 5ms

---

### 2. GET /api/orders/by-phone/{phone}

**Purpose**: Retrieve most recent order(s) for a customer by phone number.

**Path Parameters**:
| Param | Type | Notes |
|-------|------|-------|
| `phone` | string | E.164 format (e.g., "+1234567890") |

**Query Parameters**:
| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `limit` | integer | 1 | Max orders to return (1–10) |

**Request Example**:
```
GET /api/orders/by-phone/+1234567890?limit=3
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "data": [
    {
      "order_id": "550e8400-e29b-41d4-a716-446655440000",
      "customer_name": "Alice Johnson",
      "product_name": "Blue T-Shirt",
      "quantity": 2,
      "status": "shipped",
      "estimated_delivery": "2026-05-15",
      "tracking_url": "https://track.example.com/abc123",
      "created_at": "2026-05-10T10:00:00Z"
    }
  ]
}
```

**Response Schema**:
- Same as `/api/orders/{order_id}`, but returns array
- Ordered by `created_at DESC` (most recent first)

**Error Response (404 Not Found)**:
```json
{
  "status": "error",
  "error": "No customer found with phone: +1234567890"
}
```

**Error Response (400 Bad Request)**:
```json
{
  "status": "error",
  "error": "Invalid phone format. Expected E.164: +1234567890"
}
```

**Error Cases**:
- phone not in E.164 format → 400
- phone doesn't exist in customers table → 404
- Database error → 500

**Notes**:
- Fast lookup via index on customers(phone)
- Default returns 1 most recent order; specify ?limit to get more
- Useful for quick order status checks without order ID

---

### 3. GET /health

**Purpose**: Liveness check.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "service": "order-service",
  "timestamp": "2026-05-11T14:30:00Z"
}
```

**Notes**:
- Return 200 if Order Service is running

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
| 200 | Success | Order found and returned |
| 400 | Bad Request | Invalid phone format, invalid UUID |
| 404 | Not Found | Order or customer doesn't exist |
| 500 | Internal Server Error | Database connection error |

---

## Performance Characteristics

| Endpoint | Expected Latency | Notes |
|----------|-----------------|-------|
| GET /api/orders/{order_id} | < 5ms | Indexed lookup by UUID |
| GET /api/orders/by-phone/{phone} | < 5ms | Indexed lookup by phone, then foreign key join |
| GET /health | < 1ms | No database query |

---

## Query Examples (for debugging)

```sql
-- Look up order by ID
SELECT o.*, c.name, s.product_name 
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN stock s ON o.product_id = s.id
WHERE o.id = '550e8400-e29b-41d4-a716-446655440000';

-- Look up orders by phone
SELECT o.*, c.name, s.product_name 
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN stock s ON o.product_id = s.id
WHERE c.phone = '+1234567890'
ORDER BY o.created_at DESC
LIMIT 3;
```

---

**Contract Version**: 1.0.0 | **Status**: ✅ Ready for Implementation
