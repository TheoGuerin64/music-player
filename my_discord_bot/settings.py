from os import environ


def get_env(key: str) -> str:
    value = environ.get(key)
    if value is None:
        raise ValueError(f"{key} environment variable is not set.")
    return value


TOKEN = get_env("TOKEN")
NASA_API_KEY = get_env("NASA_API_KEY")
