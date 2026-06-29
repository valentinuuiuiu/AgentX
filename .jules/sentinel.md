## 2026-06-29 - [CRITICAL] Remove Hardcoded Fallbacks for External API Keys

**Vulnerability:** Found active and dummy API keys embedded directly within the codebase. Specific findings included `QfkjpUEE-OGny-o7VA7Hvo2VJ7J4ui9H` as an Alchemy API key fallback in `verify_rehoboam_integrations.py`, `your_infura_api_key` in `src/services/hive_mind/vetalShabarRaksha.js`, and `your_nvidia_api_key_here` in `configure_nvidia_babyagi.py`.

**Learning:** Providing inline string fallbacks for secrets, even dummy ones, introduces significant risk. If the underlying environment configuration fails or isn't set, actual credentials will leak, and dummy ones mask configuration failures by either executing with bad auth (which might lead to unexpected application states or silent failures) or persisting placeholder strings in repositories.

**Prevention:** Always enforce strict checking on sensitive environment variables. Do not use `|| "fallback_string"`, or similar default argument paradigms `os.environ.get("KEY", "fallback")` for API keys, passwords, or secrets. Instead, read the value as-is. If the value is critically required to proceed, throw a clear exception (`throw new Error()`, `raise ValueError()`). If optional, leave it empty or `None` and handle gracefully at the execution layer (e.g., warning logs, skipping downstream functionality).

## 2026-06-22 - [CRITICAL] Prevent Hardcoded Secrets Fallbacks

**Vulnerability:** Found hardcoded Infura API keys used as fallbacks in configuration values (e.g., `import.meta.env.VITE_INFURA_API_KEY || 'hardcoded_secret'`).

**Learning:** When env vars are missing, developers often use hardcoded strings to keep local development working. This inadvertently leaks sensitive access keys into the version control and final web builds.

**Prevention:** Never use secrets as fallback values in default expressions. Instead, explicitly handle cases where variables might be undefined by gracefully disabling components or outputting warnings via the console logger. Ensure environment parity across all environments.
