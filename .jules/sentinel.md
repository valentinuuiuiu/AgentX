## 2024-05-24 - [Hardcoded Infura API Keys]
**Vulnerability:** Hardcoded Infura API keys were found in the codebase as fallbacks for the `VITE_INFURA_API_KEY` environment variable.
**Learning:** Using `|| 'hardcoded_secret'` after an environment variable creates a critical risk of exposing keys in the source code if the environment variable is not set.
**Prevention:** Always rely strictly on environment variables without hardcoded fallbacks for sensitive keys. Implement logging or error handling when keys are missing to degrade gracefully.
