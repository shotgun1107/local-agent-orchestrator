from migration.legacy import normalize_legacy


def load(payload):
    return normalize_legacy(payload)
