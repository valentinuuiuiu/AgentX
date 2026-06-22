## 2026-06-22 - [CRITICAL] Prevent Hardcoded Secrets Fallbacks

**Vulnerability:** Found hardcoded Infura API keys used as fallbacks in configuration values (e.g., `import.meta.env.VITE_INFURA_API_KEY || 'hardcoded_secret'`).

**Learning:** When env vars are missing, developers often use hardcoded strings to keep local development working. This inadvertently leaks sensitive access keys into the version control and final web builds.

**Prevention:** Never use secrets as fallback values in default expressions. Instead, explicitly handle cases where variables might be undefined by gracefully disabling components or outputting warnings via the console logger. Ensure environment parity across all environments.
