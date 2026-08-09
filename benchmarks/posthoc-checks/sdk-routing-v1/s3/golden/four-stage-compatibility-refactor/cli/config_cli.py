from runtime.parser import parse
from schema.errors import ContractError


def run(payload):
    try:
        return {"ok": True, "value": parse(payload)}
    except ContractError as error:
        return {"ok": False, "error_code": error.code}
