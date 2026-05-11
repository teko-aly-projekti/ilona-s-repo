from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from helpers import classify_category, read_clean_rows


EXCEL_2023 = "tamperetalo2023.xlsx"
EXCEL_2024 = "tamperetalo2024.xlsx"
EXCEL_2025 = "tamperetalo2025.xlsx"
OUTPUT_DIR = "output"


def load_year_data(file_path, year_label):
    df = read_clean_rows(file_path).copy()
    df["Vuosi"] = year_label
    return df


def main():
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)

    df_2023 = load_year_data(EXCEL_2023, "2023")
    df_2024 = load_year_data(EXCEL_2024, "2024")
    df_2025 = load_year_data(EXCEL_2025, "2025")

    df = pd.concat([df_2023, df_2024, df_2025], ignore_index=True)

    df["Kategoria"] = df.apply(
        lambda r: classify_category(r["Seloste"], r["Koodi"]),
        axis=1,
    )

    autumn_months = {
        "2023-09", "2023-10", "2023-11",
        "2024-09", "2024-10", "2024-11",
        "2025-09", "2025-10", "2025-11",
    }

    autumn = df[df["Kuukausi"].isin(autumn_months)].copy()

    month_labels = {
        "2023-09": "2023 syyskuu",
        "2023-10": "2023 lokakuu",
        "2023-11": "2023 marraskuu",
        "2024-09": "2024 syyskuu",
        "2024-10": "2024 lokakuu",
        "2024-11": "2024 marraskuu",
        "2025-09": "2025 syyskuu",
        "2025-10": "2025 lokakuu",
        "2025-11": "2025 marraskuu",
    }

    autumn["Kuukausi_label"] = autumn["Kuukausi"].map(month_labels)

    pivot = (
        autumn.groupby(["Kuukausi_label", "Kategoria"])["Summa €"]
        .sum()
        .reset_index()
        .pivot(index="Kuukausi_label", columns="Kategoria", values="Summa €")
        .fillna(0)
    )

    month_order = [
        "2023 syyskuu", "2023 lokakuu", "2023 marraskuu",
        "2024 syyskuu", "2024 lokakuu", "2024 marraskuu",
        "2025 syyskuu", "2025 lokakuu", "2025 marraskuu",
    ]
    pivot = pivot.reindex(month_order)

    print(pivot.round(2))

    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(16, 8))

    pivot.plot(kind="bar", stacked=True, ax=ax, colormap="tab20c")

    ax.set_title("Syksyn työterveyspalveluiden kustannusjakauma 2023–2025")
    ax.set_xlabel("Kuukausi")
    ax.set_ylabel("Euroa")
    ax.legend(title="Palvelutyyppi", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.tick_params(axis="x", rotation=35)

    plt.tight_layout()
    fig.savefig(out / "09_syksyn_palvelutyypit.png", dpi=220, bbox_inches="tight")
    pivot.to_csv(out / "09_syksyn_palvelutyypit.csv")

    print(f"Valmis: {out / '09_syksyn_palvelutyypit.png'}")


if __name__ == "__main__":
    main()
