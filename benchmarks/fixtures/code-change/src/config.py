ALLOWED_KEYS = {"name"}


def parse_config(value: dict[str, object]) -> dict[str, object]:
    return dict(value)
