"""Simula la llegada del CSV al Blob Storage: crea los contenedores y sube el CSV a 'landing'.
Uso: python scripts/seed_blob.py data/ComisionEmpleados_V1_202610.csv"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import storage

csv = Path(sys.argv[1])
storage.ensure_containers()
storage.upload_file(storage.LANDING, csv.name, csv)
print(f"CSV {csv.name} cargado en blob {storage.LANDING}/{csv.name}")
