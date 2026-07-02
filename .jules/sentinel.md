## 2026-06-22 - [CRITICAL] Prevent Hardcoded Secrets Fallbacks

**Vulnerability:** Found hardcoded Infura API keys used as fallbacks in configuration values (e.g., `import.meta.env.VITE_INFURA_API_KEY || 'hardcoded_secret'`).

**Learning:** When env vars are missing, developers often use hardcoded strings to keep local development working. This inadvertently leaks sensitive access keys into the version control and final web builds.

**Prevention:** Never use secrets as fallback values in default expressions. Instead, explicitly handle cases where variables might be undefined by gracefully disabling components or outputting warnings via the console logger. Ensure environment parity across all environments.

## 2026-06-25 - [HIGH] Fix Overly permissive CORS configuration
**Vulnerability:** Found overly permissive CORS configuration in `api_server.py` (`allow_origins=["*"]` combined with `allow_credentials=True`), presenting a significant cross-site scripting security risk.
**Learning:** Overly permissive CORS configurations are often used to simplify local development or resolve browser-level blocks during initial integration. However, when left in production code (especially with `allow_credentials=True`), this opens the backend up to Cross-Site Request Forgery (CSRF) and other attacks, as malicious domains could potentially send authenticated requests. Note that ASGI frameworks/FastAPI correctly block `allow_origins=["*"]` with `allow_credentials=True` for security reasons in modern versions, meaning it could also lead to 500 errors.
**Prevention:** Never use `allow_origins=["*"]` with `allow_credentials=True`. Always hardcode the exact list of known production and local development origins, or rely on a sanitized list provided securely via environment variables (e.g. `CORS_ORIGINS`).
