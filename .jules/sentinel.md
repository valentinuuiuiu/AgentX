## 2025-02-14 - Fix Hardcoded NVIDIA API Keys in Python Files
**Vulnerability:** Multiple Python files contained hardcoded `NVIDIA_NIM_KEY` tokens (e.g., `nvapi-...`).
**Learning:** Hardcoded secrets in the codebase pose a severe security risk and can be easily extracted by attackers.
**Prevention:** Always use environment variables (`os.environ.get("NVIDIA_API_KEY", "")`) to access sensitive information.
