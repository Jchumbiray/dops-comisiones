"""Punto de entrada. Uso: python app/main.py --env dev [--csv data/ComisionEmpleados_V1_202610.csv]
Credenciales por variables de entorno (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)."""
import argparse, logging, os, sys
from pathlib import Path
import pipeline as p

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("comisiones")


def db_config() -> dict:
    try:
        return dict(host=os.environ["DB_HOST"], port=int(os.getenv("DB_PORT", "5432")),
                    dbname=os.environ["DB_NAME"], user=os.environ["DB_USER"],
                    password=os.environ["DB_PASSWORD"], connect_timeout=15)
    except KeyError as e:
        sys.exit(f"Falta la variable de entorno {e}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", choices=["dev", "test", "prod"], required=True)
    ap.add_argument("--csv", default="data/ComisionEmpleados_V1_202610.csv")
    ap.add_argument("--out", default="output")
    a = ap.parse_args()

    periodo = p.periodo_from_filename(a.csv)
    log.info("Entorno=%s periodo=%s", a.env, periodo)
    csv_df = p.read_commission_csv(a.csv)
    log.info("CSV leido: %d filas", len(csv_df))
    db_df = p.read_empleados(db_config())
    log.info("Tabla rrhh.empleado leida: %d filas", len(db_df))
    for i in p.unmatched_ids(csv_df, db_df):
        log.warning("empleado_id %s esta en el CSV pero no en la BD (excluido)", i)
    result = p.build_consolidated(csv_df, db_df, periodo)
    out = p.write_parquet(result, Path(a.out) / a.env, periodo)
    log.info("Parquet generado: %s (%d filas, salario_total suma=%.2f)", out, len(result), result["salario_total"].sum())


if __name__ == "__main__":
    main()
