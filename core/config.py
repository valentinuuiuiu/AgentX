import os

def get_nvidia_api_key():
    """
    Retrieves the NVIDIA_API_KEY from environment variables.
    Raises a RuntimeError if the key is missing.
    """
    key = os.getenv("NVIDIA_API_KEY")

    if not key:
        raise RuntimeError(
            "NVIDIA_API_KEY environment variable is missing. "
            "Please set it in your environment or .env file."
        )

    return key

NVIDIA_API_KEY = get_nvidia_api_key()
