from schema.model import validate


def serialize(payload):
    return validate(payload)
