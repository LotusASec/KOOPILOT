# Data Model: OpsAI MVP

**Phase**: Phase 1 (Design & Contracts)  
**Date**: 2026-05-11  
**Status**: ✅ Complete  

---

## Entity-Relationship Diagram (Logical)

```
┌──────────────────┐
│   customers      │
├──────────────────┤
│ id (PK)          │
│ phone (UNIQUE)   │
│ name             │
│ created_at       │
└──────────────────┘
        │
        │ 1:N
        ├─────────────────┐
        │                 │
        ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│    orders        │  │  conversations   │
├──────────────────┤  ├──────────────────┤
│ id (PK)          │  │ id (PK)          │
│ customer_id(FK)  │  │ customer_id(FK)  │
│ product_id(FK)   │  │ phone            │
│ quantity         │  │ message_text     │
│ status           │  │ intent_classified│
│ estimated_del... │  │ confidence_score │
│ tracking_url     │  │ lookup_data(JSON)│
│ created_at       │  │ draft_response   │
│ updated_at       │  │ draft_confidence │
└──────────────────┘  │ approval_status  │
        │             │ final_response   │
        │             │ sent_at          │
        │ N:1         │ created_at       │
        │             └──────────────────┘
        │
        ▼
┌──────────────────┐
│      stock       │
├──────────────────┤
│ id (PK)          │
│ product_name     │
│ sku              │
│ quantity_avail...│
│ size             │
│ color            │
│ created_at       │
│ updated_at       │
└──────────────────┘
```

---

## Entity Definitions

### 1. customers

**Purpose**: Store customer profiles for lookup and history.

| Field | Type | Constraints | Notes |
|-------|------|-----------|-------|
| `id` | UUID | PRIMARY KEY | Auto-generated; used internally |
| `phone` | VARCHAR(20) | UNIQUE, NOT NULL | WhatsApp phone number; unique identifier from user perspective |
| `name` | VARCHAR(255) | NOT NULL | Customer name (e.g., "John Doe") |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Account creation time (UTC) |

**Indexes**:
- `UNIQUE INDEX idx_customers_phone ON customers(phone)` — Quick lookup by phone number
- `INDEX idx_customers_created_at ON customers(created_at)` — For analytics/reporting (future)

**Constraints**:
- `phone` must be in E.164 format (e.g., `+1234567890`)
- `name` must not be empty

**Sample Data**:
```sql
INSERT INTO customers (phone, name) VALUES 
  ('+1234567890', 'Alice Johnson'),
  ('+0987654321', 'Bob Smith'),
  ('+1111111111', 'Charlie Brown');
```

---

### 2. orders

**Purpose**: Purchase history; used for "order_lookup" intent.

| Field | Type | Constraints | Notes |
|-------|------|-----------|-------|
| `id` | UUID | PRIMARY KEY | Auto-generated |
| `customer_id` | UUID | NOT NULL, FOREIGN KEY → customers(id) | Links to customer |
| `product_id` | UUID | NOT NULL, FOREIGN KEY → stock(id) | Links to product in inventory |
| `quantity` | INT | NOT NULL, CHECK > 0 | Number of units ordered |
| `status` | ENUM | NOT NULL, DEFAULT 'pending' | One of: `pending`, `processing`, `shipped`, `delivered`, `cancelled` |
| `estimated_delivery` | DATE | | Expected delivery (nullable; may not be set immediately) |
| `tracking_url` | TEXT | | Tracking link from logistics provider (nullable) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Order placement time |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last status change |

**ENUM Definition**:
```sql
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'shipped', 'delivered', 'cancelled');
```

**Indexes**:
- `INDEX idx_orders_customer_id ON orders(customer_id)` — Look up orders by customer
- `INDEX idx_orders_status ON orders(status)` — Filter orders by status
- `INDEX idx_orders_created_at ON orders(created_at)` — For sorting/analytics

**Constraints**:
- `quantity` must be > 0
- `customer_id` must exist in customers table
- `product_id` must exist in stock table

**Sample Data**:
```sql
INSERT INTO orders (customer_id, product_id, quantity, status, estimated_delivery, tracking_url) 
VALUES 
  (uuid_1, product_uuid_1, 2, 'shipped', '2026-05-15', 'https://track.example.com/abc123'),
  (uuid_2, product_uuid_2, 1, 'delivered', '2026-05-10', 'https://track.example.com/xyz789');
```

---

### 3. stock

**Purpose**: Product inventory; used for "stock_check" intent.

| Field | Type | Constraints | Notes |
|-------|------|-----------|-------|
| `id` | UUID | PRIMARY KEY | Auto-generated |
| `product_name` | VARCHAR(255) | NOT NULL | Product name (e.g., "Blue T-Shirt") |
| `sku` | VARCHAR(50) | UNIQUE, NOT NULL | Stock keeping unit; for internal reference |
| `quantity_available` | INT | NOT NULL, CHECK ≥ 0 | Units in stock (0 = out of stock) |
| `size` | VARCHAR(50) | | Size variant (e.g., "XL", "Medium") — nullable for non-sized products |
| `color` | VARCHAR(50) | | Color variant (e.g., "blue", "red") — nullable for non-colored products |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Product creation time |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Last inventory update |

**Indexes**:
- `UNIQUE INDEX idx_stock_sku ON stock(sku)` — Look up by SKU
- `INDEX idx_stock_product_name ON stock(product_name)` — Search by product name
- `INDEX idx_stock_color_size ON stock(color, size)` — Filter by variants

**Constraints**:
- `quantity_available` must be ≥ 0
- `sku` must be unique across all products
- `product_name` must not be empty

**Sample Data**:
```sql
INSERT INTO stock (product_name, sku, quantity_available, size, color) 
VALUES 
  ('T-Shirt', 'TSH-001-M-BLU', 10, 'Medium', 'blue'),
  ('T-Shirt', 'TSH-001-XL-BLU', 5, 'XL', 'blue'),
  ('Jeans', 'JNS-002-L-BLK', 8, 'Large', 'black');
```

---

### 4. conversations

**Purpose**: Message log with AI classification, draft response, and approval status. Immutable audit trail.

| Field | Type | Constraints | Notes |
|-------|------|-----------|-------|
| `id` | UUID | PRIMARY KEY | Auto-generated; conversation ID |
| `customer_id` | UUID | FOREIGN KEY → customers(id) | Nullable; may not match if customer is new/unknown |
| `phone` | VARCHAR(20) | NOT NULL | Sender phone number (raw, for traceability) |
| `message_text` | TEXT | NOT NULL | Original customer message |
| `intent_classified` | ENUM | NOT NULL | One of: `order_lookup`, `stock_check`, `complaint`, `inquiry`, `other` |
| `confidence_score` | NUMERIC(3,2) | NOT NULL | Classification confidence (0.00–1.00) |
| `lookup_data` | JSONB | | Retrieved data (order info, stock info, or null if not applicable) |
| `draft_response` | TEXT | | AI-generated response (nullable if escalated) |
| `draft_confidence` | NUMERIC(3,2) | | Confidence of response generation (0.00–1.00) |
| `approval_status` | ENUM | NOT NULL, DEFAULT 'pending' | One of: `pending`, `approved`, `rejected`, `edited`, `escalated` |
| `final_response` | TEXT | | Human-approved (or edited) response; nullable until approved |
| `sent_at` | TIMESTAMPTZ | | Timestamp when response was sent; nullable until sent |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Message receipt time |

**ENUM Definitions**:
```sql
CREATE TYPE intent_type AS ENUM ('order_lookup', 'stock_check', 'complaint', 'inquiry', 'other');
CREATE TYPE approval_status_enum AS ENUM ('pending', 'approved', 'rejected', 'edited', 'escalated');
```

**Indexes**:
- `INDEX idx_conversations_customer_id ON conversations(customer_id)` — Conversation history per customer
- `INDEX idx_conversations_approval_status ON conversations(approval_status)` — Find pending messages
- `INDEX idx_conversations_intent ON conversations(intent_classified)` — Filter by intent
- `INDEX idx_conversations_created_at ON conversations(created_at DESC)` — Recent messages first

**Constraints**:
- `confidence_score` must be between 0.00 and 1.00 (intent classification confidence)
- `draft_confidence` must be between 0.00 and 1.00 (response generation confidence; NULL if approval_status = 'escalated')
- `lookup_data` and `draft_response` are NULL if classification confidence ≤ 0.7 (escalated)
- `sent_at` is NULL until approval_status = 'approved' (set to CURRENT_TIMESTAMP on approval)
- `phone` must match E.164 format
- No updates allowed after creation (append-only table); corrections via new rows

**Sample Data**:
```sql
INSERT INTO conversations 
  (customer_id, phone, message_text, intent_classified, confidence_score, 
   lookup_data, draft_response, draft_confidence, approval_status) 
VALUES 
  (uuid_1, '+1234567890', 'Where is my order?', 'order_lookup', 0.92, 
   '{"order_id":"ORD-001", "status":"shipped"}', 
   'Your order is on the way!', 0.95, 'pending');
```

---

## Database Schema (DDL)

### Create Types

```sql
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'shipped', 'delivered', 'cancelled');
CREATE TYPE intent_type AS ENUM ('order_lookup', 'stock_check', 'complaint', 'inquiry', 'other');
CREATE TYPE approval_status_enum AS ENUM ('pending', 'approved', 'rejected', 'edited', 'escalated');
```

### Create Tables

```sql
-- Customers table
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone VARCHAR(20) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Stock table
CREATE TABLE stock (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_name VARCHAR(255) NOT NULL,
  sku VARCHAR(50) UNIQUE NOT NULL,
  quantity_available INT NOT NULL CHECK (quantity_available >= 0),
  size VARCHAR(50),
  color VARCHAR(50),
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
  product_id UUID NOT NULL REFERENCES stock(id) ON DELETE RESTRICT,
  quantity INT NOT NULL CHECK (quantity > 0),
  status order_status NOT NULL DEFAULT 'pending',
  estimated_delivery DATE,
  tracking_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table (append-only audit log)
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
  phone VARCHAR(20) NOT NULL,
  message_text TEXT NOT NULL,
  intent_classified intent_type NOT NULL,
  confidence_score NUMERIC(3,2) NOT NULL,
  lookup_data JSONB,
  draft_response TEXT,
  draft_confidence NUMERIC(3,2),
  approval_status approval_status_enum NOT NULL DEFAULT 'pending',
  final_response TEXT,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Create Indexes

```sql
-- Customer indexes
CREATE UNIQUE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_created_at ON customers(created_at);

-- Stock indexes
CREATE UNIQUE INDEX idx_stock_sku ON stock(sku);
CREATE INDEX idx_stock_product_name ON stock(product_name);
CREATE INDEX idx_stock_color_size ON stock(color, size);

-- Order indexes
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Conversation indexes
CREATE INDEX idx_conversations_customer_id ON conversations(customer_id);
CREATE INDEX idx_conversations_approval_status ON conversations(approval_status);
CREATE INDEX idx_conversations_intent ON conversations(intent_classified);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
```

---

## Data Relationships & Constraints

### Foreign Key Constraints
- `orders.customer_id` → `customers.id` (many-to-one)
  - Cascade: Restrict (prevent deleting customers with orders)
- `orders.product_id` → `stock.id` (many-to-one)
  - Cascade: Restrict (prevent deleting stock with orders)
- `conversations.customer_id` → `customers.id` (many-to-one)
  - Cascade: Set NULL (conversation can exist without customer link if customer ID unknown)

### Referential Integrity
- All foreign keys enforced at database level
- Prevents orphaned records (order without customer, etc.)
- Rollback on constraint violation

---

## Data Integrity Rules

### Audit Trail (conversations table)
- **Append-Only**: No updates or deletes allowed after creation
- **Immutable History**: Every message, classification, draft, and approval is recorded
- **Timestamp**: All records include `created_at` for timeline reconstruction

### Stock Inventory
- **No Overselling**: `quantity_available` always ≥ 0
- **No Negative Quantities**: Check constraint prevents accidental negative values
- **No Double-Counting**: Stock ID is unique; no duplicate SKUs

### Order Status Progression
- **Valid States**: Only enum values allowed (prevents typos)
- **No Rollback**: Status progresses forward (`pending` → `processing` → `shipped` → `delivered`)
- **Tracking Optional**: Order can be shipped without tracking URL (nullable)

---

## Migration Strategy

### Initial Setup (for demo)
```bash
# 1. Run DDL script
psql $DATABASE_URL < migrations/001_initial_schema.sql

# 2. Verify tables created
psql $DATABASE_URL -c "\dt"

# 3. Load seed data
psql $DATABASE_URL < seed_data/customers.sql
psql $DATABASE_URL < seed_data/stock.sql
psql $DATABASE_URL < seed_data/orders.sql
```

### Future Migrations (if needed)
- Use Alembic or manual SQL scripts in `migrations/versions/`
- Version naming: `002_add_product_category.sql`, etc.
- Always test migrations on local database before running on shared instance

---

## Performance Considerations

### Query Performance
- **Look Up Orders by Phone**: `customers(phone) → orders(customer_id)` — O(log n) with index
- **Find Pending Messages**: `conversations(approval_status)` index — O(log n)
- **Search Stock by Variant**: `stock(color, size)` composite index — O(log n)

### Typical Query Latencies
- Simple lookup (e.g., `SELECT * FROM customers WHERE phone = ?`) — < 1ms
- Foreign key join (e.g., `SELECT * FROM orders WHERE customer_id = ?`) — < 5ms
- Full conversation history (e.g., `SELECT * FROM conversations LIMIT 100`) — < 50ms

### Scaling Considerations (Out of Scope for MVP)
- No horizontal scaling (single PostgreSQL instance)
- No denormalization (normalized schema preferred for simplicity)
- No caching layer (direct queries fast enough for demo scale)

---

**Data Model Status**: ✅ Complete | **Ready for**: Contract definitions & implementation

**Version**: 1.0.0 | **Created**: 2026-05-11 | **Status**: Complete
