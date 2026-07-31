import time

_DATA_VERSION: int = int(time.time())


def touch_data_version() -> None:
    global _DATA_VERSION
    _DATA_VERSION = int(time.time())


def get_data_version() -> str:
    return f'"{_DATA_VERSION}"'
