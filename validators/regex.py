import re

PATTERNS = {
    "email": r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$",
    "uuid": (
        r"^[0-9a-fA-F]{8}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{12}$"
    ),
    "numeric": r"^\d+$",
    "alphanumeric": r"^[A-Za-z0-9]+$",
}

def validate_regex(value: str, pattern_name: str) -> bool:  
    if pattern_name not in PATTERNS:
        raise ValueError(
            f"Patrón de validación desconocido: {pattern_name}"
        )
    pattern = PATTERNS[pattern_name]
    return re.fullmatch(pattern, str(value)) is not None

#####################################################
#####################################################
## Valida un valor utilizando un patrón predefinido.
#####################################################
#####################################################

# Args:
#     value: Valor a evaluar.
#     pattern_name: Identificador del patrón.
# Returns:
#     True si cumple el patrón; False en caso contrario.
# Raises:
#     ValueError: Si el patrón solicitado no existe.
