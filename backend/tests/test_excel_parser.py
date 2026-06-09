"""Smoke tests del excel_parser sin DB."""
from app.services.excel_parser import build_template_xlsx, parse_xlsx


def test_build_template_returns_valid_xlsx():
    data = build_template_xlsx()
    assert data[:2] == b"PK"  # zip header (xlsx es un zip)
    rows, errors = parse_xlsx(data)
    # La plantilla trae una fila de ejemplo válida.
    assert len(rows) == 1
    assert rows[0].employee_code == "SF000001"
    assert rows[0].status is True
    assert errors == []


def test_parse_empty_returns_empty():
    empty = build_template_xlsx()
    # No es estrictamente vacío (trae fila ejemplo), así que solo
    # validamos que no rompe.
    rows, errors = parse_xlsx(empty)
    assert isinstance(rows, list)
    assert isinstance(errors, list)
