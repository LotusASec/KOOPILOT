# Stock Service Contract

**Service**: Stock Service (Internal, Port 8003)  
**Purpose**: Stock availability lookup and search  
**Responsibility**: Query PostgreSQL stock table, return product availability data  

---

## Endpoints

### 1. GET /api/stock/{product_id}

**Purpose**: Retrieve stock details by product ID.

**Path Parameters**:
| Param | Type | Notes |
|-------|------|-------|
| `product_id` | UUID | Stock/Product ID |

**Request Example**:
```
GET /api/stock/660f9511-f39d-42e4-b917-557766551111
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "data": {
    "product_id": "660f9511-f39d-42e4-b917-557766551111",
    "product_name": "Blue T-Shirt",
    "sku": "TSH-001-M-BLU",
    "quantity_available": 10,
    "size": "Medium",
    "color": "blue",
    "in_stock": true,
    "created_at": "2026-05-01T08:00:00Z",
    "updated_at": "2026-05-11T10:00:00Z"
  }
}
```

**Response Schema**:
| Field | Type | Notes |
|-------|------|-------|
| `status` | "success" | Fixed |
| `data.product_id` | UUID | Product ID |
| `data.product_name` | string | Product name |
| `data.sku` | string | Stock keeping unit |
| `data.quantity_available` | integer | Units in stock (≥ 0) |
| `data.size` | string | Size variant or null |
| `data.color` | string | Color variant or null |
| `data.in_stock` | boolean | True if quantity_available > 0 |
| `data.created_at` | string | ISO 8601 timestamp |
| `data.updated_at` | string | ISO 8601 timestamp |

**Error Response (404 Not Found)**:
```json
{
  "status": "error",
  "error": "Product not found: 660f9511-f39d-42e4-b917-557766551111"
}
```

**Error Response (400 Bad Request)**:
```json
{
  "status": "error",
  "error": "Invalid product_id format. Expected UUID."
}
```

**Error Cases**:
- product_id not valid UUID → 400
- product_id doesn't exist → 404
- Database error → 500

**Notes**:
- Fast lookup via index on stock(id)
- `in_stock` boolean is derived from quantity_available > 0
- Expected latency: < 5ms

---

### 2. GET /api/stock/search

**Purpose**: Search stock by product name, SKU, or variant (size/color).

**Query Parameters**:
| Param | Type | Notes |
|-------|------|-------|
| `q` | string | Search query (product name or SKU, case-insensitive) |
| `size` | string | Optional filter by size |
| `color` | string | Optional filter by color |
| `in_stock_only` | boolean | If true, return only in-stock items |
| `limit` | integer | Max results (default 10, max 50) |

**Request Example**:
```
GET /api/stock/search?q=blue&color=blue&in_stock_only=true&limit=5
```

**Response (200 OK)**:
```json
{
  "status": "success",
  "data": [
    {
      "product_id": "660f9511-f39d-42e4-b917-557766551111",
      "product_name": "Blue T-Shirt",
      "sku": "TSH-001-M-BLU",
      "quantity_available": 10,
      "size": "Medium",
      "color": "blue",
      "in_stock": true
    },
    {
      "product_id": "660f9511-f39d-42e4-b917-557766551112",
      "product_name": "Blue T-Shirt",
      "sku": "TSH-001-XL-BLU",
      "quantity_available": 5,
      "size": "XL",
      "color": "blue",
      "in_stock": true
    }
  ]
}
```

**Response Schema**:
- Array of product objects (same format as `/api/stock/{product_id}`)
- Ordered by quantity_available DESC (most stock first)

**Error Response (400 Bad Request)**:
```json
{
  "status": "error",
  "error": "Search query 'q' is required"
}
```

**Error Cases**:
- `q` parameter missing → 400
- `limit` > 50 → 400 (capped at 50)
- Database error → 500

**Notes**:
- Searches product_name and sku (case-insensitive substring match)
- Optional size/color filters for variant-specific searches
- in_stock_only filter excludes quantity_available = 0
- Expected latency: < 20ms (may scan multiple rows if search is broad)

---

### 3. GET /health

**Purpose**: Liveness check.

**Response (200 OK)**:
```json
{
  "status": "healthy",
  "service": "stock-service",
  "timestamp": "2026-05-11T14:30:00Z"
}
```

**Notes**:
- Return 200 if Stock Service is running

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
| 200 | Success | Product found and returned |
| 400 | Bad Request | Invalid UUID, missing search query, limit too high |
| 404 | Not Found | Product doesn't exist |
| 500 | Internal Server Error | Database connection error |

---

## Performance Characteristics

| Endpoint | Expected Latency | Notes |
|----------|-----------------|-------|
| GET /api/stock/{product_id} | < 5ms | Indexed lookup by UUID |
| GET /api/stock/search | 10–50ms | Substring search; can scan multiple rows |
| GET /health | < 1ms | No database query |

---

## Query Examples (for debugging)

```sql
-- Look up product by ID
SELECT * FROM stock WHERE id = '660f9511-f39d-42e4-b917-557766551111';

-- Search by product name and color
SELECT * FROM stock 
WHERE LOWER(product_name) LIKE LOWER('%blue%') 
  AND color = 'blue'
  AND quantity_available > 0
ORDER BY quantity_available DESC
LIMIT 10;

-- Search by SKU
SELECT * FROM stock 
WHERE LOWER(sku) LIKE LOWER('%TSH-001%')
ORDER BY quantity_available DESC;
```

---

## Data Consistency

- Stock quantities are updated immediately when inventory changes (e.g., order placed)
- No eventual consistency; reads reflect current state
- For MVP, assume manual stock updates or basic integration with inventory system

---

**Contract Version**: 1.0.0 | **Status**: ✅ Ready for Implementation
