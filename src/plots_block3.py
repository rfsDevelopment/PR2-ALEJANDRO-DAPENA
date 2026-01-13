import numpy as np
import matplotlib.pyplot as plt

from src.cleaning import add_decade, add_driver_key, add_finish_pos, to_numeric
from src.plot_utils import save_figure

try:
    import statsmodels.api as sm
    _HAS_STATSMODELS = True
except Exception:
    _HAS_STATSMODELS = False


TITLE_B3_01 = "BLOQUE 3 - Scatter: tiempo total en boxes vs posición final"
TITLE_B3_02 = "BLOQUE 3 - Efecto marginal del tiempo en boxes por década"
TITLE_B3_03 = "BLOQUE 3 - Distribución de errores graves en boxes"


def _pit_time_column(pitstops):
    if "Time" in pitstops.columns:
        return "Time"
    if "Total" in pitstops.columns:
        return "Total"
    raise ValueError("pitstops.csv no contiene columnas de duración (Time/Total)")


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


def plot_b3_01(pitstops, race_details, output_dir):
    merged = _merge_pit_race(pitstops, race_details)

    fig, ax = plt.subplots(figsize=(10, 6))
    if not merged.empty:
        ax.scatter(merged["total_pit_time"], merged["FinishPos"])
        if len(merged) > 1:
            x = merged["total_pit_time"].values
            y = merged["FinishPos"].values
            slope, intercept = np.polyfit(x, y, 1)
            x_line = np.linspace(x.min(), x.max(), 100)
            y_line = slope * x_line + intercept
            ax.plot(x_line, y_line)

    ax.set_xlabel("Tiempo total en boxes (s)")
    ax.set_ylabel("Posición final")
    ax.set_title(TITLE_B3_01)

    return save_figure(
        fig,
        output_dir,
        "B3_01_scatter_pit_time_vs_pos.png",
        TITLE_B3_01,
        "pitstops.csv, race_details.csv",
        "Excluye DNFs (posición final no numérica)",
        note="Excluye DNFs",
    )


def plot_b3_02(pitstops, race_details, output_dir):
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
            coefs.append(coef)
            ci_low.append(ci[0])
            ci_high.append(ci[1])
        else:
            slope, _ = np.polyfit(x, y, 1)
            decades.append(int(decade))
            coefs.append(slope)

    fig, ax = plt.subplots(figsize=(10, 6))
    if decades:
        order = np.argsort(decades)
        decades = [decades[i] for i in order]
        coefs = [coefs[i] for i in order]
        ax.bar(decades, coefs)
        if _HAS_STATSMODELS:
            ci_low = [ci_low[i] for i in order]
            ci_high = [ci_high[i] for i in order]
            yerr = [
                [coef - low for coef, low in zip(coefs, ci_low)],
                [high - coef for coef, high in zip(coefs, ci_high)],
            ]
            ax.errorbar(decades, coefs, yerr=yerr, fmt="none", capsize=3)

    ax.set_xlabel("Década")
    ax.set_ylabel("Δ posiciones por +1s en boxes")
    ax.set_title(TITLE_B3_02)

    note = "Excluye DNFs"
    if not _HAS_STATSMODELS:
        note = "Excluye DNFs; sin IC (statsmodels no disponible)"

    return save_figure(
        fig,
        output_dir,
        "B3_02_efecto_marginal_pit_time.png",
        TITLE_B3_02,
        "pitstops.csv, race_details.csv",
        "Excluye DNFs (posición final no numérica)",
        note=note,
    )


def plot_b3_03(pitstops, output_dir):
    pit = pitstops.copy()
    pit["Year"] = to_numeric(pit["Year"])
    pit_time_col = _pit_time_column(pit)
    pit["PitTime"] = to_numeric(pit[pit_time_col])
    pit = pit.dropna(subset=["PitTime", "Year"])

    thresholds = pit.groupby("Year")["PitTime"].quantile(0.95)
    pit = pit.merge(
        thresholds.rename("P95"), left_on="Year", right_index=True, how="left"
    )
    severe = pit[pit["PitTime"] > pit["P95"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    if not severe.empty:
        ax.hist(severe["PitTime"].values, bins=30)
    ax.set_xlabel("Duración de parada (s)")
    ax.set_ylabel("Frecuencia")
    ax.set_title(TITLE_B3_03)

    return save_figure(
        fig,
        output_dir,
        "B3_03_distribucion_errores_graves.png",
        TITLE_B3_03,
        "pitstops.csv",
        "Error grave = parada > p95 de su temporada",
        note="Error grave = parada > p95 de su temporada",
    )
