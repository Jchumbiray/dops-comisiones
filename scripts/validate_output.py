"""Valida el Parquet generado: sin nulos, salario_total == salario + comision."""
import sys, glob
import pandas as pd
env = sys.argv[1]
files = glob.glob(f"output/{env}/*.parquet")
assert files, f"No hay parquet en output/{env}"
df = pd.read_parquet(files[0])
assert len(df) > 0, "Parquet vacio"
assert df[["empleado_id", "mnt_salario", "comision", "salario_total"]].notna().all().all(), "Hay nulos"
assert ((df.mnt_salario + df.comision - df.salario_total).abs() < 0.005).all(), "salario_total incorrecto"
assert df.empleado_id.is_unique, "empleado_id duplicado"
print(f"[{env}] OK: {len(df)} filas, total salario_total={df.salario_total.sum():.2f}")
