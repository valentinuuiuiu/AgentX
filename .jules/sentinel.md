## 2025-02-23 - [Hardcoded NVIDIA API Keys]
**Vulnerability:** Found hardcoded NVIDIA API keys in multiple Python scripts (e.g. nvidia_openai_integration.py, minimax_nvidia_integration.py, kimi_test.py).
**Learning:** Development testing often bypasses environment variable injection for convenience, leaving actual keys inside version-controlled code.
**Prevention:** Rely on standard `os.environ.get('NVIDIA_NIM_KEY')` or similar `.env` setups across all scripts and set up lint rules (e.g. detect-secrets) to catch leaked tokens.
