# DataOps – Cálculo de comisiones de empleados

[![CI](https://github.com/Jchumbiray/dops-comisiones/actions/workflows/ci.yml/badge.svg)](https://github.com/Jchumbiray/dops-comisiones/actions/workflows/ci.yml)

Pipeline en Python que combina la tabla `rrhh.empleado` (PostgreSQL) con el CSV de comisiones
`ComisionEmpleados_V1_202610.csv`, calcula `salario_total = salario + comisión` y genera un
archivo **Parquet**. El despliegue se automatiza con **Jenkins** (CI/CD) en tres entornos:
`dev → test → prod`, con aprobación manual antes de TEST y PROD.

## Contenido del repositorio

```
├── app/
│   ├── pipeline.py        # Lógica: lectura, validación, join, cálculo y escritura Parquet
│   ├── main.py            # Punto de entrada (CLI: --env dev|test|prod)
│   ├── storage.py         # Azure Blob Storage / Data Lake (SDK azure-storage-blob)
│   └── requirements.txt
├── data/ComisionEmpleados_V1_202610.csv
├── tests/test_pipeline.py # Pruebas unitarias (pytest)
├── scripts/validate_output.py  # Validación del Parquet (lee del Data Lake)
├── scripts/seed_blob.py        # Crea contenedores y sube el CSV a Blob (landing)
├── .github/workflows/ci.yml    # CI en GitHub Actions (pytest en cada push)
├── Jenkinsfile            # Pipeline CI/CD
├── jenkins/               # Imagen de Jenkins (Dockerfile, plugins, config como código)
├── docker-compose.yml     # Levanta Jenkins + Azurite (emulador de Azure Storage)
└── .env.example           # Variables necesarias (el .env real NO se versiona)
```

## Flujo del pipeline

1. Descarga el CSV desde **Azure Blob Storage** (contenedor `landing`), lo lee (separador `;`) y valida columnas, tipos y `empleado_id` duplicados.
2. Extrae `rrhh.empleado` de PostgreSQL (usuario de solo lectura).
3. *Inner join* por `empleado_id`. Los IDs del CSV que no existen en la BD se excluyen y se registran como `WARNING`.
4. `salario_total = mnt_salario + comision`, y se agrega la columna `periodo` (tomada del nombre del CSV).
5. Escribe el Parquet en el **Data Lake** (contenedor `datalake`, ruta `<env>/rrhh/empleados_salario_total_<periodo>.parquet`) y una copia en `output/<env>/`.

El almacenamiento se usa si existe la variable `AZURE_STORAGE_CONNECTION_STRING`; sin ella el pipeline trabaja solo con archivos locales. En desarrollo se usa el emulador **Azurite**; en Azure real solo cambia la cadena de conexión.

## Ejecución local (sin Jenkins)

```bash
pip install -r app/requirements.txt pytest
pytest -v
export DB_HOST=mgg.vps.webdock.cloud DB_NAME=dmc DB_USER=<usuario> DB_PASSWORD=<password>
python app/main.py --env dev
python scripts/validate_output.py dev
```

## Despliegue CI/CD con Jenkins

1. Copiar `.env.example` a `.env` y completar `DB_PASSWORD`, `JENKINS_ADMIN_PASSWORD` y `REPO_URL`.
2. `docker compose up -d --build` → Jenkins en http://localhost:8090 (usuario `admin`).
   El usuario/clave de la BD se registran como credencial `dmc-db` y el job `pipeline-comisiones` se crea automáticamente.
3. Ejecutar **Build Now** (o hacer `git push`: el pipeline consulta el repo cada 2 min con `pollSCM`).
4. Etapas: `CI Preparar entorno → CI Pruebas unitarias → CD Preparar Blob Storage → CD DEV (automático) → Aprobación TEST → CD TEST → Aprobación PROD → CD PROD`.
   En las aprobaciones, pulsar **Desplegar a TEST / PROD** en la vista de la ejecución.
5. Los Parquet quedan como artefactos de cada build.

> Con un Jenkins accesible desde internet, se puede reemplazar `pollSCM` por un webhook de GitHub
> (`http://<host>/github-webhook/`).

## CI en GitHub Actions
En cada `push` a `main` y en cada Pull Request se ejecutan las pruebas (`.github/workflows/ci.yml`); el resultado se ve en la pestaña **Actions** y en el badge de arriba.

## Seguridad
Las credenciales no están en el repositorio: viajan por variables de entorno y por el almacén de credenciales de Jenkins.
