import os


def get_env(key: str) -> str:
    value = os.environ.get(key)
    assert value is not None, f"{key} environment variable is not set."
    return value


TOKEN = get_env("TOKEN")
