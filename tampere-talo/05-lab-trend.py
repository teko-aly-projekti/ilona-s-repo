from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from helpers import is_lab_row, read_clean_rows


EXCEL_FILE = "tamperetalo2023.xlsx"
OUTPUT_DIR = "output"


def main():
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)

    df = read_clean_rows(EXCEL_FILE)
    lab = df[df.apply(lambda r: is_lab_row(r["Seloste"], r["Koodi"]), axis=1)].copy()

    top_labs = (
        lab.groupby("Seloste")["Summa €"]
        .sum()
        .sort_values(ascending=False)
        .head(6)
        .index
        .tolist()
    )

    lab = lab[lab["Seloste"].isin(top_labs)]

    pivot = (
        lab.groupby(["Kuukausi", "Seloste"])["Summa €"]
        .sum()
        .reset_index()
        .pivot(index="Kuukausi", columns="Seloste", values="Summa €")
        .fillna(0)
        .sort_index()
    )

    print(pivot.round(2))

    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(16, 8))

    colors = sns.color_palette("Set2", n_colors=len(pivot.columns))

    for color, col in zip(colors, pivot.columns):
        ax.plot(
            pivot.index,
            pivot[col],
            marker="o",
            linewidth=3,
            markersize=8,
            label=col,
            color=color
        )

    ax.set_title("Suurimpien labrakulujen kuukausikehitys 2023")
    ax.set_xlabel("Kuukausi")
    ax.set_ylabel("Euroa")
    ax.legend(title="Tutkimus", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(axis="y", alpha=0.3)

    # Tämä korjaa päällekkäiset kuukaudet
    ax.set_xticks(range(len(pivot.index)))
    ax.set_xticklabels(pivot.index, rotation=45, ha="right")

    plt.tight_layout()
    fig.savefig(out / "05_labrat_kuukausittain_selkea.png", dpi=220, bbox_inches="tight")
    pivot.to_csv(out / "05_labrat_kuukausittain.csv")

    print(f"Valmis: {out / '05_labrat_kuukausittain_selkea.png'}")


if __name__ == "__main__":
    main()
