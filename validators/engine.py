
import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
import yaml
from .rules import SUPPORTED_TYPES, validate_value
from .regex import PATTERNS

def load_contract(file_path):
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el contrato: {file_path}")
    with path.open("r", encoding="utf-8") as file:
        contract = yaml.safe_load(file)
    validate_contract(contract)
    return contract
def validate_contract(contract):
    if not isinstance(contract, dict):
        raise ValueError("El contrato debe ser un diccionario")
    for section in ("contract", "file", "columns"):
        if section not in contract:
            raise ValueError(f"Falta la sección: {section}")
    metadata = contract["contract"]
    config = contract["file"]
    columns = contract["columns"]
    if not isinstance(metadata, dict) or not isinstance(config, dict):
        raise ValueError("Las secciones contract y file deben ser diccionarios")
    if not isinstance(columns, list) or not columns:
        raise ValueError("columns debe ser una lista no vacía")
    for key in ("name", "version", "owner"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f"Metadato inválido: {key}")
    if config.get("format") != "csv":
        raise ValueError("Solo se admiten archivos CSV")
    delimiter = config.get("delimiter", ",")
    if not isinstance(delimiter, str) or len(delimiter) != 1:
        raise ValueError("Delimitador inválido")
    if config.get("encoding", "utf-8") not in ("utf-8", "utf-8-sig"):
        raise ValueError("Encoding no soportado")
    if not isinstance(config.get("allow_extra_columns", False), bool):
        raise ValueError("allow_extra_columns debe ser booleano")
    names = set()
    for column in columns:
        if not isinstance(column, dict):
            raise ValueError("Cada columna debe ser un diccionario")
        name = column.get("name")
        data_type = column.get("type")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Nombre de columna inválido")
        if name in names:
            raise ValueError(f"Columna duplicada: {name}")
        names.add(name)
        if data_type not in SUPPORTED_TYPES:
            raise ValueError(f"Tipo no soportado en {name}: {data_type}")
        for flag in ("nullable", "unique"):
            if flag in column and not isinstance(column[flag], bool):
                raise ValueError(f"{flag} debe ser booleano en {name}")
        if "regex" in column and column["regex"] not in PATTERNS:
            raise ValueError(f"Regex desconocida en {name}")
        if "allowed_values" in column:
            values = column["allowed_values"]
            if not isinstance(values, list) or not values:
                raise ValueError(f"allowed_values inválido en {name}")
        if "format" in column and (data_type != "date" or not isinstance(column["format"], str)):
            raise ValueError(f"Formato inválido en {name}")
        if "min" in column or "max" in column:
            if data_type not in {"integer", "decimal"}:
                raise ValueError(f"min/max requieren tipo numérico en {name}")
            for bound in ("min", "max"):
                if bound in column:
                    try:
                        number = Decimal(str(column[bound]))
                        if not number.is_finite():
                            raise ValueError()
                    except (InvalidOperation, ValueError):
                        raise ValueError(f"{bound} inválido en {name}") from None
            if "min" in column and "max" in column:
                if Decimal(str(column["min"])) > Decimal(str(column["max"])):
                    raise ValueError(f"min mayor que max en {name}")
    return True
def validate_csv(csv_path, contract_path, max_errors=1000, progress_callback=None):
    if type(max_errors) is not int or max_errors < 0:
        raise ValueError("max_errors debe ser un entero no negativo")
    contract = load_contract(contract_path)
    config = contract["file"]
    columns = contract["columns"]
    expected = [column["name"] for column in columns]
    result = {
        "contract": contract["contract"]["name"],
        "version": contract["contract"]["version"],
        "status": "REJECTED",
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "error_count": 0,
        "errors": [],
        "errors_truncated": False
    }
    def add_error(row, column, value, message):
        result["error_count"] += 1
        if len(result["errors"]) < max_errors:
            result["errors"].append({
                "row": row,
                "column": column,
                "value": value,
                "message": message
            })
        else:
            result["errors_truncated"] = True
    unique_values = {c["name"]: set() for c in columns if c.get("unique", False)}
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el CSV: {csv_path}")
    with path.open("r", encoding=config.get("encoding", "utf-8"), newline="") as file:
        reader = csv.reader(file, delimiter=config.get("delimiter", ","), strict=True)
        header = next(reader, None)
        if header is None or not header:
            add_error(1, None, None, "El archivo CSV está vacío")
            return result
        if len(header) != len(set(header)):
            add_error(1, None, None, "El CSV contiene columnas duplicadas")
            return result
        for name in expected:
            if name not in header:
                add_error(1, name, None, "Columna obligatoria ausente")
        if not config.get("allow_extra_columns", False):
            for name in header:
                if name not in expected:
                    add_error(1, name, None, "Columna no permitida")
        if result["error_count"]:
            return result
        for values in reader:
            line_number = reader.line_num
            result["total_rows"] += 1
            if progress_callback and result["total_rows"] % 100 == 0:
                progress_callback(result["total_rows"])
            if len(values) != len(header):
                add_error(line_number, None, None, "Número de campos incorrecto")
                result["invalid_rows"] += 1
                continue
            row = dict(zip(header, values))
            row_has_errors = False
            for column in columns:
                name = column["name"]
                value = row[name]
                for message in validate_value(value, column):
                    add_error(line_number, name, value, message)
                    row_has_errors = True
                if name in unique_values and str(value).strip():
                    if value in unique_values[name]:
                        add_error(line_number, name, value, "Valor duplicado")
                        row_has_errors = True
                    else:
                        unique_values[name].add(value)
            if row_has_errors:
                result["invalid_rows"] += 1
            else:
                result["valid_rows"] += 1
    if result["error_count"] == 0:
        result["status"] = "APPROVED"
    return result
