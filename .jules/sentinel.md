## 2025-05-05 - target="_blank" without rel="noopener noreferrer"
**Vulnerability:** A `target="_blank"` anchor link was missing the `rel="noopener noreferrer"` attribute in `src/components/Team.tsx`.
**Learning:** This exposes the application to a "reverse tabnabbing" attack where the newly opened tab can gain a reference to the `window.opener` object of the original page and potentially redirect it to a malicious site.
**Prevention:** Always add `rel="noopener noreferrer"` to external links that open in a new tab via `target="_blank"`.
## 2024-05-04 - Fix information leakage in error handling
**Vulnerability:** In `server.ts`, error stack traces and detailed error messages were being leaked to the client in the `/api/market-data` endpoint. The `catch (e)` block contained `res.status(500).json({ error: String(e) || "Failed to fetch real market data" });`.
**Learning:** This is a classic information leakage vulnerability. Exposing raw error strings or stack traces can provide attackers with valuable insights into the internal workings of the application, such as file paths, dependencies, and internal configurations.
**Prevention:** Always sanitize error messages sent to the client. Log the full error on the server side for debugging, but only send generic, non-sensitive error messages to the client.
## 2026-05-11 - SSRF vulnerability in OpenRouter API instantiation
**Vulnerability:** The `/api/chat` endpoint allowed users to supply an `openRouterBaseUrl` in the `req.body` which was used as the `baseURL` when instantiating the OpenAI client with the `openRouterApiKey`. This allowed a malicious user to configure the API client to point to a server they control, effectively transmitting the server's private `OPENROUTER_API_KEY` to the attacker.
**Learning:** Instantiating external API SDKs with base URLs derived from user input is dangerous because the SDK will transmit authentication credentials (API keys) to that URL. This is a form of Server-Side Request Forgery (SSRF) that leads directly to credential leakage.
**Prevention:** Never use user-supplied input to define the `baseURL` for an API client that requires authentication. Always hardcode trusted base URLs or use verified environment variables that cannot be manipulated by external requests.
