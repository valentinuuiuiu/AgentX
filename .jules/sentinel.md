## 2024-06-10 - [Hardcoded Infura API Key]
**Vulnerability:** A hardcoded Infura API key was found in `src/services/tradingAPIService.ts` and `src/contexts/Web3Context.tsx`.
**Learning:** Hardcoded secrets in client-side code are easily extractable, leading to potential abuse and quota exhaustion of the linked service.
**Prevention:** Always use environment variables for sensitive keys and provide safe defaults (like an empty string) or error handling when they are missing.
