import os


def get_env(key: str) -> str:
    value = os.environ.get(key)
    assert value is not None, f"{key} environment variable is not set."
    return value


TOKEN = get_env("TOKEN")
NASA_API_KEY = get_env("NASA_API_KEY")
