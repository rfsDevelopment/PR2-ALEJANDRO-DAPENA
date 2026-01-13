from pathlib import Path
import csv
import shutil

from src.data_loader import load_csv
from src.interactive_data import export_interactive_data
from src.plots_block1 import plot_b1_01, plot_b1_02, plot_b1_03
from src.plots_block2 import plot_b2_01, plot_b2_02, plot_b2_03
from src.plots_block3 import plot_b3_01, plot_b3_02, plot_b3_03
from src.plots_block4 import plot_b4_01, plot_b4_02, plot_b4_03, plot_b4_04


def write_manifest(entries, output_dir):
    manifest_path = output_dir / "manifest.csv"
    fieldnames = ["filename", "title", "datasets", "filters", "generated_at"]
    with open(manifest_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(entries)


def copy_to_docs(output_dir):
    docs_dir = Path(__file__).resolve().parent / "docs" / "figures"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for path in output_dir.glob("*.png"):
        shutil.copy2(path, docs_dir / path.name)
    manifest = output_dir / "manifest.csv"
    if manifest.exists():
        shutil.copy2(manifest, docs_dir / manifest.name)


def main():
    base_dir = Path(__file__).resolve().parent
    output_dir = base_dir / "outputs" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    race_details = load_csv(
        "race_details.csv",
        required_cols=["Pos", "Driver", "Car", "Year", "Grand Prix"],
    )
    driver_standings = load_csv(
        "driver_standings.csv",
        required_cols=["Pos", "Driver", "Year", "PTS"],
    )
    constructor_standings = load_csv(
        "constructor_standings.csv",
        required_cols=["Pos", "Team", "Year"],
    )
    starting_grids = load_csv(
        "starting_grids.csv",
        required_cols=["Pos", "Driver", "Year", "Grand Prix"],
    )
    pitstops = load_csv(
        "pitstops.csv",
        required_cols=["Driver", "Year", "Grand Prix"],
    )
    sprint_results = load_csv(
        "sprint_results.csv",
        required_cols=["Pos", "Driver", "Year", "Grand Prix", "PTS"],
    )
    sprint_grid = load_csv(
        "sprint_grid.csv",
        required_cols=["Pos", "Driver", "Year", "Grand Prix"],
    )

    manifest = []
    manifest.append(plot_b1_01(race_details, output_dir))
    manifest.append(plot_b1_02(race_details, output_dir))
    manifest.extend(plot_b1_03(driver_standings, constructor_standings, output_dir))

    manifest.append(plot_b2_01(race_details, starting_grids, output_dir))
    manifest.append(plot_b2_02(race_details, starting_grids, output_dir))
    manifest.append(plot_b2_03(race_details, starting_grids, output_dir))

    manifest.append(plot_b3_01(pitstops, race_details, output_dir))
    manifest.append(plot_b3_02(pitstops, race_details, output_dir))
    manifest.append(plot_b3_03(pitstops, output_dir))

    manifest.append(plot_b4_01(sprint_results, driver_standings, output_dir))
    manifest.append(plot_b4_02(sprint_results, sprint_grid, starting_grids, output_dir))
    manifest.append(plot_b4_03(race_details, sprint_results, output_dir))
    manifest.append(plot_b4_04(sprint_results, driver_standings, output_dir))

    write_manifest(manifest, output_dir)
    copy_to_docs(output_dir)

    export_interactive_data(
        race_details,
        driver_standings,
        constructor_standings,
        starting_grids,
        pitstops,
        sprint_results,
        sprint_grid,
        base_dir / "docs",
    )


if __name__ == "__main__":
    main()
