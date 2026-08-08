from migration.upgrade import migrate


def parse(payload):
    return migrate(payload)
