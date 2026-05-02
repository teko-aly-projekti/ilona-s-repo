from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from helpers import read_clean_rows


EXCEL_FILE = "tamperetalo2023.xlsx"
OUTPUT_DIR = "output"


def main():
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)

    df = read_clean_rows(EXCEL_FILE)

    top = (
        df.groupby(["Koodi", "Seloste"])["Summa €"]
        .sum()
        .reset_index()
        .sort_values("Summa €", ascending=False)
        .head(15)
    )

    top["Label"] = top["Koodi"] + " | " + top["Seloste"]

    print(top[["Label", "Summa €"]].round(2))

    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(13, 8))
    sns.barplot(data=top, x="Summa €", y="Label", color="#4C78A8", ax=ax)

    ax.set_title("Suurimmat kustannusrivit 2023")
    ax.set_xlabel("Euroa")
    ax.set_ylabel("")

    plt.tight_layout()
    fig.savefig(out / "03_suurimmat_kulurivit.png", dpi=220, bbox_inches="tight")
    top.to_csv(out / "03_suurimmat_kulurivit.csv", index=False)

    print(f"Valmis: {out / '03_suurimmat_kulurivit.png'}")


if __name__ == "__main__":
    main()
