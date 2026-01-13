from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt


def add_footer(fig, datasets, note=None):
    parts = [f"Fuente: {datasets}"]
    if note:
        parts.append(f"Nota: {note}")
    fig.text(
        0.01,
        0.01,
        "\n".join(parts),
        ha="left",
        va="bottom",
        fontsize=8,
    )


def save_figure(fig, output_dir, filename, title, datasets, filters, note=None):
    add_footer(fig, datasets, note)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return {
        "filename": filename,
        "title": title,
        "datasets": datasets,
        "filters": filters,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
