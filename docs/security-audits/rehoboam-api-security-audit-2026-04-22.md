# Vetala Security Audit — Rehoboam API Server
**Date**: 2026-04-22
**Auditor**: Vetal Shabar Raksha
**Scope**: `/home/aryan/free-claude/bittensor/clean_rehoboam_project/api_server.py`
**Severity**: CRITICAL — Production deployment unsafe

---

## Finding 1: Hardcoded Default JWT_SECRET
**Severity**: CRITICAL
**Line**: 183
**CVSS**: 9.8

```python
JWT_SECRET = os.getenv("JWT_SECRET", "a-very-insecure-default-secret-for-dev")
```

If `JWT_SECRET` is not set in environment, the server falls back to a hardcoded string. An attacker who knows this default can forge any JWT token, impersonate any user, and gain full API access. The warning log is insufficient — the server should **refuse to start** without a proper secret.

**Impact**: Complete authentication bypass.

**Fix**: Refuse startup if secret is default. Require minimum 32 bytes of entropy.

---

## Finding 2: CORS `allow_origins=["*"]` with `allow_credentials=True`
**Severity**: CRITICAL
**Line**: 144-146
**CVSS**: 8.2

```python
allow_origins=["*"],  # Restrict in production
allow_credentials=True,
allow_methods=["*"],
```

`allow_origins="*"` combined with `allow_credentials=True` is a known CSRF vector. Any malicious website can make authenticated cross-origin requests to the API using the victim's cookies/session. The comment says "Restrict in production" but the code doesn't actually restrict anything.

**Impact**: Cross-site request forgery, session hijacking, unauthorized API calls from attacker domains.

**Fix**: Read allowed origins from environment. Default to empty list. Never wildcard with credentials.

---

## Finding 3: No Rate Limiting on Auth Endpoints
**Severity**: HIGH
**CVSS**: 7.5

`/api/auth/login`, `/api/auth/register`, and token refresh have no rate limiting. Brute-force attacks against passwords are trivial.

**Impact**: Account takeover via credential stuffing, password brute-forcing.

**Fix**: Implement Redis-backed rate limiting (3 attempts per 15 min window).

---

## Finding 4: Secrets in docker-compose.yml (Plaintext)
**Severity**: HIGH
**CVSS**: 7.0

```yaml
POSTGRES_PASSWORD: rehoboam123
GF_SECURITY_ADMIN_PASSWORD: rehoboam123
```

Database and Grafana passwords are hardcoded in the compose file. These are checked into version control and visible in `docker inspect` output.

**Impact**: Lateral movement, database compromise, monitoring system takeover.

**Fix**: Use Docker secrets or `.env` file excluded from git. Generate strong random passwords on first run.

---

## Finding 5: No HTTPS Enforcement
**Severity**: MEDIUM
**CVSS**: 5.3

The FastAPI server runs on HTTP (port 5002). No redirect to HTTPS, no HSTS headers, no secure cookie flags.

**Impact**: Man-in-the-middle attacks, token interception on local network.

**Fix**: Add HTTPS redirect middleware. Set `Secure`, `HttpOnly`, `SameSite=Strict` on cookies.

---

## Finding 6: Weak JWT Algorithm (HS256)
**Severity**: MEDIUM
**CVSS**: 4.3

`JWT_ALGORITHM = "HS256"` is fine for symmetric signing, but the secret is weak. Consider RS256 with a proper key rotation mechanism for multi-service deployments.

**Impact**: If secret leaks, all tokens are forgeable. No key rotation support.

**Fix**: Keep HS256 for now but add secret rotation and minimum entropy check.

---

## Finding 7: Missing Input Validation on Login
**Severity**: MEDIUM
**CVSS**: 5.3

The login endpoint accepts raw username/password with no validation on length, characters, or SQL injection protection.

**Impact**: Potential SQL injection if DB layer is weak. Username enumeration.

**Fix**: Add pydantic validators for username format, password minimum length.

---

## Finding 8: No Audit Logging
**Severity**: LOW
**CVSS**: 3.7

Failed login attempts, token refreshes, and privilege escalations are not logged to a tamper-resistant store.

**Impact**: Incident response is impossible. Attackers can brute-force without detection.

**Fix**: Log all auth events to PostgreSQL with IP, timestamp, user agent, and outcome.

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 2 | 🔴 Unfixed |
| HIGH | 2 | 🟠 Unfixed |
| MEDIUM | 2 | 🟡 Unfixed |
| LOW | 2 | 🟢 Acceptable |

**Verdict**: DO NOT deploy to production. Authentication is bypassable. CORS is wide open. Rate limiting is absent.

**Recommended Actions**:
1. Set `JWT_SECRET` via Docker secret or env var with ≥32 random bytes
2. Remove CORS wildcard, enforce origin whitelist
3. Add Redis rate limiter on all auth endpoints
4. Move passwords out of docker-compose.yml
5. Add HTTPS redirect middleware
6. Implement audit logging table

---

*Om Namo Veer Vetaal*
*Sankat Bagao*
*Jaldi Aao*
