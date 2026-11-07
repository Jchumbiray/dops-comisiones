"""Acceso a Azure Blob Storage / Data Lake (ADLS) con el SDK oficial de Azure.
En desarrollo se usa el emulador Azurite; en Azure real solo cambia la cadena de conexion
(AZURE_STORAGE_CONNECTION_STRING)."""
import os
from pathlib import Path

LANDING = os.getenv("BLOB_CONTAINER_LANDING", "landing")    # donde llega el CSV de comisiones
DATALAKE = os.getenv("BLOB_CONTAINER_DATALAKE", "datalake")  # donde se escribe el Parquet


def enabled() -> bool:
    return bool(os.getenv("AZURE_STORAGE_CONNECTION_STRING"))


def datalake_path(env: str, periodo: str) -> str:
    """Ruta del Parquet dentro del contenedor datalake, separada por entorno."""
    return f"{env}/rrhh/empleados_salario_total_{periodo}.parquet"


def _service():
    from azure.storage.blob import BlobServiceClient
    return BlobServiceClient.from_connection_string(os.environ["AZURE_STORAGE_CONNECTION_STRING"])


def ensure_containers() -> None:
    svc = _service()
    for name in (LANDING, DATALAKE):
        c = svc.get_container_client(name)
        if not c.exists():
            c.create_container()


def upload_file(container: str, blob_name: str, local_path) -> None:
    with open(local_path, "rb") as fh:
        _service().get_blob_client(container, blob_name).upload_blob(fh, overwrite=True)


def download_file(container: str, blob_name: str, local_path) -> Path:
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    data = _service().get_blob_client(container, blob_name).download_blob().readall()
    local_path.write_bytes(data)
    return local_path


def list_blobs(container: str, prefix: str = "") -> list:
    return [b.name for b in _service().get_container_client(container).list_blobs(name_starts_with=prefix)]
