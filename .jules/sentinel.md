## 2026-06-22 - [CRITICAL] Prevent Hardcoded Secrets Fallbacks

**Vulnerability:** Found hardcoded Infura API keys used as fallbacks in configuration values (e.g., `import.meta.env.VITE_INFURA_API_KEY || 'hardcoded_secret'`).

**Learning:** When env vars are missing, developers often use hardcoded strings to keep local development working. This inadvertently leaks sensitive access keys into the version control and final web builds.

**Prevention:** Never use secrets as fallback values in default expressions. Instead, explicitly handle cases where variables might be undefined by gracefully disabling components or outputting warnings via the console logger. Ensure environment parity across all environments.

## 2026-07-01 - [CRITICAL] Prevent Authentication Bypass via Error Fallbacks

**Vulnerability:** Found a hardcoded user ID fallback (`1`) returned during `ImportError` exceptions when loading user management functionality. This bypasses authentication, granting a default access level to any request when the module isn't loaded properly.

**Learning:** Error handlers and `except` blocks that attempt to "fail gracefully" by providing dummy data can inadvertently create catastrophic security holes, especially around authentication or authorization logic.

**Prevention:** Never use hardcoded IDs or "dummy" data to bypass errors in security-critical logic. Instead, fail securely by explicitly throwing an appropriate HTTP error (like 500 Internal Server Error) to halt execution immediately.
