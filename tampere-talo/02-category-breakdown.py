from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from helpers import classify_category, read_clean_rows


EXCEL_FILE = "tamperetalo2023.xlsx"
OUTPUT_DIR = "output"


def main():
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)

    df = read_clean_rows(EXCEL_FILE)
    df["Kategoria"] = df.apply(lambda r: classify_category(r["Seloste"], r["Koodi"]), axis=1)

    pivot = (
        df.groupby(["Kuukausi", "Kategoria"])["Summa €"]
        .sum()
        .reset_index()
        .pivot(index="Kuukausi", columns="Kategoria", values="Summa €")
        .fillna(0)
        .sort_index()
    )

    totals = (
        df.groupby("Kategoria")["Summa €"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    print(pivot.round(2))
    print(totals.round(2))

    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(2, 1, figsize=(14, 12))

    pivot.plot(kind="bar", stacked=True, ax=axes[0], colormap="tab20c")
    axes[0].set_title("Työterveyskulut kategorioittain kuukausittain")
    axes[0].set_xlabel("Kuukausi")
    axes[0].set_ylabel("Euroa")
    axes[0].legend(title="Kategoria", bbox_to_anchor=(1.02, 1), loc="upper left")

    sns.barplot(data=totals, x="Summa €", y="Kategoria", color="#4C78A8", ax=axes[1])
    axes[1].set_title("Koko vuoden suurimmat kulukategoriat")
    axes[1].set_xlabel("Euroa")
    axes[1].set_ylabel("")

    plt.tight_layout()
    fig.savefig(out / "02_kategoriat_selkea.png", dpi=220, bbox_inches="tight")

    pivot.to_csv(out / "02_kategoriat_kuukausittain.csv")
    totals.to_csv(out / "02_kategoriat_vuositaso.csv", index=False)

    print(f"Valmis: {out / '02_kategoriat_selkea.png'}")


if __name__ == "__main__":
    main()
