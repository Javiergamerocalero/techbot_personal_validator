"""Parseo + validación de filas del Excel de empleados.

Schema confirmado con Javier 2026-06-09 21:03 — columnas:
employee_code, document_number, document_type, full_name, status,
status_reason, tenant_name. Sin cost_center.

`status` se acepta como string libre ("Active" / "Inactive") con
normalización case-insensitive en el Pydantic schema.
"""
import io
from typing import IO

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from pydantic import ValidationError

from app.models.employee import DocumentType, STATUS_ACTIVE, STATUS_INACTIVE
from app.schemas.employee import (
    EmployeeImportRow,
    ImportError as ImportErrorSchema,
)


HEADERS = [
    "employee_code",
    "document_number",
    "document_type",
    "full_name",
    "status",
    "status_reason",
    "tenant_name",
]

_DOC_TYPES = [t.value for t in DocumentType]
_STATUSES = [STATUS_ACTIVE, STATUS_INACTIVE]


def build_template_xlsx() -> bytes:
    """Genera el `.xlsx` plantilla.

    Hoja "Empleados" con headers, fila de ejemplo y data validation
    en columnas de enums (document_type, status). Hoja "Catalogos"
    muestra los valores válidos.
    """
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Empleados"

    header_fill = PatternFill(
        start_color="222B57", end_color="222B57", fill_type="solid"
    )
    header_font = Font(color="FFFFFF", bold=True)
    for col_idx, header in enumerate(HEADERS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[get_column_letter(col_idx)].width = max(
            len(header) + 4, 18
        )

    cat_ws = wb.create_sheet(title="Catalogos")
    cat_ws.cell(row=1, column=1, value="document_type").font = Font(bold=True)
    cat_ws.cell(row=1, column=2, value="status").font = Font(bold=True)
    for i, v in enumerate(_DOC_TYPES, start=2):
        cat_ws.cell(row=i, column=1, value=v)
    for i, v in enumerate(_STATUSES, start=2):
        cat_ws.cell(row=i, column=2, value=v)

    # Data validation:
    # - Columna C (3) = document_type
    # - Columna E (5) = status
    dv_doctype = DataValidation(
        type="list",
        formula1=f'"{",".join(_DOC_TYPES)}"',
        allow_blank=True,
    )
    dv_doctype.add("C2:C1048576")
    ws.add_data_validation(dv_doctype)

    dv_status = DataValidation(
        type="list",
        formula1=f'"{",".join(_STATUSES)}"',
        allow_blank=True,
    )
    dv_status.add("E2:E1048576")
    ws.add_data_validation(dv_status)

    ws.append(
        [
            "SF000001",
            "12345678",
            "DNI",
            "Juan Perez Lopez",
            STATUS_ACTIVE,
            "",  # status_reason vacío cuando está Active
            "San Fernando",
        ]
    )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def parse_xlsx(
    file_bytes: bytes | IO[bytes],
) -> tuple[list[EmployeeImportRow], list[ImportErrorSchema]]:
    if isinstance(file_bytes, (bytes, bytearray)):
        stream: IO[bytes] = io.BytesIO(file_bytes)
    else:
        stream = file_bytes
    try:
        wb = load_workbook(stream, read_only=True, data_only=True)
    except Exception as e:
        return (
            [],
            [
                ImportErrorSchema(
                    row=0,
                    column=None,
                    reason=f"No se pudo abrir el archivo: {e}",
                )
            ],
        )

    ws = wb.active
    if ws is None:
        return [], [
            ImportErrorSchema(row=0, column=None, reason="Hoja vacía")
        ]

    rows_iter = ws.iter_rows(values_only=True)
    try:
        header_row = next(rows_iter)
    except StopIteration:
        return [], [
            ImportErrorSchema(row=0, column=None, reason="Archivo vacío")
        ]

    header_map: dict[str, int] = {}
    for idx, h in enumerate(header_row):
        if h is None:
            continue
        normalized = str(h).strip().lower()
        if normalized in HEADERS:
            header_map[normalized] = idx

    missing = [h for h in HEADERS if h not in header_map]
    if missing:
        return [], [
            ImportErrorSchema(
                row=1,
                column=", ".join(missing),
                reason=f"Faltan columnas: {', '.join(missing)}",
            )
        ]

    valid: list[EmployeeImportRow] = []
    errors: list[ImportErrorSchema] = []

    for row_num, row in enumerate(rows_iter, start=2):
        if row is None or all(c in (None, "") for c in row):
            continue
        try:
            data = {
                "employee_code": _str_or_none(row[header_map["employee_code"]]),
                "document_number": _str_or_none(
                    row[header_map["document_number"]]
                ),
                "document_type": _str_or_default(
                    row[header_map["document_type"]], "DNI"
                ),
                "full_name": _str_or_none(row[header_map["full_name"]]),
                "status": _str_or_default(row[header_map["status"]], "Active"),
                "status_reason": _str_or_none(
                    row[header_map["status_reason"]]
                ),
                "tenant_name": _str_or_none(row[header_map["tenant_name"]]),
            }
            parsed = EmployeeImportRow.model_validate(data)
            valid.append(parsed)
        except ValidationError as ve:
            for err in ve.errors():
                loc = ".".join(str(p) for p in err["loc"]) or None
                errors.append(
                    ImportErrorSchema(
                        row=row_num, column=loc, reason=err["msg"]
                    )
                )
        except Exception as e:  # noqa: BLE001
            errors.append(
                ImportErrorSchema(
                    row=row_num,
                    column=None,
                    reason=f"Error inesperado: {e}",
                )
            )

    return valid, errors


def _str_or_none(v) -> str | None:  # noqa: ANN001
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _str_or_default(v, default: str) -> str:  # noqa: ANN001
    s = _str_or_none(v)
    return s if s is not None else default
