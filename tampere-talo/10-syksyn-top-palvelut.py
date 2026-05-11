# Tämä skripti hakee automaattisesti kaikki tiedostot,
# joiden nimi on muotoa tamperetaloYYYY.xlsx.
# Jos haluat lisätä uuden vuoden mukaan analyysiin,
# lisää vain uusi tiedosto samaan kansioon samalla nimeämislogiikalla.

from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from helpers import read_clean_rows


DATA_DIR = Path(".")
FILE_PATTERN = "tamperetalo*.xlsx"
AUTUMN_MONTHS = ["09", "10", "11"]
TOP_N = 12
OUTPUT_DIR = "output"


def find_year_files():
    year_files = {}

    for path in DATA_DIR.glob(FILE_PATTERN):
        match = re.search(r"tamperetalo(20\d{2})\.xlsx$", path.name)
        if match:
            year = match.group(1)
            year_files[year] = str(path)

    return dict(sorted(year_files.items()))


def load_all_years(year_files):
    frames = []

    for year, file_path in year_files.items():
        df = read_clean_rows(file_path).copy()
        df["Vuosi"] = year
        frames.append(df)

    if not frames:
        raise ValueError("Yhtään tamperetaloYYYY.xlsx -tiedostoa ei löytynyt.")

    return pd.concat(frames, ignore_index=True)


def main():
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)

    year_files = find_year_files()
    print("Löydetyt tiedostot:", year_files)

    df = load_all_years(year_files)

    autumn_month_values = {
        f"{year}-{month}"
        for year in year_files
        for month in AUTUMN_MONTHS
    }

    autumn = df[df["Kuukausi"].isin(autumn_month_values)].copy()

    service_totals = (
        autumn.groupby(["Koodi", "Seloste"])["Summa €"]
        .sum()
        .reset_index()
        .sort_values("Summa €", ascending=False)
    )

    top_services = service_totals.head(TOP_N).copy()
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
        ax=axes[0],
    )
    axes[0].set_title("Syksyn suurimmat palvelut yhteensä")
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
