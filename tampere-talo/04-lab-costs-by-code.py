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
    df["Onko_labra"] = df.apply(lambda r: is_lab_row(r["Seloste"], r["Koodi"]), axis=1)

    # Tarkistuslista: näet tästä mitä koodi tulkitsi labroiksi
    lab_rows = df[df["Onko_labra"]].copy()
    lab_rows.to_csv(out / "04_labrat_tarkistuslista.csv", index=False)

    totals = (
        lab_rows.groupby(["Koodi", "Seloste"])["Summa €"]
        .sum()
        .reset_index()
        .sort_values("Summa €", ascending=False)
    )

    totals["Label"] = totals["Koodi"] + " | " + totals["Seloste"]
    print(totals[["Label", "Summa €"]].head(20).round(2))

    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.barplot(data=totals.head(15), x="Summa €", y="Label", color="#2E6F95", ax=ax)

    ax.set_title("Labrakustannukset koodeittain 2023")
    ax.set_xlabel("Euroa")
    ax.set_ylabel("")

    plt.tight_layout()
    fig.savefig(out / "04_labrat_koodeittain.png", dpi=220, bbox_inches="tight")
    totals.to_csv(out / "04_labrat_koodeittain.csv", index=False)

    print(f"Valmis: {out / '04_labrat_koodeittain.png'}")
    print(f"Tarkistuslista: {out / '04_labrat_tarkistuslista.csv'}")


if __name__ == "__main__":
    main()
