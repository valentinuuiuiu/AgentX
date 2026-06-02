## 2025-05-31 - Missing Rate Limits & Security Headers on AI Routes
**Vulnerability:** The Express server (`server.ts`) exposed several `/api/` endpoints (including `/api/chat` which calls external LLMs like Gemini and OpenRouter) without any rate limiting. It also lacked fundamental security headers.
**Learning:** Endpoints that call external LLM APIs are extremely vulnerable to DoS and quota exhaustion attacks if left unprotected. Rate limiters are absolutely necessary to secure AI applications. Also `app.set('trust proxy', 1)` is required when rate-limiting is used behind a reverse proxy (like Nginx on a VPS) so the real client IPs are evaluated properly. `helmet` should be used with CSP disabled for Vite build compatability.
**Prevention:** Always implement `express-rate-limit` (or an equivalent) on all AI/LLM integration routes and apply basic security headers using `helmet`.

## 2026-06-02 - Hardcoded Firebase API Key
**Vulnerability:** The Firebase API key was hardcoded in `firebase-applet-config.json`, exposing it in version control.
**Learning:** Sensitive keys like `apiKey` must not be stored in static configuration files that are checked into version control. Doing so risks credential leakage and unauthorized access to Firebase services.
**Prevention:** Always inject sensitive keys dynamically via environment variables (e.g., `import.meta.env.VITE_FIREBASE_API_KEY`) at runtime and document the required variables in `.env.example`.
