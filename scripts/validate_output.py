"""Valida el Parquet generado: sin nulos, salario_total == salario + comision."""
import sys, glob, tempfile
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import storage
env = sys.argv[1]
files = glob.glob(f"output/{env}/*.parquet")
assert files, f"No hay parquet en output/{env}"
if storage.enabled():  # validar lo que realmente quedo en el Data Lake
    blobs = storage.list_blobs(storage.DATALAKE, f"{env}/")
    assert blobs, f"No hay parquet en el Data Lake para {env}"
    files = [str(storage.download_file(storage.DATALAKE, blobs[0], Path(tempfile.gettempdir()) / "dl_check.parquet"))]
    print(f"[{env}] Data Lake: {storage.DATALAKE}/{blobs[0]}")
df = pd.read_parquet(files[0])
assert len(df) > 0, "Parquet vacio"
assert df[["empleado_id", "mnt_salario", "comision", "salario_total"]].notna().all().all(), "Hay nulos"
assert ((df.mnt_salario + df.comision - df.salario_total).abs() < 0.005).all(), "salario_total incorrecto"
assert df.empleado_id.is_unique, "empleado_id duplicado"
print(f"[{env}] OK: {len(df)} filas, total salario_total={df.salario_total.sum():.2f}")
