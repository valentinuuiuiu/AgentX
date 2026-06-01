## 2025-05-31 - Missing Rate Limits & Security Headers on AI Routes
**Vulnerability:** The Express server (`server.ts`) exposed several `/api/` endpoints (including `/api/chat` which calls external LLMs like Gemini and OpenRouter) without any rate limiting. It also lacked fundamental security headers.
**Learning:** Endpoints that call external LLM APIs are extremely vulnerable to DoS and quota exhaustion attacks if left unprotected. Rate limiters are absolutely necessary to secure AI applications. Also `app.set('trust proxy', 1)` is required when rate-limiting is used behind a reverse proxy (like Nginx on a VPS) so the real client IPs are evaluated properly. `helmet` should be used with CSP disabled for Vite build compatability.
**Prevention:** Always implement `express-rate-limit` (or an equivalent) on all AI/LLM integration routes and apply basic security headers using `helmet`.

## 2025-05-31 - Hardcoded Firebase API Key
**Vulnerability:** A hardcoded Firebase API key was found in `firebase-applet-config.json`.
**Learning:** Hardcoding sensitive API keys or credentials in JSON configuration files (or anywhere in the source code) poses a critical security risk as they could be exposed in version control or to unauthorized individuals. It is safer to use environment variables for keys. Although Firebase API keys are meant to be public, it is best practice to keep them out of source control.
**Prevention:** Avoid committing sensitive credentials directly into the repository. Instead, use environment variables (`import.meta.env.*` or `process.env.*`) and document the required variables in an `.env.example` file.
