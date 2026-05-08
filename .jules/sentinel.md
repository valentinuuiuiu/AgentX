## 2025-05-05 - target="_blank" without rel="noopener noreferrer"
**Vulnerability:** A `target="_blank"` anchor link was missing the `rel="noopener noreferrer"` attribute in `src/components/Team.tsx`.
**Learning:** This exposes the application to a "reverse tabnabbing" attack where the newly opened tab can gain a reference to the `window.opener` object of the original page and potentially redirect it to a malicious site.
**Prevention:** Always add `rel="noopener noreferrer"` to external links that open in a new tab via `target="_blank"`.
## 2024-05-04 - Fix information leakage in error handling
**Vulnerability:** In `server.ts`, error stack traces and detailed error messages were being leaked to the client in the `/api/market-data` endpoint. The `catch (e)` block contained `res.status(500).json({ error: String(e) || "Failed to fetch real market data" });`.
**Learning:** This is a classic information leakage vulnerability. Exposing raw error strings or stack traces can provide attackers with valuable insights into the internal workings of the application, such as file paths, dependencies, and internal configurations.
**Prevention:** Always sanitize error messages sent to the client. Log the full error on the server side for debugging, but only send generic, non-sensitive error messages to the client.
## 2024-05-08 - SSRF and Credential Leakage via User-Controlled Base URLs
**Vulnerability:** The `/api/chat` endpoint in `server.ts` accepted `nvidiaBaseUrl` and `openRouterBaseUrl` from the client payload and passed them directly to the backend OpenAI client instantiation.
**Learning:** Trusting client input for base URLs when initializing HTTP clients or SDKs with secret API keys allows an attacker to specify an arbitrary URL. This causes the server to send its API keys to the attacker-controlled server (Credential Leakage) and potentially interact with internal network resources (SSRF).
**Prevention:** To prevent SSRF and credential leakage, backend HTTP clients and SDKs (e.g., OpenAI integrations) must use hardcoded, trusted base URLs rather than dynamically assigning them from user-controlled payload parameters.
