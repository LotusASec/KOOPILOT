# Quickstart: OpsAI MVP Local Development

**Phase**: Phase 1 (Design & Contracts)  
**Date**: 2026-05-11  
**Status**: ✅ Ready for Implementation  

---

## Prerequisites

### System Requirements
- macOS 10.15+, Linux (Ubuntu 20.04+), or Windows 10+ (WSL2)
- CPU: 2+ cores
- RAM: 4GB+ available
- Disk: 5GB free

### Software Requirements
- Python 3.11+ (`python --version`)
- PostgreSQL 13+ (via Docker or native install)
- Docker & Docker Compose (recommended for PostgreSQL)
- Git 2.30+
- Bash shell (for helper scripts)

### API Keys
- Google Gemini API key (from [Google AI Studio](https://makersuite.google.com/app/apikey))

---

## Option A: Docker Compose (Recommended for Hackathon)

### Step 1: Setup Docker & PostgreSQL

```bash
# Install Docker Desktop (https://www.docker.com/products/docker-desktop)
# Then verify installation
docker --version
docker-compose --version
```

### Step 2: Clone & Navigate to Project

```bash
git clone <repo-url>
cd koopilot
```

### Step 3: Start PostgreSQL & Services

```bash
# Start PostgreSQL container
docker-compose up -d postgresql

# Verify PostgreSQL is running
docker-compose ps
# Expected: postgresql container status "Up"

# Wait 5 seconds for PostgreSQL to be ready
sleep 5
```

### Step 4: Initialize Database Schema

```bash
# Connect to PostgreSQL and run DDL
docker-compose exec postgresql psql -U opsai -d opsai_db -f /migrations/001_initial_schema.sql

# Verify tables created
docker-compose exec postgresql psql -U opsai -d opsai_db -c "\dt"
```

### Step 5: Seed Test Data

```bash
# Load sample customers, orders, stock
docker-compose exec postgresql psql -U opsai -d opsai_db < backend/seed_data/customers.sql
docker-compose exec postgresql psql -U opsai -d opsai_db < backend/seed_data/orders.sql
docker-compose exec postgresql psql -U opsai -d opsai_db < backend/seed_data/stock.sql

# Verify data loaded
docker-compose exec postgresql psql -U opsai -d opsai_db -c "SELECT COUNT(*) FROM customers;"
```

### Step 6: Create `.env` File

```bash
# Copy template
cp backend/.env.example backend/.env

# Edit .env with your Gemini API key
nano backend/.env
# Or use your editor of choice

# Expected content:
# GEMINI_API_KEY=your-api-key-here
# DATABASE_URL=postgresql://opsai:opsai@postgresql:5432/opsai_db
# API_GATEWAY_PORT=8000
# AI_SERVICE_PORT=8001
# ORDER_SERVICE_PORT=8002
# STOCK_SERVICE_PORT=8003
```

### Step 7: Start Backend Services

```bash
# Build Docker images for services (one-time)
docker-compose build

# Start all services
docker-compose up -d api-gateway ai-service order-service stock-service

# Verify all services running
docker-compose ps
# Expected: all service containers status "Up"

# Check logs
docker-compose logs -f api-gateway
```

### Step 8: Test Endpoints

```bash
# Test API Gateway health
curl http://localhost:8000/health

# Test message ingestion
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "message_text": "Where is my order?"
  }'

# View pending conversations
curl http://localhost:8000/api/conversations?status=pending
```

### Step 9: Open Web UI

```bash
# Open browser to approval interface
open http://localhost:8000/ui
# or on Linux:
xdg-open http://localhost:8000/ui
```

### Step 10: Run End-to-End Test

```bash
# Run test suite
cd backend
pytest tests/integration/test_end_to_end.py -v

# Expected: all tests pass
```

---

## Option B: Native PostgreSQL + Manual Service Startup

### Step 1: Install PostgreSQL (macOS)

```bash
# Using Homebrew
brew install postgresql
brew services start postgresql

# Verify
psql --version
psql -U postgres -c "SELECT version();"
```

### Step 1: Install PostgreSQL (Linux)

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Start service
sudo systemctl start postgresql

# Verify
sudo -u postgres psql -c "SELECT version();"
```

### Step 2: Create Database & User

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql:
CREATE USER opsai WITH PASSWORD 'opsai';
CREATE DATABASE opsai_db OWNER opsai;
GRANT ALL PRIVILEGES ON DATABASE opsai_db TO opsai;
\quit
```

### Step 3: Initialize Schema

```bash
# Run DDL
psql -U opsai -d opsai_db -f backend/migrations/001_initial_schema.sql

# Verify
psql -U opsai -d opsai_db -c "\dt"
```

### Step 4: Seed Data

```bash
psql -U opsai -d opsai_db < backend/seed_data/customers.sql
psql -U opsai -d opsai_db < backend/seed_data/orders.sql
psql -U opsai -d opsai_db < backend/seed_data/stock.sql
```

### Step 5: Setup Python Environment

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 6: Create `.env` File

```bash
cp .env.example .env
nano .env
# Add your Gemini API key and database credentials
```

### Step 7: Start Services (4 terminals)

**Terminal 1 – API Gateway**:
```bash
cd backend
source venv/bin/activate
python -m uvicorn services.api_gateway.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 – AI Service**:
```bash
cd backend
source venv/bin/activate
python -m uvicorn services.ai_service.main:app --host 0.0.0.0 --port 8001
```

**Terminal 3 – Order Service**:
```bash
cd backend
source venv/bin/activate
python -m uvicorn services.order_service.main:app --host 0.0.0.0 --port 8002
```

**Terminal 4 – Stock Service**:
```bash
cd backend
source venv/bin/activate
python -m uvicorn services.stock_service.main:app --host 0.0.0.0 --port 8003
```

### Step 8: Test & Demo

Same as Option A, Step 8–10.

---

## Helper Script (Optional)

```bash
#!/bin/bash
# backend/run_services.sh

set -e

echo "Starting OpsAI services..."

# Activate venv
source venv/bin/activate

# Start services in background
python -m uvicorn services.api_gateway.main:app --port 8000 &
python -m uvicorn services.ai_service.main:app --port 8001 &
python -m uvicorn services.order_service.main:app --port 8002 &
python -m uvicorn services.stock_service.main:app --port 8003 &

echo "All services started. Open http://localhost:8000/ui"
wait
```

Usage:
```bash
chmod +x backend/run_services.sh
./backend/run_services.sh
```

---

## End-to-End Demo Flow

### 1. Send Message

```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1234567890",
    "message_text": "Do you have size XL in blue?"
  }'
```

Response:
```json
{
  "status": "success",
  "data": {
    "conversation_id": "uuid-xyz",
    "intent": "stock_check",
    "confidence": 0.89,
    "draft_response": "Yes, we have XL in blue with 5 units available.",
    "approval_pending": true
  }
}
```

### 2. View Pending Messages (Web UI)

```
Navigate to: http://localhost:8000/ui
- See pending message
- See classified intent & confidence
- See AI draft response
- See lookup data (stock info)
```

### 3. Approve Response

Click "Approve" button in UI. Response saved and sent (logged as "sent").

### 4. Query Conversation History

```bash
curl http://localhost:8000/api/conversations?status=approved&limit=5
```

---

## Troubleshooting

### "Connection refused" on port 8000

```bash
# Check if service is running
lsof -i :8000

# Kill any existing process on port 8000
kill -9 <PID>

# Restart service
python -m uvicorn services.api_gateway.main:app --port 8000
```

### "PostgreSQL connection error"

```bash
# Check if PostgreSQL is running
# Docker:
docker-compose ps postgresql

# Native:
psql -U opsai -d opsai_db -c "SELECT 1"

# If connection fails, verify .env DATABASE_URL
cat backend/.env | grep DATABASE_URL
```

### "Gemini API timeout"

```bash
# Check API key in .env
echo $GEMINI_API_KEY

# Test Gemini connectivity manually
# (see Python snippet below)
python -c "
from google.generativeai import GenerativeModel
model = GenerativeModel('gemini-pro')
response = model.generate_content('Hello')
print(response.text)
"
```

### "Table not found" error

```bash
# Verify schema was created
psql -U opsai -d opsai_db -c "\dt"

# If tables missing, re-run DDL
psql -U opsai -d opsai_db -f backend/migrations/001_initial_schema.sql
```

---

## Next Steps

1. ✅ All services running? → Proceed to `/speckit.tasks` to generate task list
2. ✅ End-to-end flow works? → Run integration tests: `pytest tests/integration/ -v`
3. ✅ Ready to demo? → Memorize demo script (message → approval → logged)

---

## Useful Commands

```bash
# View API Gateway logs
docker-compose logs -f api-gateway
# or
tail -f backend/logs/api-gateway.log

# Connect to PostgreSQL directly
docker-compose exec postgresql psql -U opsai -d opsai_db
# or (native)
psql -U opsai -d opsai_db

# View all conversations
psql -U opsai -d opsai_db -c "SELECT * FROM conversations ORDER BY created_at DESC LIMIT 10;"

# Reset database (delete all data)
psql -U opsai -d opsai_db -c "DELETE FROM conversations; DELETE FROM orders; DELETE FROM stock; DELETE FROM customers;"

# Run tests
cd backend && pytest tests/ -v

# Check Python dependencies
pip list

# Update .env after changes
source .env && echo "Environment loaded"
```

---

**Quickstart Status**: ✅ Complete | **Time to Full Setup**: 10–15 minutes (Docker) or 15–20 minutes (native)

**Ready to Demo**: Once all services are running and you can hit http://localhost:8000/ui without errors.

---

**Version**: 1.0.0 | **Created**: 2026-05-11 | **Status**: Complete
