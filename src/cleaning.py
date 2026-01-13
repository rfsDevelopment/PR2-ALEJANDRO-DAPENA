import numpy as np
import pandas as pd


def to_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def add_decade(df, year_col="Year"):
    df = df.copy()
    df[year_col] = to_numeric(df[year_col])
    df = df.dropna(subset=[year_col])
    df[year_col] = df[year_col].astype(int)
    df["Decade"] = (df[year_col] // 10) * 10
    return df


def add_driver_key(df):
    df = df.copy()
    if "DriverCode" in df.columns:
        codes = df["DriverCode"].astype(str).str.strip()
        codes = codes.where(codes != "", np.nan)
        df["DriverKey"] = codes
        df["DriverKey"] = df["DriverKey"].where(df["DriverKey"].notna(), df["Driver"])
    else:
        df["DriverKey"] = df["Driver"]
    return df


def add_finish_pos(df, pos_col="Pos"):
    df = df.copy()
    df["FinishPos"] = to_numeric(df[pos_col])
    return df


def add_grid_pos(df, pos_col="Pos"):
    df = df.copy()
    df["GridPos"] = to_numeric(df[pos_col])
    return df


def spearman_corr(x, y):
    x_series = pd.Series(x)
    y_series = pd.Series(y)
    mask = x_series.notna() & y_series.notna()
    if mask.sum() < 2:
        return np.nan
    x_rank = x_series[mask].rank()
    y_rank = y_series[mask].rank()
    return float(np.corrcoef(x_rank, y_rank)[0, 1])
