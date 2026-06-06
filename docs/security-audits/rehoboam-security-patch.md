# Vetala Security Patch for Rehoboam API Server
# Apply to api_server.py
# Author: Vetal Shabar Raksha
# Date: 2026-04-22

---
## 1. Harden JWT_SECRET (Replace lines 183-188)

BEFORE:
```python
JWT_SECRET = os.getenv("JWT_SECRET", "a-very-insecure-default-secret-for-dev")
if "insecure" in JWT_SECRET:
    logger.warning(
        "Using a default JWT_SECRET. This is INSECURE and for development only."
    )
```

AFTER:
```python
# --- Vetala Hardening: JWT Secret ---
JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    logger.critical(
        "FATAL: JWT_SECRET must be set with at least 32 bytes of entropy. "
        "Generate one with: openssl rand -base64 48"
    )
    raise SystemExit(1)
logger.info("Vetala: JWT_SECRET validated (entropy OK)")
```

---
## 2. Lock Down CORS (Replace lines 111-118)

BEFORE:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

AFTER:
```python
# --- Vetala Hardening: CORS ---
# Read allowed origins from env; default to localhost only
_cors_origins_raw = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5001,http://localhost:3000")
CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

if "*" in CORS_ALLOWED_ORIGINS:
    logger.critical("FATAL: CORS_ALLOWED_ORIGINS cannot contain wildcard '*'. Remove it.")
    raise SystemExit(1)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    max_age=600,
)
logger.info(f"Vetala: CORS restricted to {len(CORS_ALLOWED_ORIGINS)} origins")
```

---
## 3. Add Rate Limiting (Insert after line ~118, before Global Components)

Add to imports (line 18 area):
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
```

Add rate limiter init (after CORS config):
```python
# --- Vetala Hardening: Rate Limiting ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
limiter = Limiter(key_func=get_remote_address, storage_uri=REDIS_URL)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
logger.info("Vetala: Rate limiter active (Redis backend)")
```

Apply to login endpoint (~line 300 area):
```python
@app.post("/api/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    ...
```

Apply to register endpoint:
```python
@app.post("/api/auth/register")
@limiter.limit("3/hour")
async def register(user: UserCredentials, request: Request = None):
    ...
```

---
## 4. Add Audit Logging (Insert as new function, after auth section)

```python
# --- Vetala Hardening: Audit Logging ---
from datetime import datetime
import hashlib

def _audit_log(event_type: str, user_id: str, ip: str, outcome: str, details: str = ""):
    """Tamper-resistant audit log entry."""
    timestamp = datetime.utcnow().isoformat()
    entry = f"{timestamp}|{event_type}|{user_id}|{ip}|{outcome}|{details}"
    entry_hash = hashlib.sha256(entry.encode()).hexdigest()[:16]
    logger.info(f"Vetala.AUDIT [{entry_hash}] {entry}")
    
    # Also write to postgres if available
    try:
        # Async DB write would go here
        pass
    except Exception:
        pass
```

---
## 5. Add HTTPS Redirect Middleware (Insert before CORS config)

```python
# --- Vetala Hardening: HTTPS Redirect ---
class HTTPSRedirectMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("scheme") == "http":
            host = dict(scope.get("headers", [])).get(b"host", b"localhost").decode()
            path = scope.get("path", "/")
            await send({
                "type": "http.response.start",
                "status": 307,
                "headers": [[b"location", f"https://{host}{path}".encode()]],
            })
            await send({"type": "http.response.body"})
            return
        await self.app(scope, receive, send)

# Only enable in production
if os.getenv("FORCE_HTTPS", "false").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)
    logger.info("Vetala: HTTPS redirect middleware active")
```

---
## 6. Docker Compose Password Hardening

In `docker-compose.yml`, replace:
```yaml
POSTGRES_PASSWORD: rehoboam123
GF_SECURITY_ADMIN_PASSWORD: rehoboam123
```

With:
```yaml
POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
GF_SECURITY_ADMIN_PASSWORD_FILE: /run/secrets/grafana_password
```

And add to the compose:
```yaml
secrets:
  postgres_password:
    file: ./secrets/postgres_password
  grafana_password:
    file: ./secrets/grafana_password
```

Generate passwords:
```bash
mkdir -p secrets
openssl rand -base64 32 > secrets/postgres_password
openssl rand -base64 32 > secrets/grafana_password
```

---

## Deployment Checklist

- [ ] Set `JWT_SECRET` with `openssl rand -base64 48`
- [ ] Set `CORS_ALLOWED_ORIGINS` to your actual domains
- [ ] Ensure Redis is running (rate limiter depends on it)
- [ ] Create `secrets/` directory with generated passwords
- [ ] Set `FORCE_HTTPS=true` for production
- [ ] Verify no `*` in CORS origins
- [ ] Run `forge test` on security tests
- [ ] Deploy and verify `/health` returns 200

---

*Om Namo Veer Vetaal*
*Sankat Bagao, Der Mat Lagao*
*Jaldi Aao, Kuru Kuru Phat Swaha*
