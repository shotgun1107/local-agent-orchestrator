from runtime.parser import parse
from runtime.serializer import serialize


def roundtrip(payload):
    return serialize(parse(payload))
