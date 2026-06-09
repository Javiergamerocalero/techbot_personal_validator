# Despliegue — VPS Contabo

Guía concreta para levantar el servicio en el mismo VPS donde corre el
backend de visión IA. Asume Ubuntu 22.04+ y nginx ya configurado.

## 1. Postgres

```bash
sudo -u postgres psql <<'SQL'
CREATE USER qapp_user WITH PASSWORD 'STRONG_PASS_HERE';
CREATE DATABASE qapp_employees OWNER qapp_user;
GRANT ALL PRIVILEGES ON DATABASE qapp_employees TO qapp_user;
SQL
```

## 2. Backend

```bash
cd /opt
sudo git clone git@github.com:Javiergamerocalero/qapp-employee-validation-service.git
sudo chown -R deploy:deploy qapp-employee-validation-service
cd qapp-employee-validation-service/backend

python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# editar .env con DATABASE_URL real y ADMIN_TOKEN seguro
alembic upgrade head
```

Probar manualmente:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001
curl http://127.0.0.1:8001/api/v1/health
```

## 3. Supervisor

`/etc/supervisor/conf.d/qapp-employees.conf`:

```ini
[program:qapp-employees]
command=/opt/qapp-employee-validation-service/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 2
directory=/opt/qapp-employee-validation-service/backend
user=deploy
autostart=true
autorestart=true
stopsignal=TERM
stdout_logfile=/var/log/qapp-employees.out.log
stderr_logfile=/var/log/qapp-employees.err.log
environment=PYTHONUNBUFFERED="1"
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status qapp-employees
```

## 4. Frontend

```bash
cd /opt/qapp-employee-validation-service/frontend
npm install
npm run build
# El bundle queda en frontend/dist/
```

## 5. nginx

Agregar al server block del VPS:

```nginx
# Frontend
location /admin/empleados/ {
    alias /opt/qapp-employee-validation-service/frontend/dist/;
    try_files $uri $uri/ /admin/empleados/index.html;
}

# Backend
location /api/v1/employees/ {
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 20M;  # excel files
}
location /api/v1/tenants/ {
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host $host;
}
location /api/v1/health {
    proxy_pass http://127.0.0.1:8001;
}
```

Reload:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 6. Crear primer tenant (San Fernando)

```bash
curl -X POST https://api.tu-dominio.com/api/v1/tenants \
  -H "X-Admin-Token: $(grep ADMIN_TOKEN /opt/qapp-employee-validation-service/backend/.env | cut -d= -f2)" \
  -H "Content-Type: application/json" \
  -d '{"name":"San Fernando","slug":"san-fernando"}'
```

Guardar el `api_key` que devuelve — se muestra una sola vez. Esa es
la key que va al header `X-Tenant-Key` en Qapp.

## 7. Actualización de versión

```bash
cd /opt/qapp-employee-validation-service
git pull
cd backend
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo supervisorctl restart qapp-employees

cd ../frontend
npm install
npm run build
```

## 8. Rotar API key de un tenant comprometido

```bash
curl -X POST https://api.tu-dominio.com/api/v1/tenants/1/rotate \
  -H "X-Admin-Token: ${ADMIN_TOKEN}"
```

Devuelve nueva key. Hay que coordinarla con el equipo Qapp para
cambiarla en el config del quiosco antes de invalidar la vieja —
sino corta el flujo de validación.

## Backups

Para el clúster Postgres:
```bash
0 3 * * * pg_dump -Fc qapp_employees > /backups/qapp_employees_$(date +\%F).dump
```

## Troubleshooting rápido

- **401 "Missing X-Tenant-Key"** → el header no llegó o nginx lo
  filtró. Verificar `proxy_pass_request_headers on;` (default es on).
- **401 "Invalid or inactive tenant key"** → el hash no matchea o el
  tenant está marcado `is_active=false`.
- **422 al importar Excel** → archivo corrupto o sin la hoja
  "Empleados" con los headers esperados.
- **500 inesperado** → revisar `/var/log/qapp-employees.err.log`.
