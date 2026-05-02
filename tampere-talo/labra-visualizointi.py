from __future__ import annotations

from pathlib import Path
import unicodedata
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


EXCEL_FILE = "labra2023-1.xlsx"
OUTPUT_DIR = "output_labrat"


MONTH_MAP = {
    "tammikuu": "2023-01",
    "helmikuu": "2023-02",
    "maaliskuu": "2023-03",
    "huhtikuu": "2023-04",
    "toukokuu": "2023-05",
    "kesäkuu": "2023-06",
    "heinäkuu": "2023-07",
    "elokuu": "2023-08",
    "syyskuu": "2023-09",
    "lokakuu": "2023-10",
    "marraskuu": "2023-11",
    "joulukuu": "2023-12",
}


def normalize_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def to_float(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip().replace(",", ".")
    text = text.replace("\u00a0", "").replace(" ", "").replace("..", ".")
    if text == "" or text.lower() == "nan":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_month_from_sheet(sheet_name: str) -> str:
    normalized = normalize_text(sheet_name)
    for key, value in MONTH_MAP.items():
        if normalized.startswith(normalize_text(key)):
            return value

    match = re.search(r"(2023)[-_ ]?(\d{2})", normalized)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    raise ValueError(f"Tuntematon kuukausi sheetissä: {sheet_name}")


def is_data_row(values) -> bool:
    c0 = normalize_text(values[0] if len(values) > 0 else "")
    c1 = normalize_text(values[1] if len(values) > 1 else "")
    c2 = normalize_text(values[2] if len(values) > 2 else "")
    joined = f"{c0} {c1} {c2}"

    if not any([c0, c1, c2]):
        return False
    if c0.startswith("koodi"):
        return False
    if c0 == "0":
        return False
    if "yhteensa" in joined:
        return False
    if "seloste" in joined and "summa" in joined:
        return False
    return True


def get_amount(values):
    if len(values) > 8:
        amount = to_float(values[8])
        if amount is not None:
            return amount
    if len(values) > 7:
        amount = to_float(values[7])
        if amount is not None:
            return amount
    return None


def read_lab_rows(excel_path: str | Path) -> pd.DataFrame:
    xls = pd.ExcelFile(excel_path)
    rows = []

    for sheet_name in xls.sheet_names:
        month = parse_month_from_sheet(sheet_name)
        df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)

        for _, row in df.iterrows():
            values = row.tolist()

            if not is_data_row(values):
                continue

            amount = get_amount(values)
            if amount is None:
                continue

            rows.append(
                {
                    "Kuukausi": month,
                    "Koodi": "" if len(values) <= 0 or pd.isna(values[0]) else str(values[0]).strip(),
                    "Seloste": "" if len(values) <= 2 or pd.isna(values[2]) else str(values[2]).strip(),
                    "Lkm": to_float(values[7]) if len(values) > 7 else None,
                    "Summa €": amount,
                }
            )

    return pd.DataFrame(rows)


def main():
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)

    df = read_lab_rows(EXCEL_FILE)

    totals = (
        df.groupby(["Koodi", "Seloste"])["Summa €"]
        .sum()
        .reset_index()
        .sort_values("Summa €", ascending=False)
    )
    totals["Label"] = totals["Koodi"] + " | " + totals["Seloste"]

    monthly = (
        df.groupby(["Kuukausi", "Seloste"])["Summa €"]
        .sum()
        .reset_index()
        .pivot(index="Kuukausi", columns="Seloste", values="Summa €")
        .fillna(0)
        .sort_index()
    )

    top_tests = (
        df.groupby("Seloste")["Summa €"]
        .sum()
        .sort_values(ascending=False)
        .head(6)
        .index
        .tolist()
    )
    monthly_top = monthly[top_tests] if top_tests else monthly

    sns.set_theme(style="whitegrid", context="talk")

    fig, axes = plt.subplots(2, 1, figsize=(15, 12))

    sns.barplot(data=totals.head(15), x="Summa €", y="Label", color="#2E6F95", ax=axes[0])
    axes[0].set_title("Suurimmat laboratoriokulut koodeittain")
    axes[0].set_xlabel("Euroa")
    axes[0].set_ylabel("")

    colors = sns.color_palette("Set2", n_colors=len(monthly_top.columns))
    for color, col in zip(colors, monthly_top.columns):
        axes[1].plot(
            monthly_top.index,
            monthly_top[col],
            marker="o",
            linewidth=3,
            markersize=8,
            label=col,
            color=color,
        )

    axes[1].set_title("Suurimpien laboratoriokulujen kuukausikehitys")
    axes[1].set_xlabel("Kuukausi")
    axes[1].set_ylabel("Euroa")
    axes[1].set_xticks(range(len(monthly_top.index)))
    axes[1].set_xticklabels(monthly_top.index, rotation=45, ha="right")
    axes[1].legend(title="Tutkimus", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    fig.savefig(out / "labrat_visualisointi.png", dpi=220, bbox_inches="tight")

    totals.to_csv(out / "labrat_koodeittain.csv", index=False)
    monthly.to_csv(out / "labrat_kuukausittain.csv")

    print(f"Valmis: {out / 'labrat_visualisointi.png'}")


if __name__ == "__main__":
    main()
