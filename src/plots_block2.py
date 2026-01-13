import numpy as np
import matplotlib.pyplot as plt

from src.cleaning import (
    add_decade,
    add_driver_key,
    add_finish_pos,
    add_grid_pos,
    spearman_corr,
    to_numeric,
)
from src.plot_utils import save_figure

try:
    from scipy.stats import spearmanr
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False


TITLE_B2_01 = "BLOQUE 2 - Correlación Grid ↔ Posición final por temporada"
TITLE_B2_02 = "BLOQUE 2 - Probabilidad de podio según posición de salida (por décadas)"
TITLE_B2_03 = "BLOQUE 2 - Boxplot de posiciones ganadas/perdidas por década"


def _merge_race_grid(race_details, starting_grids):
    race = add_driver_key(add_finish_pos(race_details, "Pos"))
    grid = add_driver_key(add_grid_pos(starting_grids, "Pos"))

    race["Year"] = to_numeric(race["Year"])
    grid["Year"] = to_numeric(grid["Year"])

    race = race.dropna(subset=["Year", "Grand Prix", "DriverKey"])
    grid = grid.dropna(subset=["Year", "Grand Prix", "DriverKey"])

    merged = race.merge(
        grid[["Year", "Grand Prix", "DriverKey", "GridPos"]],
        on=["Year", "Grand Prix", "DriverKey"],
        how="inner",
    )
    return merged


def _spearman(x, y):
    if _HAS_SCIPY:
        value, _ = spearmanr(x, y, nan_policy="omit")
        return value
    return spearman_corr(x, y)


def plot_b2_01(race_details, starting_grids, output_dir):
    merged = _merge_race_grid(race_details, starting_grids)
    merged = merged.dropna(subset=["FinishPos", "GridPos"])

    rows = []
    for year, group in merged.groupby("Year"):
        rho = _spearman(group["GridPos"], group["FinishPos"])
        if not np.isnan(rho):
            rows.append((int(year), rho))

    rows.sort(key=lambda item: item[0])
    years = [item[0] for item in rows]
    rhos = [item[1] for item in rows]

    fig, ax = plt.subplots(figsize=(10, 5))
    if rows:
        ax.plot(years, rhos)
    ax.set_xlabel("Año")
    ax.set_ylabel("Rho (Spearman)")
    ax.set_title(TITLE_B2_01)

    return save_figure(
        fig,
        output_dir,
        "B2_01_correlacion_grid_posicion.png",
        TITLE_B2_01,
        "race_details.csv, starting_grids.csv",
        "Excluye DNFs (posición final no numérica)",
        note="Excluye DNFs",
    )


def plot_b2_02(race_details, starting_grids, output_dir):
    merged = _merge_race_grid(race_details, starting_grids)
    merged = merged.dropna(subset=["FinishPos", "GridPos"])
    merged = add_decade(merged, "Year")
    merged["Podium"] = merged["FinishPos"] <= 3

    fig, ax = plt.subplots(figsize=(10, 6))
    for decade, group in merged.groupby("Decade"):
        prob = (
            group.groupby("GridPos")["Podium"].mean().reset_index()
        )
        prob = prob.dropna(subset=["GridPos"])
        if not prob.empty:
            ax.plot(prob["GridPos"], prob["Podium"], label=str(int(decade)))

    ax.set_xlabel("Posición de salida")
    ax.set_ylabel("Probabilidad de podio")
    ax.set_title(TITLE_B2_02)
    ax.legend(title="Década")

    return save_figure(
        fig,
        output_dir,
        "B2_02_prob_podio_grid_decadas.png",
        TITLE_B2_02,
        "race_details.csv, starting_grids.csv",
        "Excluye DNFs (posición final no numérica)",
        note="Excluye DNFs",
    )


def plot_b2_03(race_details, starting_grids, output_dir):
    merged = _merge_race_grid(race_details, starting_grids)
    merged = merged.dropna(subset=["FinishPos", "GridPos"])
    merged = add_decade(merged, "Year")
    merged["Delta"] = merged["FinishPos"] - merged["GridPos"]

    data = []
    labels = []
    for decade, group in merged.groupby("Decade"):
        values = group["Delta"].dropna().values
        if len(values) > 0:
            data.append(values)
            labels.append(str(int(decade)))

    fig, ax = plt.subplots(figsize=(10, 6))
    if data:
        ax.boxplot(data, labels=labels)
    ax.set_xlabel("Década")
    ax.set_ylabel("Posiciones ganadas/perdidas (final - grid)")
    ax.set_title(TITLE_B2_03)

    return save_figure(
        fig,
        output_dir,
        "B2_03_boxplot_posiciones_ganadas.png",
        TITLE_B2_03,
        "race_details.csv, starting_grids.csv",
        "Excluye DNFs (posición final no numérica)",
        note="Excluye DNFs",
    )
