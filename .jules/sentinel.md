## 2025-05-31 - Missing Rate Limits & Security Headers on AI Routes
**Vulnerability:** The Express server (`server.ts`) exposed several `/api/` endpoints (including `/api/chat` which calls external LLMs like Gemini and OpenRouter) without any rate limiting. It also lacked fundamental security headers.
**Learning:** Endpoints that call external LLM APIs are extremely vulnerable to DoS and quota exhaustion attacks if left unprotected. Rate limiters are absolutely necessary to secure AI applications. Also `app.set('trust proxy', 1)` is required when rate-limiting is used behind a reverse proxy (like Nginx on a VPS) so the real client IPs are evaluated properly. `helmet` should be used with CSP disabled for Vite build compatability.
**Prevention:** Always implement `express-rate-limit` (or an equivalent) on all AI/LLM integration routes and apply basic security headers using `helmet`.

## 2025-06-06 - Hardcoded Firebase API Key
**Vulnerability:** The Firebase `apiKey` was hardcoded directly in `firebase-applet-config.json`, which was committed to version control.
**Learning:** Hardcoding API keys or other sensitive secrets in source code files exposes the project to unauthorized access, especially when the repository is public or shared. Even if Firebase keys have usage limits, exposing them is bad practice and could lead to quota exhaustion.
**Prevention:** Sensitive keys (e.g., `apiKey`) must be injected dynamically via environment variables like `import.meta.env.VITE_FIREBASE_API_KEY` to avoid hardcoded secrets. Configuration files containing base setups can be checked in, but secrets should always be read from the environment.
