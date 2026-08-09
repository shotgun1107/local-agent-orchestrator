ERROR_CODES = {
    "missing_field": "MISSING_FIELD",
    "invalid_mode": "INVALID_MODE",
    "alias_conflict": "ALIAS_CONFLICT",
    "unknown_field": "UNKNOWN_FIELD",
}


class ContractError(ValueError):
    code = "CONTRACT_ERROR"


class MissingFieldError(ContractError):
    code = ERROR_CODES["missing_field"]


class InvalidModeError(ContractError):
    code = ERROR_CODES["invalid_mode"]


class AliasConflictError(ContractError):
    code = ERROR_CODES["alias_conflict"]


class UnknownFieldError(ContractError):
    code = ERROR_CODES["unknown_field"]
