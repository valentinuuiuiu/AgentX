## 2025-05-05 - target="_blank" without rel="noopener noreferrer"
**Vulnerability:** A `target="_blank"` anchor link was missing the `rel="noopener noreferrer"` attribute in `src/components/Team.tsx`.
**Learning:** This exposes the application to a "reverse tabnabbing" attack where the newly opened tab can gain a reference to the `window.opener` object of the original page and potentially redirect it to a malicious site.
**Prevention:** Always add `rel="noopener noreferrer"` to external links that open in a new tab via `target="_blank"`.
## 2024-05-04 - Fix information leakage in error handling
**Vulnerability:** In `server.ts`, error stack traces and detailed error messages were being leaked to the client in the `/api/market-data` endpoint. The `catch (e)` block contained `res.status(500).json({ error: String(e) || "Failed to fetch real market data" });`.
**Learning:** This is a classic information leakage vulnerability. Exposing raw error strings or stack traces can provide attackers with valuable insights into the internal workings of the application, such as file paths, dependencies, and internal configurations.
**Prevention:** Always sanitize error messages sent to the client. Log the full error on the server side for debugging, but only send generic, non-sensitive error messages to the client.
## 2024-05-30 - Add Rate Limiting and Security Headers
**Vulnerability:** The application was missing fundamental security headers and an exposed API endpoint (`/api/chat`) lacked rate-limiting, making it vulnerable to Denial of Service (DoS) and potential LLM quota exhaustion.
**Learning:** This exposes the application to DoS attacks on expensive resources (LLM API requests) and increases the risk of attacks like XSS, Clickjacking without basic security headers, which are very easy to implement using standard tools like helmet.
**Prevention:** Use standard middleware tools like `helmet` for security headers, and always configure rate limiting via tools like `express-rate-limit` for API routes—especially routes making external or resource-intensive calls. Setting `app.set("trust proxy", 1)` is required if hosted behind a reverse proxy so the IP addresses are tracked correctly.
