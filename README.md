# AI Cost Monitoring Platform API

A production-ready FastAPI REST API for B2B AI cost monitoring with secure JWT authentication and strict tenant data isolation.

## Features

- **JWT Authentication**: Stateless Bearer token authentication using PyJWT
- **Password Security**: Bcrypt password hashing via passlib
- **Tenant Isolation**: All database queries strictly filter by authenticated organization ID
- **API Key Encryption**: Fernet symmetric encryption for storing provider API keys
- **OpenAPI Documentation**: Auto-generated Swagger UI at `/docs`
- **Metrics Analytics**: Cost breakdown, summary, and leak detection insights

## Architecture

```
app/
├── api/
│   ├── __init__.py
│   ├── schemas.py              # Pydantic models for request/response validation
│   ├── dependencies.py         # Authentication dependency (get_current_org)
│   └── v1/
│       ├── __init__.py
│       ├── auth.py             # Signup and API key management endpoints
│       └── metrics.py          # Metrics summary, breakdown, and leak detector
├── core/
│   ├── __init__.py
│   ├── config.py              # Environment-based configuration
│   ├── database.py            # SQLAlchemy session management
│   ├── auth.py                # JWT token utilities and password hashing
│   └── security.py            # Fernet encryption for API keys
├── models/
│   ├── __init__.py
│   ├── organization.py        # Organization model with auth fields
│   └── usage_cache.py         # Hourly/daily usage cache model
└── main.py                    # FastAPI application entry point
```

## Getting Started

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

### Step 1: Clone the Repository

```bash
cd /home/nechi/work/SREforAI
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- FastAPI and Uvicorn (ASGI server)
- PyJWT for JWT token handling
- passlib with bcrypt for password hashing
- SQLAlchemy for database ORM
- Pydantic for data validation
- cryptography for Fernet encryption

### Step 4: Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```bash
# Application Configuration
APP_NAME=AI Cost Monitoring Platform
APP_VERSION=1.0.0
DEBUG=True

# Database Configuration
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/ai_cost_monitor

# Security Configuration (CRITICAL - Change these in production!)
ENCRYPTION_KEY=your-fernet-encryption-key-at-least-32-characters-long
JWT_SECRET_KEY=your-jwt-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

**Generate secure keys:**

```bash
# Generate encryption key (32+ characters)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Set Up PostgreSQL Database

```bash
# Create database
createdb ai_cost_monitor

# Run migrations
psql -U your_user -d ai_cost_monitor -f database/001_initial_schema.sql
psql -U your_user -d ai_cost_monitor -f database/002_add_auth_fields.sql
```

### Step 6: Start the API Server

**Development mode (with auto-reload):**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Step 7: Test the API

**1. Sign up a new organization:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Test Corp",
    "email": "founder@testcorp.com",
    "password": "SecurePass123"
  }'
```

**2. Use the returned token to access protected endpoints:**
```bash
curl -X GET "http://localhost:8000/api/v1/metrics/summary?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## API Endpoints

### Authentication

#### POST `/api/v1/auth/signup`
Register a new organization and user account.

**Description:**
Creates a new organization with the provided name, email, and password. The password is hashed using bcrypt before storage. Returns a JWT access token that can be used to authenticate subsequent requests.

**Request Body:**
```json
{
  "organization_name": "Acme Corp",
  "email": "founder@acme.com",
  "password": "SecurePass123"
}
```

**Field Validation:**
- `organization_name`: String, 1-255 characters, required
- `email`: Valid email address, required
- `password`: String, 8-128 characters, must contain uppercase, lowercase, and digit, required

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "founder@acme.com"
}
```

**Error Responses:**
- `409 Conflict`: Organization with this email already exists
- `422 Unprocessable Entity`: Validation error in request body

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "organization_name": "Acme Corp",
    "email": "founder@acme.com",
    "password": "SecurePass123"
  }'
```

---

#### POST `/api/v1/auth/keys`
Add or update an API key for the authenticated organization.

**Description:**
Securely stores a provider API key (OpenAI or Anthropic) for the authenticated organization. The API key is encrypted using Fernet symmetric encryption before storage. This endpoint requires authentication via Bearer token.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Request Body:**
```json
{
  "provider": "openai",
  "admin_api_key": "sk-proj-..."
}
```

**Field Validation:**
- `provider`: Must be either "openai" or "anthropic", required
- `admin_api_key`: Non-empty string, required

**Response (200 OK):**
```json
{
  "message": "Successfully encrypted and stored openai API key",
  "provider": "openai"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing authentication token
- `404 Not Found`: Organization not found
- `400 Bad Request`: Invalid provider value

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/keys" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "provider": "openai",
    "admin_api_key": "sk-proj-..."
  }'
```

---

### Metrics

All metrics endpoints require authentication via `Authorization: Bearer <token>` header. All queries are strictly filtered by the authenticated organization's `org_id` to ensure tenant isolation.

#### GET `/api/v1/metrics/summary`
Get high-level aggregate metrics for the authenticated organization over a specified date range.

**Description:**
Returns aggregated cost and token metrics (input, output, cached tokens) for the authenticated organization within the specified date range. Useful for dashboard overview cards.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Query Parameters:**
- `start_date`: ISO 8601 datetime string (required)
- `end_date`: ISO 8601 datetime string, must be after start_date (required)

**Response (200 OK):**
```json
{
  "total_cost_usd": 1234.56,
  "total_input_tokens": 1000000,
  "total_output_tokens": 500000,
  "total_cached_tokens": 100000,
  "total_requests": 500,
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing authentication token
- `422 Unprocessable Entity`: Invalid query parameters (e.g., end_date before start_date)

**Example using curl:**
```bash
curl -X GET "http://localhost:8000/api/v1/metrics/summary?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

#### GET `/api/v1/metrics/breakdown`
Get metrics grouped dynamically by model, provider, or API key ID.

**Description:**
Returns metrics grouped by the specified dimension (model, provider, or api_key_id). Each group includes aggregated cost, token counts, and request count. Useful for detailed cost analysis and identifying high-cost resources.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Query Parameters:**
- `start_date`: ISO 8601 datetime string (required)
- `end_date`: ISO 8601 datetime string, must be after start_date (required)
- `group_by`: One of "model", "provider", or "api_key_id" (required)

**Response (200 OK):**
```json
{
  "breakdown": [
    {
      "group_key": "gpt-4o",
      "total_cost_usd": 1000.00,
      "input_tokens": 800000,
      "output_tokens": 400000,
      "cached_tokens": 80000,
      "request_count": 400
    },
    {
      "group_key": "gpt-3.5-turbo",
      "total_cost_usd": 234.56,
      "input_tokens": 200000,
      "output_tokens": 100000,
      "cached_tokens": 20000,
      "request_count": 100
    }
  ],
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59",
  "group_by": "model"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing authentication token
- `400 Bad Request`: Invalid group_by value
- `422 Unprocessable Entity`: Invalid query parameters

**Example using curl:**
```bash
# Group by model
curl -X GET "http://localhost:8000/api/v1/metrics/breakdown?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59&group_by=model" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Group by provider
curl -X GET "http://localhost:8000/api/v1/metrics/breakdown?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59&group_by=provider" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

#### GET `/api/v1/metrics/leak-detector`
Get automated cost-saving insights for the authenticated organization.

**Description:**
Analyzes the organization's usage patterns to surface cost-saving insights such as cache efficiency analysis, cost anomalies, and provider cost comparisons. Insights are generated specifically for the authenticated organization's data.

**Headers:**
- `Authorization: Bearer <token>` (required)

**Query Parameters:**
None

**Response (200 OK):**
```json
{
  "insights": [
    {
      "insight_type": "cache_efficiency",
      "description": "Low cache efficiency (5.2%). Consider optimizing prompts to increase cache hits.",
      "severity": "medium",
      "potential_savings_usd": null,
      "metadata": {
        "cache_efficiency_percent": 5.2
      }
    },
    {
      "insight_type": "cost_anomaly",
      "description": "High cost detected in the last 7 days: $1,500.00. Review usage patterns.",
      "severity": "high",
      "potential_savings_usd": 150.0,
      "metadata": {
        "recent_7_day_cost_usd": 1500.0
      }
    },
    {
      "insight_type": "provider_comparison",
      "description": "openai is your highest cost provider. Consider evaluating alternatives.",
      "severity": "low",
      "potential_savings_usd": null,
      "metadata": {
        "provider_costs": {
          "openai": 1200.0,
          "anthropic": 300.0
        }
      }
    }
  ],
  "total_insights": 3,
  "generated_at": "2024-01-15T10:30:00"
}
```

**Insight Types:**
- `cache_efficiency`: Analyzes prompt cache hit rates
- `cost_anomaly`: Detects unusual spending patterns
- `provider_comparison`: Compares costs across providers

**Severity Levels:**
- `low`: Informational insight
- `medium`: Actionable recommendation
- `high`: Urgent issue requiring attention

**Error Responses:**
- `401 Unauthorized`: Invalid or missing authentication token

**Example using curl:**
```bash
curl -X GET "http://localhost:8000/api/v1/metrics/leak-detector" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### System Endpoints

#### GET `/`
Root endpoint providing API information.

**Response (200 OK):**
```json
{
  "message": "AI Cost Monitoring Platform API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### GET `/health`
Health check endpoint for monitoring and load balancers.

**Response (200 OK):**
```json
{
  "status": "healthy"
}
```

## Security Architecture

### Authentication Flow

1. User signs up via `/api/v1/auth/signup`
2. Password is hashed using bcrypt
3. Organization record is created with email and password_hash
4. JWT token is issued with claims: `sub` (email) and `org_id` (organization UUID)
5. Client includes token in `Authorization: Bearer <token>` header
6. `get_current_org` dependency validates token and injects `OrganizationContext`

### Tenant Isolation

All database queries strictly filter by `org_id` from the authenticated context:

```python
# Example from metrics summary
result = db.query(...).filter(
    HourlyDailyUsageCache.org_id == org_context.org_id,
    # ... date filters
).first()
```

This prevents cross-tenant data leaks by ensuring users can only access their own organization's data.

### API Key Security

- Admin API keys are encrypted using Fernet symmetric encryption before storage
- Encryption key is configured via `ENCRYPTION_KEY` environment variable
- Keys are never stored in plain text in the database

## Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Environment Variables

See `.env.example` for all required configuration variables.

Critical security variables:
- `ENCRYPTION_KEY`: Fernet encryption key (min 32 characters)
- `JWT_SECRET_KEY`: JWT signing secret (change in production)
- `DATABASE_URL`: PostgreSQL connection string

## Database Schema

### organizations
- `id`: UUID (primary key)
- `name`: VARCHAR(255)
- `email`: VARCHAR(255) (unique, indexed)
- `password_hash`: VARCHAR(255)
- `encrypted_openai_admin_key`: TEXT (encrypted)
- `encrypted_anthropic_admin_key`: TEXT (encrypted)
- `created_at`: TIMESTAMP WITH TIME ZONE
- `updated_at`: TIMESTAMP WITH TIME ZONE

### hourly_daily_usage_cache
- `id`: UUID (primary key)
- `org_id`: UUID (foreign key to organizations)
- `provider`: VARCHAR(50)
- `model`: VARCHAR(100)
- `api_key_id`: VARCHAR(255)
- `input_tokens`: BIGINT
- `output_tokens`: BIGINT
- `cached_tokens`: BIGINT
- `raw_cost_usd`: NUMERIC(12, 6)
- `timestamp_bucket`: TIMESTAMP WITH TIME ZONE
- `created_at`: TIMESTAMP WITH TIME ZONE

## Development

Run with auto-reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run tests:
```bash
pytest tests/
```
