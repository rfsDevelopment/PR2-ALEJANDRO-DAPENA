from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]


def load_csv(filename, required_cols=None):
    path = BASE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"No se encuentra el archivo: {path}")
    df = pd.read_csv(path)
    if required_cols:
        validate_columns(df, required_cols, filename)
    return df


def validate_columns(df, required_cols, filename):
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(
            f"Faltan columnas en {filename}: {', '.join(missing)}"
        )
