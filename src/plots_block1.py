import numpy as np
import matplotlib.pyplot as plt

from src.cleaning import add_decade, add_finish_pos, to_numeric
from src.plot_utils import save_figure


TITLE_B1_01 = "BLOQUE 1 - Línea temporal del % de victorias del equipo dominante por temporada"
TITLE_B1_02 = "BLOQUE 1 - Heatmap década × equipo (share de victorias o puntos)"
TITLE_B1_03 = "BLOQUE 1 - Barras de continuidad: títulos consecutivos"


def plot_b1_01(race_details, output_dir):
    df = race_details.copy()
    df["Year"] = to_numeric(df["Year"])
    df = df.dropna(subset=["Year", "Grand Prix", "Car"])
    df["Year"] = df["Year"].astype(int)
    df = add_finish_pos(df, "Pos")
    winners = df[df["FinishPos"] == 1]

    total_races = df[["Year", "Grand Prix"]].drop_duplicates().groupby("Year").size()
    wins = winners.groupby(["Year", "Car"]).size()
    max_wins = wins.groupby("Year").max()
    pct = (max_wins / total_races).sort_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    if not pct.empty:
        ax.plot(pct.index.astype(int), pct.values * 100)
    ax.set_xlabel("Año")
    ax.set_ylabel("% de victorias del equipo dominante")
    ax.set_title(TITLE_B1_01)

    return save_figure(
        fig,
        output_dir,
        "B1_01_linea_temporal_pct_victorias.png",
        TITLE_B1_01,
        "race_details.csv",
        "Ganadores (Pos=1); años con carreras",
    )


def plot_b1_02(race_details, output_dir):
    df = race_details.copy()
    df = add_finish_pos(df, "Pos")
    df = df[df["FinishPos"] == 1]
    df = add_decade(df, "Year")
    df = df.dropna(subset=["Car"])

    wins_by_decade = df.groupby(["Decade", "Car"]).size().unstack(fill_value=0)
    if wins_by_decade.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_title(TITLE_B1_02)
        ax.set_xlabel("Equipo")
        ax.set_ylabel("Década")
        return save_figure(
            fig,
            output_dir,
            "B1_02_heatmap_decada_equipo.png",
            TITLE_B1_02,
            "race_details.csv",
            "Ganadores (Pos=1); share por década",
        )

    total_wins = wins_by_decade.sum(axis=0).sort_values(ascending=False)
    wins_by_decade = wins_by_decade[total_wins.index]
    share = wins_by_decade.div(wins_by_decade.sum(axis=1), axis=0).fillna(0)

    fig, ax = plt.subplots(figsize=(12, 6))
    im = ax.imshow(share.values, aspect="auto")
    ax.set_xticks(range(len(share.columns)))
    ax.set_xticklabels(share.columns, rotation=90, fontsize=8)
    ax.set_yticks(range(len(share.index)))
    ax.set_yticklabels(share.index.astype(int))
    ax.set_xlabel("Equipo")
    ax.set_ylabel("Década")
    ax.set_title(TITLE_B1_02)
    fig.colorbar(im, ax=ax)

    return save_figure(
        fig,
        output_dir,
        "B1_02_heatmap_decada_equipo.png",
        TITLE_B1_02,
        "race_details.csv",
        "Ganadores (Pos=1); share por década",
    )


def _max_consecutive_years(years):
    max_run = 0
    current = 0
    prev_year = None
    for year in sorted(set(years)):
        if prev_year is None or year == prev_year + 1:
            current += 1
        else:
            current = 1
        if current > max_run:
            max_run = current
        prev_year = year
    return max_run


def _compute_streaks(df, entity_col):
    df = df.copy()
    df["Year"] = to_numeric(df["Year"])
    df["PosNum"] = to_numeric(df["Pos"])
    df = df[(df["PosNum"] == 1) & df["Year"].notna()]
    df["Year"] = df["Year"].astype(int)

    streaks = {}
    for entity, group in df.groupby(entity_col):
        streaks[entity] = _max_consecutive_years(group["Year"].tolist())
    return streaks


def _plot_streaks(streaks, title, filename, ylabel, dataset_label, output_dir):
    items = sorted(streaks.items(), key=lambda item: item[1], reverse=True)[:15]
    labels = [item[0] for item in items][::-1]
    values = [item[1] for item in items][::-1]

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(labels, values)
    ax.set_xlabel("Títulos consecutivos (máximo)")
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    return save_figure(
        fig,
        output_dir,
        filename,
        title,
        dataset_label,
        "Pos=1; racha máxima de años consecutivos",
    )


def plot_b1_03(driver_standings, constructor_standings, output_dir):
    driver_streaks = _compute_streaks(driver_standings, "Driver")
    team_streaks = _compute_streaks(constructor_standings, "Team")

    results = []
    results.append(
        _plot_streaks(
            driver_streaks,
            TITLE_B1_03,
            "B1_03a_rachas_consecutivas_pilotos.png",
            "Piloto",
            "driver_standings.csv",
            output_dir,
        )
    )
    results.append(
        _plot_streaks(
            team_streaks,
            TITLE_B1_03,
            "B1_03b_rachas_consecutivas_equipos.png",
            "Equipo",
            "constructor_standings.csv",
            output_dir,
        )
    )
    return results
