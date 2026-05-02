from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from helpers import classify_category, read_clean_rows


EXCEL_FILE = "tamperetalo2023.xlsx"
OUTPUT_DIR = "output"


def main():
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)

    df = read_clean_rows(EXCEL_FILE)
    df["Kategoria"] = df.apply(lambda r: classify_category(r["Seloste"], r["Koodi"]), axis=1)

    monthly = (
        df.groupby(["Kuukausi", "Kategoria"])["Summa €"]
        .sum()
        .reset_index()
        .pivot(index="Kuukausi", columns="Kategoria", values="Summa €")
        .fillna(0)
        .sort_index()
    )

    first_month = monthly.index.min()
    last_month = monthly.index.max()

    growth = pd.DataFrame({
        "Kategoria": monthly.columns,
        "Alkuvuosi": [monthly.loc[first_month, c] for c in monthly.columns],
        "Loppuvuosi": [monthly.loc[last_month, c] for c in monthly.columns],
    })
    growth["Muutos €"] = growth["Loppuvuosi"] - growth["Alkuvuosi"]

    month_changes = monthly.diff().fillna(0)
    biggest_jumps = []
    for category in monthly.columns:
        jump_series = month_changes[category]
        max_idx = jump_series.idxmax()
        biggest_jumps.append(
            {
                "Kategoria": category,
                "Suurin kuukausihyppy €": jump_series.max(),
                "Kuukausi": max_idx,
            }
        )

    jumps = pd.DataFrame(biggest_jumps)
    growth = growth.merge(jumps, on="Kategoria", how="left")
    growth = growth.sort_values("Muutos €", ascending=False)

    print(growth.round(2))

    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))

    sns.barplot(data=growth, x="Muutos €", y="Kategoria", color="#C46C2B", ax=axes[0])
    axes[0].set_title("Kategorioiden muutos alkuvuodesta loppuvuoteen")
    axes[0].set_xlabel("Muutos euroissa")
    axes[0].set_ylabel("")

    top_jumps = growth.sort_values("Suurin kuukausihyppy €", ascending=False)
    sns.barplot(data=top_jumps, x="Suurin kuukausihyppy €", y="Kategoria", color="#4C9F70", ax=axes[1])
    axes[1].set_title("Suurin yksittäinen kuukausihyppy kategorioittain")
    axes[1].set_xlabel("Euroa")
    axes[1].set_ylabel("")

    plt.tight_layout()
    fig.savefig(out / "07_nopeimmin_kasvavat_kategoriat.png", dpi=220, bbox_inches="tight")
    growth.to_csv(out / "07_nopeimmin_kasvavat_kategoriat.csv", index=False)

    print(f"Valmis: {out / '07_nopeimmin_kasvavat_kategoriat.png'}")


if __name__ == "__main__":
    main()
