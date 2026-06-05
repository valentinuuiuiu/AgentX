## 2025-05-31 - Missing Rate Limits & Security Headers on AI Routes
**Vulnerability:** The Express server (`server.ts`) exposed several `/api/` endpoints (including `/api/chat` which calls external LLMs like Gemini and OpenRouter) without any rate limiting. It also lacked fundamental security headers.
**Learning:** Endpoints that call external LLM APIs are extremely vulnerable to DoS and quota exhaustion attacks if left unprotected. Rate limiters are absolutely necessary to secure AI applications. Also `app.set('trust proxy', 1)` is required when rate-limiting is used behind a reverse proxy (like Nginx on a VPS) so the real client IPs are evaluated properly. `helmet` should be used with CSP disabled for Vite build compatability.
**Prevention:** Always implement `express-rate-limit` (or an equivalent) on all AI/LLM integration routes and apply basic security headers using `helmet`.

## 2026-06-05 - Hardcoded API Key in Firebase Config
**Vulnerability:** A hardcoded Firebase `apiKey` was found in `firebase-applet-config.json`.
**Learning:** In this project, Firebase configuration relies on a static JSON file. Since secrets shouldn't be hardcoded into JSON configurations committed to version control, a hybrid approach of using a base JSON file and injecting the sensitive `apiKey` dynamically via Vite's `import.meta.env` at runtime is necessary.
**Prevention:** Never commit API keys or secrets in static configuration files. Always load sensitive data securely using environment variables at runtime, and document this pattern in the application's configuration setup.
