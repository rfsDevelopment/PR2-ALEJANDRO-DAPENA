import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.cleaning import (
    add_decade,
    add_driver_key,
    add_finish_pos,
    add_grid_pos,
    spearman_corr,
    to_numeric,
)

try:
    from scipy.stats import spearmanr
    _HAS_SCIPY = True
except Exception:
    _HAS_SCIPY = False

try:
    import statsmodels.api as sm
    _HAS_STATSMODELS = True
except Exception:
    _HAS_STATSMODELS = False


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=True)


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


def _pit_time_column(pitstops):
    if "Time" in pitstops.columns:
        return "Time"
    if "Total" in pitstops.columns:
        return "Total"
    raise ValueError("pitstops.csv no contiene columnas de duracion (Time/Total)")


def _merge_pit_race(pitstops, race_details):
    pit = add_driver_key(pitstops)
    pit["Year"] = to_numeric(pit["Year"])
    pit_time_col = _pit_time_column(pit)
    pit["PitTime"] = to_numeric(pit[pit_time_col])
    pit = pit.dropna(subset=["PitTime", "Year", "Grand Prix", "DriverKey"])

    pit_agg = (
        pit.groupby(["Year", "Grand Prix", "DriverKey"])["PitTime"]
        .agg(total_pit_time="sum", n_stops="size")
        .reset_index()
    )

    race = add_driver_key(add_finish_pos(race_details, "Pos"))
    race["Year"] = to_numeric(race["Year"])
    race = race.dropna(subset=["FinishPos", "Year", "Grand Prix", "DriverKey"])

    merged = pit_agg.merge(
        race[["Year", "Grand Prix", "DriverKey", "FinishPos"]],
        on=["Year", "Grand Prix", "DriverKey"],
        how="inner",
    )
    return merged


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


def export_interactive_data(
    race_details,
    driver_standings,
    constructor_standings,
    starting_grids,
    pitstops,
    sprint_results,
    sprint_grid,
    output_dir,
):
    data_dir = Path(output_dir) / "data"

    # B1_01
    df = race_details.copy()
    df["Year"] = to_numeric(df["Year"])
    df = df.dropna(subset=["Year", "Grand Prix", "Car"])
    df["Year"] = df["Year"].astype(int)
    df = add_finish_pos(df, "Pos")
    winners = df[df["FinishPos"] == 1]
    total_races = df[["Year", "Grand Prix"]].drop_duplicates().groupby("Year").size()
    wins = winners.groupby(["Year", "Car"]).size()
    max_wins = wins.groupby("Year").max()
    pct = (max_wins / total_races).sort_index() * 100
    _write_json(
        data_dir / "b1_01.json",
        {"years": pct.index.astype(int).tolist(), "pct": pct.values.tolist()},
    )

    # B1_02
    df = race_details.copy()
    df = add_finish_pos(df, "Pos")
    df = df[df["FinishPos"] == 1]
    df = add_decade(df, "Year")
    df = df.dropna(subset=["Car"])
    wins_by_decade = df.groupby(["Decade", "Car"]).size().unstack(fill_value=0)
    if not wins_by_decade.empty:
        total_wins = wins_by_decade.sum(axis=0).sort_values(ascending=False)
        wins_by_decade = wins_by_decade[total_wins.index]
        share = wins_by_decade.div(wins_by_decade.sum(axis=1), axis=0).fillna(0)
        _write_json(
            data_dir / "b1_02.json",
            {
                "decades": share.index.astype(int).tolist(),
                "teams": share.columns.tolist(),
                "z": share.values.tolist(),
            },
        )
    else:
        _write_json(data_dir / "b1_02.json", {"decades": [], "teams": [], "z": []})

    # B1_03
    driver_streaks = _compute_streaks(driver_standings, "Driver")
    team_streaks = _compute_streaks(constructor_standings, "Team")

    def _top15(streaks):
        items = sorted(streaks.items(), key=lambda item: item[1], reverse=True)[:15]
        return {
            "labels": [item[0] for item in items][::-1],
            "values": [item[1] for item in items][::-1],
        }

    _write_json(data_dir / "b1_03a.json", _top15(driver_streaks))
    _write_json(data_dir / "b1_03b.json", _top15(team_streaks))

    # B2_01
    merged = _merge_race_grid(race_details, starting_grids)
    merged = merged.dropna(subset=["FinishPos", "GridPos"])
    rows = []
    for year, group in merged.groupby("Year"):
        rho = _spearman(group["GridPos"], group["FinishPos"])
        if not np.isnan(rho):
            rows.append((int(year), float(rho)))
    rows.sort(key=lambda item: item[0])
    _write_json(
        data_dir / "b2_01.json",
        {"years": [r[0] for r in rows], "rho": [r[1] for r in rows]},
    )

    # B2_02
    merged = _merge_race_grid(race_details, starting_grids)
    merged = merged.dropna(subset=["FinishPos", "GridPos"])
    merged = add_decade(merged, "Year")
    merged["Podium"] = merged["FinishPos"] <= 3
    decade_traces = []
    for decade, group in merged.groupby("Decade"):
        prob = group.groupby("GridPos")["Podium"].mean().reset_index()
        prob = prob.dropna(subset=["GridPos"])
        if not prob.empty:
            decade_traces.append(
                {
                    "decade": int(decade),
                    "x": prob["GridPos"].tolist(),
                    "y": prob["Podium"].tolist(),
                }
            )
    _write_json(data_dir / "b2_02.json", {"traces": decade_traces})

    # B2_03
    merged = _merge_race_grid(race_details, starting_grids)
    merged = merged.dropna(subset=["FinishPos", "GridPos"])
    merged = add_decade(merged, "Year")
    merged["Delta"] = merged["FinishPos"] - merged["GridPos"]
    box_traces = []
    for decade, group in merged.groupby("Decade"):
        values = group["Delta"].dropna().tolist()
        if values:
            box_traces.append({"label": str(int(decade)), "values": values})
    _write_json(data_dir / "b2_03.json", {"traces": box_traces})

    # B3_01
    merged = _merge_pit_race(pitstops, race_details)
    scatter = {
        "x": merged["total_pit_time"].tolist(),
        "y": merged["FinishPos"].tolist(),
    }
    if len(merged) > 1:
        x = merged["total_pit_time"].values
        y = merged["FinishPos"].values
        slope, intercept = np.polyfit(x, y, 1)
        scatter["trend"] = {"slope": float(slope), "intercept": float(intercept)}
    _write_json(data_dir / "b3_01.json", scatter)

    # B3_02
    merged = _merge_pit_race(pitstops, race_details)
    merged = add_decade(merged, "Year")
    decades = []
    coefs = []
    ci_low = []
    ci_high = []
    for decade, group in merged.groupby("Decade"):
        x = group["total_pit_time"]
        y = group["FinishPos"]
        if len(group) < 2:
            continue
        if _HAS_STATSMODELS:
            X = sm.add_constant(x)
            model = sm.OLS(y, X, missing="drop").fit()
            coef = model.params.get("total_pit_time")
            ci = model.conf_int().loc["total_pit_time"].tolist()
            decades.append(int(decade))
            coefs.append(float(coef))
            ci_low.append(float(ci[0]))
            ci_high.append(float(ci[1]))
        else:
            slope, _ = np.polyfit(x, y, 1)
            decades.append(int(decade))
            coefs.append(float(slope))
    _write_json(
        data_dir / "b3_02.json",
        {
            "decades": decades,
            "coefs": coefs,
            "ci_low": ci_low if ci_low else None,
            "ci_high": ci_high if ci_high else None,
        },
    )

    # B3_03
    pit = pitstops.copy()
    pit["Year"] = to_numeric(pit["Year"])
    pit_time_col = _pit_time_column(pit)
    pit["PitTime"] = to_numeric(pit[pit_time_col])
    pit = pit.dropna(subset=["PitTime", "Year"])
    thresholds = pit.groupby("Year")["PitTime"].quantile(0.95)
    pit = pit.merge(thresholds.rename("P95"), left_on="Year", right_index=True, how="left")
    severe = pit[pit["PitTime"] > pit["P95"]]
    _write_json(data_dir / "b3_03.json", {"values": severe["PitTime"].tolist()})

    # B4_01
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
    _write_json(
        data_dir / "b4_01.json",
        {"years": share.index.astype(int).tolist(), "pct": share.values.tolist()},
    )

    # B4_02
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

    note = "Delta = grid domingo - posicion sprint"
    missing = merged["SundayGrid"].isna().sum()
    if missing > 0:
        merged["SundayGrid"] = merged["SundayGrid"].fillna(merged["SprintGrid"])
        note = "Delta = grid domingo - posicion sprint; grid domingo faltante usa grid sprint"

    merged = merged.dropna(subset=["SundayGrid", "SprintPos"])
    merged["Delta"] = merged["SundayGrid"] - merged["SprintPos"]

    _write_json(
        data_dir / "b4_02.json",
        {"values": merged["Delta"].tolist(), "note": note},
    )

    # B4_03
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

    sprint_values = variance.loc[variance["Sprint"], "FinishPos"].dropna().tolist()
    nonsprint_values = variance.loc[~variance["Sprint"], "FinishPos"].dropna().tolist()

    _write_json(
        data_dir / "b4_03.json",
        {"sprint": sprint_values, "nonsprint": nonsprint_values},
    )

    # B4_04
    sprint = add_driver_key(sprint_results)
    sprint["Year"] = to_numeric(sprint["Year"])
    sprint["PTS"] = to_numeric(sprint["PTS"])
    sprint = sprint.dropna(subset=["Year", "PTS", "DriverKey"])

    standings = add_driver_key(driver_standings)
    standings["Year"] = to_numeric(standings["Year"])
    standings["PTS"] = to_numeric(standings["PTS"])
    standings["Pos"] = to_numeric(standings["Pos"])
    standings = standings.dropna(subset=["Year", "PTS", "Pos", "DriverKey"])

    sprint_points = sprint.groupby(["Year", "DriverKey"])["PTS"].sum().reset_index()

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

    _write_json(
        data_dir / "b4_04.json",
        {
            "years": [r[0] for r in rows],
            "margins": [float(r[1]) for r in rows],
            "impacts": [float(r[2]) for r in rows],
        },
    )
