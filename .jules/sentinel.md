## 2024-06-07 - [Fix hardcoded NVIDIA API keys]
**Vulnerability:** Found hardcoded `nvapi-...` NVIDIA API keys in several test scripts and integrations (minimax_nvidia_integration.py, kimi_test.py, etc.).
**Learning:** Hardcoding API keys exposes sensitive credentials directly in source code, leading to potential unauthorized access and quota exhaustion if the repository is shared or compromised. The codebase lacked a centralized mechanism to inject these specific keys securely from environment variables.
**Prevention:** Always use environment variables (e.g., `os.environ.get("NVIDIA_NIM_API_KEY")`) to handle sensitive credentials and document required keys in `.env.example`.
