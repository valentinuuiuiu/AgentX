## 2025-05-05 - target="_blank" without rel="noopener noreferrer"
**Vulnerability:** A `target="_blank"` anchor link was missing the `rel="noopener noreferrer"` attribute in `src/components/Team.tsx`.
**Learning:** This exposes the application to a "reverse tabnabbing" attack where the newly opened tab can gain a reference to the `window.opener` object of the original page and potentially redirect it to a malicious site.
**Prevention:** Always add `rel="noopener noreferrer"` to external links that open in a new tab via `target="_blank"`.
## 2024-05-04 - Fix information leakage in error handling
**Vulnerability:** In `server.ts`, error stack traces and detailed error messages were being leaked to the client in the `/api/market-data` endpoint. The `catch (e)` block contained `res.status(500).json({ error: String(e) || "Failed to fetch real market data" });`.
**Learning:** This is a classic information leakage vulnerability. Exposing raw error strings or stack traces can provide attackers with valuable insights into the internal workings of the application, such as file paths, dependencies, and internal configurations.
**Prevention:** Always sanitize error messages sent to the client. Log the full error on the server side for debugging, but only send generic, non-sensitive error messages to the client.
## 2025-05-18 - SSRF and API Key Leakage via Dynamic baseURL
**Vulnerability:** The `/api/chat` endpoint in `server.ts` previously accepted `nvidiaBaseUrl` and `openRouterBaseUrl` from the client payload `req.body`. These user-controlled inputs were directly passed as the `baseURL` property when instantiating the `OpenAI` client, passing along sensitive server API keys (`NVIDIA_NIM_API_KEY` and `OPEN_ROUTER_API_KEY`).
**Learning:** Allowing user-controlled input to define the `baseURL` of external API clients creates a critical Server-Side Request Forgery (SSRF) and credential leakage vulnerability. An attacker can supply a URL pointing to a malicious server they control, and the backend will unwittingly send the API keys in the authorization headers to that malicious server.
**Prevention:** Never allow user input to determine the base URL or destination domain for outbound requests that include sensitive credentials. Always hardcode or use trusted environment variables for base URLs of third-party services.
