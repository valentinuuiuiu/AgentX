## 2024-06-11 - [CRITICAL] Hardcoded Secret as Fallback Pattern

**Vulnerability:** Found hardcoded Infura API keys (`ddd78bc17de648b2a89acf424fbfa8ed`) being used as fallbacks for the `import.meta.env.VITE_INFURA_API_KEY` environment variable in both `src/services/tradingAPIService.ts` and `src/contexts/Web3Context.tsx`.

**Learning:** Developers are using hardcoded keys as fallbacks for missing environment variables. This is a recurring pattern in this codebase (also found `your_infura_api_key`, `your-api-key`, etc. in other files). This exposes sensitive credentials in the source code, bypassing the security of environment variables.

**Prevention:** Never use hardcoded secrets or dummy placeholder strings (which might later be replaced with real secrets and committed) as fallbacks in `||` expressions for configuration loading. If an environment variable is required and missing, the application should log a warning, fail securely, or gracefully degrade its functionality without relying on a leaked key.
