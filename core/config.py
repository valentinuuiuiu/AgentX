import os

def get_nvidia_api_key():
    """
    Retrieves the NVIDIA_API_KEY from environment variables.
    Raises a RuntimeError if the key is missing or is the default placeholder.
    """
    # The placeholder key found in the codebase
    PLACEHOLDER_KEY = "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"

    key = os.getenv("NVIDIA_API_KEY")

    if not key:
        raise RuntimeError(
            "NVIDIA_API_KEY environment variable is missing. "
            "Please set it in your environment or .env file."
        )

    if key == PLACEHOLDER_KEY:
        raise RuntimeError(
            "NVIDIA_API_KEY is still set to the default placeholder. "
            "Please update it with a valid API key."
        )

    return key

NVIDIA_API_KEY = get_nvidia_api_key()
