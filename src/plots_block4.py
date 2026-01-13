import numpy as np
import matplotlib.pyplot as plt

from src.cleaning import add_decade, add_driver_key, add_finish_pos, to_numeric
from src.plot_utils import save_figure


TITLE_B4_01 = "BLOQUE 4 - % de puntos del mundial procedentes del sprint"
TITLE_B4_02 = "BLOQUE 4 - Cambios de posición inducidos por el sprint"
TITLE_B4_03 = "BLOQUE 4 - Imprevisibilidad: sprint vs no sprint"
TITLE_B4_04 = "BLOQUE 4 - Sprint y campeonatos decididos"


def plot_b4_01(sprint_results, driver_standings, output_dir):
    sprint = sprint_results.copy()
    sprint["Year"] = to_numeric(sprint["Year"])
    sprint["PTS"] = to_numeric(sprint["PTS"])
    sprint = sprint.dropna(subset=["Year", "PTS"])

    standings = driver_standings.copy()
    standings["Year"] = to_numeric(standings["Year"])
    standings["PTS"] = to_numeric(standings["PTS"])
    standings = standings.dropna(subset=["Year", "PTS"])

    sprint_points = sprint.groupby("Year")["PTS"].sum()
    total_points = standings.groupby("Year")["PTS"].sum()

    share = (sprint_points / total_points).dropna().sort_index() * 100

    fig, ax = plt.subplots(figsize=(10, 5))
    if not share.empty:
        ax.bar(share.index.astype(int), share.values)
    ax.set_xlabel("Año")
    ax.set_ylabel("% puntos sprint")
    ax.set_title(TITLE_B4_01)

    return save_figure(
        fig,
        output_dir,
        "B4_01_pct_puntos_sprint.png",
        TITLE_B4_01,
        "sprint_results.csv, driver_standings.csv",
        "Años con sprint",
    )


def plot_b4_02(sprint_results, sprint_grid, starting_grids, output_dir):
    res = add_driver_key(sprint_results)
    res["Year"] = to_numeric(res["Year"])
    res["SprintPos"] = to_numeric(res["Pos"])

    grid = add_driver_key(sprint_grid)
    grid["Year"] = to_numeric(grid["Year"])
    grid["SprintGrid"] = to_numeric(grid["Pos"])

    sunday = add_driver_key(starting_grids)
    sunday["Year"] = to_numeric(sunday["Year"])
    sunday["SundayGrid"] = to_numeric(sunday["Pos"])

    merged = res.merge(
        grid[["Year", "Grand Prix", "DriverKey", "SprintGrid"]],
        on=["Year", "Grand Prix", "DriverKey"],
        how="inner",
    )
    merged = merged.merge(
        sunday[["Year", "Grand Prix", "DriverKey", "SundayGrid"]],
        on=["Year", "Grand Prix", "DriverKey"],
        how="left",
    )

    note = "Delta = grid domingo - posición sprint"
    missing = merged["SundayGrid"].isna().sum()
    if missing > 0:
        merged["SundayGrid"] = merged["SundayGrid"].fillna(merged["SprintGrid"])
        note = (
            "Delta = grid domingo - posición sprint; "
            "grid domingo faltante usa grid sprint como proxy"
        )

    merged = merged.dropna(subset=["SundayGrid", "SprintPos"])
    merged["Delta"] = merged["SundayGrid"] - merged["SprintPos"]

    fig, ax = plt.subplots(figsize=(10, 5))
    if not merged.empty:
        ax.hist(merged["Delta"].values, bins=30)
    ax.set_xlabel("Cambio de posición")
    ax.set_ylabel("Frecuencia")
    ax.set_title(TITLE_B4_02)

    return save_figure(
        fig,
        output_dir,
        "B4_02_cambios_posicion_sprint.png",
        TITLE_B4_02,
        "sprint_results.csv, sprint_grid.csv, starting_grids.csv",
        "Delta = grid domingo - posición sprint",
        note=note,
    )


def plot_b4_03(race_details, sprint_results, output_dir):
    race = add_finish_pos(race_details, "Pos")
    race["Year"] = to_numeric(race["Year"])
    race = race.dropna(subset=["Year", "Grand Prix", "FinishPos"])
    race = race[race["FinishPos"] <= 10]

    variance = (
        race.groupby(["Year", "Grand Prix"])["FinishPos"]
        .var()
        .reset_index()
    )

    sprint_keys = sprint_results[["Year", "Grand Prix"]].drop_duplicates()
    sprint_keys["Year"] = to_numeric(sprint_keys["Year"])
    sprint_set = set(
        tuple(x) for x in sprint_keys[["Year", "Grand Prix"]].dropna().values
    )

    variance["Sprint"] = variance.apply(
        lambda row: (row["Year"], row["Grand Prix"]) in sprint_set, axis=1
    )

    data = [
        variance.loc[variance["Sprint"], "FinishPos"].dropna().values,
        variance.loc[~variance["Sprint"], "FinishPos"].dropna().values,
    ]

    fig, ax = plt.subplots(figsize=(8, 5))
    if any(len(d) > 0 for d in data):
        ax.boxplot(data, labels=["Con sprint", "Sin sprint"])
    ax.set_ylabel("Varianza de posiciones top-10")
    ax.set_title(TITLE_B4_03)

    note = "Carrera con sprint = aparece en sprint_results.csv"

    return save_figure(
        fig,
        output_dir,
        "B4_03_imprevisibilidad_sprint.png",
        TITLE_B4_03,
        "race_details.csv, sprint_results.csv",
        "Top-10; varianza por carrera",
        note=note,
    )


def plot_b4_04(sprint_results, driver_standings, output_dir):
    sprint = add_driver_key(sprint_results)
    sprint["Year"] = to_numeric(sprint["Year"])
    sprint["PTS"] = to_numeric(sprint["PTS"])
    sprint = sprint.dropna(subset=["Year", "PTS", "DriverKey"])

    standings = add_driver_key(driver_standings)
    standings["Year"] = to_numeric(standings["Year"])
    standings["PTS"] = to_numeric(standings["PTS"])
    standings["Pos"] = to_numeric(standings["Pos"])
    standings = standings.dropna(subset=["Year", "PTS", "Pos", "DriverKey"])

    sprint_points = (
        sprint.groupby(["Year", "DriverKey"])["PTS"].sum().reset_index()
    )

    rows = []
    for year in sprint_points["Year"].unique():
        standings_year = standings[standings["Year"] == year]
        champ = standings_year[standings_year["Pos"] == 1]
        runner = standings_year[standings_year["Pos"] == 2]
        if champ.empty or runner.empty:
            continue

        champ_pts = float(champ.iloc[0]["PTS"])
        runner_pts = float(runner.iloc[0]["PTS"])
        margin = champ_pts - runner_pts

        champ_key = champ.iloc[0]["DriverKey"]
        runner_key = runner.iloc[0]["DriverKey"]

        sprint_champ = sprint_points[
            (sprint_points["Year"] == year)
            & (sprint_points["DriverKey"] == champ_key)
        ]["PTS"].sum()
        sprint_runner = sprint_points[
            (sprint_points["Year"] == year)
            & (sprint_points["DriverKey"] == runner_key)
        ]["PTS"].sum()

        rows.append((int(year), margin, sprint_champ - sprint_runner))

    fig, ax = plt.subplots(figsize=(8, 6))
    if rows:
        margins = [row[1] for row in rows]
        impacts = [row[2] for row in rows]
        ax.scatter(margins, impacts)
        max_val = max(margins + impacts + [0])
        min_val = min(margins + impacts + [0])
        ax.plot([min_val, max_val], [min_val, max_val])

    ax.set_xlabel("Margen final campeón - subcampeón")
    ax.set_ylabel("Impacto sprint (campeón - subcampeón)")
    ax.set_title(TITLE_B4_04)

    note = "Años con sprint identificados por sprint_results.csv"

    return save_figure(
        fig,
        output_dir,
        "B4_04_sprint_campeonatos.png",
        TITLE_B4_04,
        "sprint_results.csv, driver_standings.csv",
        "Pos=1 vs Pos=2; puntos sprint por piloto",
        note=note,
    )
