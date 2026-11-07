import sys
from pathlib import Path
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import pipeline as p

CSV = Path(__file__).resolve().parents[1] / "data" / "ComisionEmpleados_V1_202610.csv"


def _db():
    return pd.DataFrame({"empleado_id": [1, 2, 3], "mnt_salario": [1000, 2000, 3000],
                         "nom_empleado": ["a", "b", "c"]})


def test_periodo():
    assert p.periodo_from_filename("x/ComisionEmpleados_V1_202610.csv") == "202610"
    with pytest.raises(ValueError):
        p.periodo_from_filename("otro.csv")


def test_salario_total_es_salario_mas_comision():
    csv = pd.DataFrame({"empleado_id": [1, 2], "Nombre y Apellido": ["x", "y"], "Comisión": [100, 50]})
    r = p.build_consolidated(csv, _db(), "202610")
    assert r.loc[r.empleado_id == 1, "salario_total"].item() == 1100
    assert r.loc[r.empleado_id == 2, "salario_total"].item() == 2050
    assert (r["periodo"] == "202610").all()


def test_inner_join_excluye_ids_sin_match():
    csv = pd.DataFrame({"empleado_id": [1, 99], "Nombre y Apellido": ["x", "y"], "Comisión": [1, 1]})
    assert list(p.build_consolidated(csv, _db(), "202610").empleado_id) == [1]
    assert p.unmatched_ids(csv, _db()) == [99]


def test_csv_real_es_valido():
    df = p.read_commission_csv(CSV)
    assert len(df) == 34 and df["Comisión"].min() > 0


def test_csv_duplicados_falla(tmp_path):
    f = tmp_path / "ComisionEmpleados_V1_202610.csv"
    f.write_text("empleado_id;Nombre y Apellido;Comisión\n1;a;1\n1;b;2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        p.read_commission_csv(f)


def test_parquet_roundtrip(tmp_path):
    csv = pd.DataFrame({"empleado_id": [1], "Nombre y Apellido": ["x"], "Comisión": [100]})
    out = p.write_parquet(p.build_consolidated(csv, _db(), "202610"), tmp_path, "202610")
    back = pd.read_parquet(out)
    assert out.exists() and back.salario_total.iloc[0] == 1100
