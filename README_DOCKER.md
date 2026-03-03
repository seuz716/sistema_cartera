# 📦 Dockerización del Sistema de Cartera ERP (Senior DevOps)

Este documento detalla la estructura y ejecución del sistema en un entorno de contenedores usando Docker, PostgreSQL y Gunicorn.

---

## 🛠️ Componentes de Infraestructura

1.  **Motor de Base de Datos**: PostgreSQL 15 (Alpine) con persistencia de volumen en `postgres_data`.
2.  **Servidor Web WSGI**: Gunicorn con 3 workers configurados para manejo eficiente de transacciones atómicas.
3.  **Gestión de Estáticos**: WhiteNoise integrado para servir `STATIC_ROOT` y `MEDIA_ROOT`.
4.  **Sistema de Migraciones**: Ejecución automática de `migrate` y `collectstatic` en la entrada del contenedor web.

---

## 🚀 Cómo Iniciar el Sistema (Un solo click)

### Opción 1: Script Ejecutivo (Recomendado)

En la terminal, otorgue permisos una sola vez:

```bash
chmod +x iniciar_sistema.sh
```

Luego, ejecútelo con:

```bash
./iniciar_sistema.sh
```

El script encenderá los contenedores, verificará que estén operativos y le mostrará la dirección IP para acceder al sistema.

### Opción 2: Ejecución Manual con Docker Compose

```bash
docker compose up -d --build
```

---

## 🔒 Variables de Entorno (.env)

El sistema soporta las siguientes variables configurables:

- `DB_NAME`: Nombre de la base de datos (Ej: `cartera_db`).
- `DB_USER`: Usuario administrador.
- `DB_PASSWORD`: Contraseña segura.
- `DJANGO_SECRET_KEY`: Llave secreta única de producción.
- `DJANGO_ALLOWED_HOSTS`: Dominios o IPs permitidas (Ej: `*` o `192.168.1.10`).

---

## 🛡️ Persistencia de Datos y Seguridad

Para validar que la base de datos está persistiendo:

1. Cree un registro en el sistema (ej: un nuevo cliente).
2. Detenga los contenedores: `docker compose down`.
3. Inicie nuevamente: `docker compose up -d`.
4. Verifique el cliente creado: los datos seguirán presentes gracias al volumen `postgres_data`.

**Copia de Seguridad Rápida (Backup SQL):**

```bash
docker exec -t sistema-cartera-db pg_dumpall -c -U admin_user > backup_erp_$(date +%Y%m%d).sql
```

---

## ⚙️ Registro como Servicio del Sistema (Auto-arranque)

Para que el ERP inicie automáticamente al encender el servidor Linux:

Cree el archivo de servicio: `sudo nano /etc/systemd/system/cartera.service`

```ini
[Unit]
Description=Servicio ERP Cartera Docker
After=docker.service
Requires=docker.service

[Service]
Restart=always
WorkingDirectory=/home/usuario/mis_proyectos/sistema_cartera
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
```

Active el servicio:

```bash
sudo systemctl enable cartera.service
sudo systemctl start cartera.service
```

---

## ✅ Checklist de Validación (DevOps)

- [ ] ¿El contenedor `sistema-cartera-db` está en estado _healthy_?
- [ ] ¿Se ejecutaron las migraciones automáticamente en el arranque?
- [ ] ¿El sistema sirve los archivos estáticos (CSS/JS) sin errores 404?
- [ ] ¿Se reemplazó SQLite por PostgreSQL exitosamente?
- [ ] ¿El sistema maneja `select_for_update` sin bloqueos persistentes en Postgres?
