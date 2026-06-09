# API — Qapp Employee Validation Service

Versión: `0.1.0`. Base path: `/api/v1`.

Todos los endpoints retornan JSON salvo `/employees/template.xlsx` que
devuelve un binario.

## Autenticación

- **`X-Tenant-Key`** (header): API key opaca por tenant. Requerida en
  todos los endpoints bajo `/employees`. Sin ella el server devuelve
  `401 Missing X-Tenant-Key`.
- **`X-Admin-Token`** (header): token estático configurado en el
  `.env` del backend. Requerido para `/tenants/*`.

## Endpoints

### `POST /employees/validate`

Endpoint principal consumido por Qapp en el quiosco.

Headers:
- `X-Tenant-Key: <key>`
- `X-Kiosk-Name: <opcional, ej. KIOSCO-SF-01>`
- `Content-Type: application/json`

Body:
```json
{
  "identifierType": "DNI",
  "identifier": "12345678"
}
```

o

```json
{
  "identifierType": "EMPLOYEE_CODE",
  "identifier": "SF001245"
}
```

Respuestas:

`200 OK` — empleado autorizado:
```json
{
  "success": true,
  "employee": {
    "employeeCode": "SF001245",
    "documentNumber": "12345678",
    "fullName": "Juan Perez Lopez",
    "status": true,
    "statusReason": "ACTIVE",
    "costCenter": "PLANTA CHORRILLOS"
  },
  "message": "Empleado validado"
}
```

`200 OK` — no autorizado / no existe:
```json
{
  "success": false,
  "employee": null,
  "message": "Empleado no autorizado para realizar compras"
}
```

`401` — Key inválida / ausente.

Cada llamada se registra en `validation_logs` con `tenant_id`,
identificador consultado, resultado y nombre del quiosco.

---

### `GET /employees/template.xlsx`

Descarga la plantilla Excel vacía con headers, hoja de catálogos y
data validation para `document_type` y `status_reason`.

Headers: `X-Tenant-Key`.

Response: `200` con `Content-Type:
application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.

---

### `POST /employees/import`

Carga masiva (insert/update por `employee_code`).

Headers: `X-Tenant-Key`. Body: `multipart/form-data` con `file=<xlsx>`.

Response `200`:
```json
{
  "received": 152,
  "inserted": 120,
  "updated": 30,
  "failed": 2,
  "errors": [
    { "row": 7, "column": "document_number", "reason": "Field required" },
    { "row": 33, "column": "status", "reason": "Valor de status no reconocido: 'maybe'" }
  ]
}
```

`400` si el archivo no es `.xlsx`.

---

### `GET /employees`

Listado paginado con búsqueda.

Headers: `X-Tenant-Key`.

Query params:
- `limit` (1-500, default 50)
- `offset` (≥0, default 0)
- `q` (opcional, busca en nombre + código + DNI)

Response `200`:
```json
{
  "total": 1542,
  "items": [
    {
      "id": 1,
      "employeeCode": "SF000001",
      "documentNumber": "12345678",
      "documentType": "DNI",
      "fullName": "Juan Perez Lopez",
      "status": true,
      "statusReason": "ACTIVE",
      "costCenter": "PLANTA CHORRILLOS",
      "updatedAt": "2026-06-09T15:23:00Z"
    }
  ]
}
```

---

### `POST /tenants` (admin)

Crea un tenant nuevo y devuelve su API key en raw (mostrar una sola
vez).

Headers: `X-Admin-Token`.

Body:
```json
{ "name": "San Fernando", "slug": "san-fernando" }
```

Response `201`:
```json
{
  "tenant": {
    "id": 1,
    "name": "San Fernando",
    "slug": "san-fernando",
    "isActive": true,
    "createdAt": "2026-06-09T12:00:00Z"
  },
  "apiKey": "8FJjz7M-XYZ123abcDEF456GHI"
}
```

---

### `GET /tenants` (admin)

Listado simple. Headers: `X-Admin-Token`.

---

### `POST /tenants/{id}/rotate` (admin)

Rota la API key. Devuelve la nueva en raw. Headers: `X-Admin-Token`.

---

### `GET /health`

Liveness check. Sin auth.

```json
{ "status": "ok", "version": "0.1.0" }
```

## Catálogos cerrados

`document_type` (acepta):
- `DNI`
- `CE`
- `PASSPORT`

`status_reason` (acepta — pendiente confirmación final de Javier):
- `ACTIVE`
- `DESVINCULADO`
- `SUSPENDIDO`
- `VACACIONES`
- `OTRO`

Cambios al catálogo: agregar el valor al enum en `app/models/employee.py`
+ migration con `ALTER TYPE … ADD VALUE` o equivalente.
