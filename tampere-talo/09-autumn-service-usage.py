# Tämä skripti hakee automaattisesti kaikki tiedostot,
# joiden nimi on muotoa tamperetaloYYYY.xlsx.
# Jos haluat lisätä uuden vuoden mukaan analyysiin,
# lisää vain uusi tiedosto samaan kansioon samalla nimeämislogiikalla.


from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from helpers import classify_category, read_clean_rows


DATA_DIR = Path(".")
FILE_PATTERN = "tamperetalo*.xlsx"
AUTUMN_MONTHS = ["09", "10", "11"]
MONTH_NAMES = {
    "09": "syyskuu",
    "10": "lokakuu",
    "11": "marraskuu",
}
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


def make_month_label(month_value):
    year, month = month_value.split("-")
    return f"{year} {MONTH_NAMES.get(month, month)}"


def main():
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)

    year_files = find_year_files()
    print("Löydetyt tiedostot:", year_files)

    df = load_all_years(year_files)

    df["Kategoria"] = df.apply(
        lambda r: classify_category(r["Seloste"], r["Koodi"]),
        axis=1,
    )

    autumn_month_values = {
        f"{year}-{month}"
        for year in year_files
        for month in AUTUMN_MONTHS
    }

    autumn = df[df["Kuukausi"].isin(autumn_month_values)].copy()
    autumn["Kuukausi_label"] = autumn["Kuukausi"].apply(make_month_label)

    pivot = (
        autumn.groupby(["Kuukausi_label", "Kategoria"])["Summa €"]
        .sum()
        .reset_index()
        .pivot(index="Kuukausi_label", columns="Kategoria", values="Summa €")
        .fillna(0)
    )

    month_order = [
        f"{year} {MONTH_NAMES[month]}"
        for year in year_files
        for month in AUTUMN_MONTHS
    ]
    pivot = pivot.reindex(month_order)

    print(pivot.round(2))

    sns.set_theme(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(16, 8))

    pivot.plot(kind="bar", stacked=True, ax=ax, colormap="tab20c")

    ax.set_title("Syksyn työterveyspalveluiden kustannusjakauma")
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
