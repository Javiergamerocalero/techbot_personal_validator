# Qapp Employee Validation Service

Servicio de validación de empleados para venta interna en quioscos
Qapp. El cliente (San Fernando — primer tenant) carga un Excel con
sus colaboradores autorizados, y el quiosco Qapp consulta este API
para decidir si un empleado puede comprar o no.

Multi-tenant desde el día 0: el mismo servicio sirve a N clientes,
cada uno con su propia data aislada por `tenant_id`.

## Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy 2 async, Alembic,
  Postgres.
- **Frontend**: React 19 + Vite + TypeScript + Tailwind 4.
- **Hosting**: VPS Contabo (mismo donde corre el backend de visión
  IA — nginx delante, supervisor para el service).

## Estructura

```
qapp-employee-validation-service/
├── backend/                   FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── core/              config, db, security, logging
│   │   ├── models/            ORM (Tenant, Employee, ValidationLog)
│   │   ├── schemas/           Pydantic in/out
│   │   ├── routers/           endpoints
│   │   └── services/          lógica (excel parser, validation)
│   ├── alembic/               migrations
│   ├── tests/                 pytest
│   ├── requirements.txt
│   └── .env.example
├── frontend/                  React + Vite admin panel
│   ├── src/
│   │   ├── components/        DropZone, PreviewTable, etc.
│   │   ├── api/               client tipado
│   │   └── types/             tipos compartidos
│   └── package.json
├── postman/
│   └── collection.json        endpoints listos para probar
└── docs/
    └── deployment.md          guía de despliegue en Contabo
```

## Endpoints principales

| Method | Path | Auth | Descripción |
|---|---|---|---|
| `POST` | `/api/v1/employees/validate` | `X-Tenant-Key` | Valida un empleado por DNI o código. Es el endpoint que consume Qapp. |
| `GET` | `/api/v1/employees/template.xlsx` | `X-Tenant-Key` | Descarga la plantilla Excel vacía con headers + hoja de status. |
| `POST` | `/api/v1/employees/import` | `X-Tenant-Key` | Carga masiva desde Excel. Valida cada fila antes de insertar. |
| `GET` | `/api/v1/employees` | `X-Tenant-Key` | Lista paginada de empleados del tenant. |
| `POST` | `/api/v1/tenants` | Admin | (Admin) Crea un tenant nuevo y devuelve su API key. |
| `GET` | `/api/v1/health` | — | Health check. |

Detalle de payloads en [docs/api.md](docs/api.md) o en la
[colección Postman](postman/collection.json).

## Autenticación

Cada tenant tiene una **API key** (header `X-Tenant-Key`) generada al
darlo de alta. El servicio resuelve el `tenant_id` server-side desde
esa key. Qapp NO manda `tenant_id` en el body.

Para endpoints administrativos (alta de tenant) se usa un token
separado `ADMIN_TOKEN` configurado en el `.env` del servicio (header
`X-Admin-Token`).

## Setup local

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # editar con tus credenciales de Postgres
alembic upgrade head
uvicorn app.main:app --reload --port 8001
```

API disponible en `http://localhost:8001/api/v1/`. Docs interactivos
en `http://localhost:8001/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI en `http://localhost:5173`.

## Despliegue en VPS Contabo

Ver [docs/deployment.md](docs/deployment.md) — configuración nginx,
supervisor, certbot y migrations en producción.

## Variables de entorno (backend)

| Var | Descripción | Default |
|---|---|---|
| `DATABASE_URL` | Postgres connection string (async) | — |
| `ADMIN_TOKEN` | Token para endpoints admin | — |
| `CORS_ORIGINS` | Lista coma-separada para CORS | `http://localhost:5173` |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` | `INFO` |
| `KIOSK_NAME_HEADER` | Header opcional para log de quiosco | `X-Kiosk-Name` |

## Estado del proyecto

Iteración inicial. Confirmado con Javier (TechBot) 2026-06-09:
- FastAPI + Postgres ✅
- React + Tailwind ✅
- Auth `X-Tenant-Key` ✅
- Excel `.xlsx` ✅
- `status_reason` catálogo cerrado ✅

Pendiente:
- Lista exacta de valores del enum `status_reason` (placeholder con
  4 valores genéricos en la migración inicial).
- Repo destino en GitHub (Javier va a mandar invitación).
