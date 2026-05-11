from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from helpers import read_clean_rows


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

    autumn_months = {
        "2023-09", "2023-10", "2023-11",
        "2024-09", "2024-10", "2024-11",
        "2025-09", "2025-10", "2025-11",
    }

    autumn = df[df["Kuukausi"].isin(autumn_months)].copy()

    service_totals = (
        autumn.groupby(["Koodi", "Seloste"])["Summa €"]
        .sum()
        .reset_index()
        .sort_values("Summa €", ascending=False)
    )

    top_services = service_totals.head(12).copy()
    top_services["Palvelu"] = top_services["Koodi"] + " | " + top_services["Seloste"]

    top_labels = top_services["Palvelu"].tolist()

    autumn["Palvelu"] = autumn["Koodi"] + " | " + autumn["Seloste"]
    autumn_top = autumn[autumn["Palvelu"].isin(top_labels)].copy()

    by_year = (
        autumn_top.groupby(["Palvelu", "Vuosi"])["Summa €"]
        .sum()
        .reset_index()
    )

    pivot = (
        by_year.pivot(index="Palvelu", columns="Vuosi", values="Summa €")
        .fillna(0)
        .reindex(top_labels)
    )

    print(pivot.round(2))

    sns.set_theme(style="whitegrid", context="talk")
    fig, axes = plt.subplots(2, 1, figsize=(16, 14))

    sns.barplot(
        data=top_services,
        x="Summa €",
        y="Palvelu",
        color="#C46C2B",
        ax=axes[0]
    )
    axes[0].set_title("Syksyn suurimmat palvelut yhteensä (2023–2025)")
    axes[0].set_xlabel("Euroa")
    axes[0].set_ylabel("")

    pivot.plot(kind="bar", ax=axes[1], width=0.8)
    axes[1].set_title("Syksyn suurimmat palvelut vuosittain")
    axes[1].set_xlabel("Palvelu")
    axes[1].set_ylabel("Euroa")
    axes[1].tick_params(axis="x", rotation=45)
    axes[1].legend(title="Vuosi")

    plt.tight_layout()
    fig.savefig(out / "10_syksyn_suurimmat_palvelut.png", dpi=220, bbox_inches="tight")

    top_services.to_csv(out / "10_syksyn_suurimmat_palvelut_yhteensa.csv", index=False)
    pivot.to_csv(out / "10_syksyn_suurimmat_palvelut_vuosittain.csv")

    print(f"Valmis: {out / '10_syksyn_suurimmat_palvelut.png'}")


if __name__ == "__main__":
    main()
