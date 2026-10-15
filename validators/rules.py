import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from .regex import validate_regex

SUPPORTED_TYPES = {
    "string",
    "integer",
    "decimal",
    "date",
    "boolean",
}

def is_null(value):
    return value is None or str(value).strip() == ""

def validate_type(value, data_type, date_format="%Y-%m-%d"):
    value = str(value).strip()
    if data_type == "string":
        return True
    if data_type == "integer":
        return bool(re.fullmatch(r"[+-]?\d+", value))
    if data_type == "decimal":
        try:
            number = Decimal(value)
            return number.is_finite()
        except InvalidOperation:
            return False
    if data_type == "date":
        try:
            parsed = datetime.strptime(value, date_format)
            return parsed.strftime(date_format) == value
        except (ValueError, TypeError):
            return False
    if data_type == "boolean":
        return value.lower() in {
            "true", "false", "1", "0"
        }
    raise ValueError(
        f"Tipo de dato no soportado: {data_type}"
    )


def validate_range(value, column):
    if "min" not in column and "max" not in column:
        return True
    number = Decimal(str(value).strip())
    if "min" in column:
        if number < Decimal(str(column["min"])):
            return False
    if "max" in column:
        if number > Decimal(str(column["max"])):
            return False
    return True


def validate_allowed_values(value, column):
    allowed_values = column.get("allowed_values")
    if allowed_values is None:
        return True
    return str(value) in {
        str(item) for item in allowed_values
    }

def validate_value(value, column):
    errors = []
    column_name = column["name"]
    data_type = column["type"]
    if is_null(value):

        if not column.get("nullable", True):
            errors.append(
                f"{column_name}: valor nulo no permitido"
            )

        return errors
    if not validate_type(
        value,
        data_type,
        column.get("format", "%Y-%m-%d")
    ):
        errors.append(
            f"{column_name}: tipo inválido, se esperaba {data_type}"
        )
        return errors
    if data_type in {"integer", "decimal"}:
        if not validate_range(value, column):
            errors.append(
                f"{column_name}: fuera del rango permitido"
            )
    if not validate_allowed_values(value, column):
        errors.append(
            f"{column_name}: valor no permitido"
        )
    if "regex" in column:
        if not validate_regex(value, column["regex"]):
            errors.append(
                f"{column_name}: formato inválido"
            )
    return errors
