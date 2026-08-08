from migration.upgrade import migrate


def normalize_legacy(payload):
    return migrate(payload)
