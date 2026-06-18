## 2024-06-18 - Hardcoded NVIDIA NIM API Key
**Vulnerability:** Found multiple instances of hardcoded `nvapi-` strings throughout the codebase, representing a hardcoded NVIDIA NIM API Key which could leak credentials.
**Learning:** Found multiple files like `nvidia_openai_integration.py` and testing scripts where this API key was hardcoded for rapid prototyping, which bypasses environmental configuration.
**Prevention:** Avoid committing test scripts with hardcoded credentials and ensure all integrations, especially with new platforms like NVIDIA NIM, correctly pull their secrets from `os.environ` or `.env`.

## 2024-06-18 - Hardcoded INFURA API Key
**Vulnerability:** Found instances of a hardcoded INFURA API Key fallback `ddd78...` and `your_infura_api_key` in JS and TS frontend and backend files.
**Learning:** Frontend config default values can still expose potentially sensitive keys if meant to be a fallback, though in this case `ddd78bc...` appears to be a real or long-standing test key.
**Prevention:** Remove fallback hardcoded keys from frontend code; environment configurations should handle failing gracefully if variables are omitted, without including hardcoded backups.
