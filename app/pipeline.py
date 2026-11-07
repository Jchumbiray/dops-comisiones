"""Logica del pipeline de comisiones: extraer (SQL + CSV), unir, calcular, exportar Parquet."""
from pathlib import Path
import re
import pandas as pd

CSV_REQUIRED = ["empleado_id", "Comisión"]
DB_REQUIRED = ["empleado_id", "mnt_salario"]


def periodo_from_filename(path) -> str:
    """ComisionEmpleados_V1_202610.csv -> '202610'."""
    m = re.search(r"_(\d{6})\.csv$", Path(path).name)
    if not m:
        raise ValueError(f"No se pudo obtener el periodo (AAAAMM) de {path}")
    return m.group(1)


def read_commission_csv(path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";", encoding="utf-8")
    missing = [c for c in CSV_REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"CSV sin columnas requeridas: {missing}")
    df["Comisión"] = pd.to_numeric(df["Comisión"], errors="raise")
    if df["empleado_id"].duplicated().any():
        raise ValueError("CSV con empleado_id duplicados")
    return df


def read_empleados(db: dict) -> pd.DataFrame:
    import psycopg2
    with psycopg2.connect(**db) as conn, conn.cursor() as cur:
        cur.execute("SELECT empleado_id, tip_documento, num_documento, nom_empleado, "
                    "ape_empleado, cod_cargo, cod_departamento, mnt_salario, "
                    "mnt_tope_comision FROM rrhh.empleado")
        return pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])


def build_consolidated(csv_df: pd.DataFrame, db_df: pd.DataFrame, periodo: str) -> pd.DataFrame:
    """Join por empleado_id y salario_total = salario + comision."""
    missing = [c for c in DB_REQUIRED if c not in db_df.columns]
    if missing:
        raise ValueError(f"Tabla empleado sin columnas requeridas: {missing}")
    merged = csv_df.merge(db_df, on="empleado_id", how="inner")
    merged["mnt_salario"] = pd.to_numeric(merged["mnt_salario"], errors="raise").astype("float64")
    merged = merged.rename(columns={"Comisión": "comision", "Nombre y Apellido": "nombre_apellido_csv"})
    merged["comision"] = merged["comision"].astype("float64")
    merged["salario_total"] = merged["mnt_salario"] + merged["comision"]
    merged["periodo"] = periodo
    return merged.sort_values("empleado_id").reset_index(drop=True)


def unmatched_ids(csv_df: pd.DataFrame, db_df: pd.DataFrame) -> list:
    return sorted(set(csv_df["empleado_id"]) - set(db_df["empleado_id"]))


def write_parquet(df: pd.DataFrame, out_dir, periodo: str) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"empleados_salario_total_{periodo}.parquet"
    df.to_parquet(out, engine="pyarrow", index=False)
    return out
