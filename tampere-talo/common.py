from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(".matplotlib-cache").resolve()))
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


COLUMN_ALIASES = {
    "kuukausi": "Kuukausi",
    "month": "Kuukausi",
    "koodi": "Koodi",
    "code": "Koodi",
    "ki": "KI",
    "seloste": "Seloste",
    "description": "Seloste",
    "lkm": "Lkm",
    "count": "Lkm",
    "a hinta": "a-hinta",
    "ahinta": "a-hinta",
    "hinta": "Hinta",
    "alennus": "Alennus",
    "summa €": "Summa €",
    "summa eur": "Summa €",
    "summa_eur": "Summa €",
    "summa": "Summa €",
}

MONTH_NAME_MAP = {
    "tammikuu": "01",
    "helmikuu": "02",
    "maaliskuu": "03",
    "huhtikuu": "04",
    "toukokuu": "05",
    "kesakuu": "06",
    "heinakuu": "07",
    "elokuu": "08",
    "syyskuu": "09",
    "lokakuu": "10",
    "marraskuu": "11",
    "joulukuu": "12",
}

LAB_CODE_PATTERN = re.compile(r"^(S-|B-|U-|P-|fP-|fS-|TES-V)", re.IGNORECASE)


def parse_standard_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--input", required=True, help="CSV/XLSX-tiedosto tai kansio")
    parser.add_argument("--output", required=True, help="Kansio tallennukselle")
    parser.add_argument(
        "--lab-reference",
        default="lab_codes_reference.csv",
        help="CSV, jossa labrakoodien selitteet",
    )
    return parser.parse_args()


def configure_plot_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams["axes.titlesize"] = 16
    plt.rcParams["axes.labelsize"] = 12


def ensure_output_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)


def read_input(input_path: Path) -> pd.DataFrame:
    if input_path.is_dir():
        frames = []
        for file_path in sorted(input_path.iterdir()):
            if file_path.suffix.lower() not in {".csv", ".xlsx", ".xls"}:
                continue
            frame = read_single_file(file_path)
            if "Kuukausi" not in frame.columns:
                frame["Kuukausi"] = infer_month_from_filename(file_path.stem)
            frames.append(frame)

        if not frames:
            raise ValueError("Syotekansiosta ei loytynyt CSV- tai Excel-tiedostoja.")

        return pd.concat(frames, ignore_index=True)

    return read_single_file(input_path)


def read_single_file(file_path: Path) -> pd.DataFrame:
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        frame = pd.read_csv(file_path)
        return normalize_columns(frame)

    if suffix in {".xlsx", ".xls"}:
        xls = pd.ExcelFile(file_path)
        frames = []

        for sheet_name in xls.sheet_names:
            sheet = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            sheet = normalize_headerless_excel(sheet, sheet_name)
            frames.append(sheet)

        if not frames:
            raise ValueError("Excel-tiedostossa ei ollut luettavia valilehtia.")

        return pd.concat(frames, ignore_index=True)

    raise ValueError(f"Tuntematon tiedostotyyppi: {file_path.suffix}")


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = {}

    for column in frame.columns:
        normalized = str(column).strip().lower().replace("ä", "a").replace("ö", "o")
        normalized = normalized.replace("€", " eur").replace("-", " ")
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if normalized in COLUMN_ALIASES:
            renamed[column] = COLUMN_ALIASES[normalized]

    frame = frame.rename(columns=renamed).copy()

    required = {"Koodi", "Seloste", "Lkm", "Summa €"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Pakollisia sarakkeita puuttuu: {', '.join(sorted(missing))}")

    if "Kuukausi" not in frame.columns:
        raise ValueError("Kuukausi-sarake puuttuu eika sita voitu paatella tiedoston nimesta.")

    frame["Kuukausi"] = pd.to_datetime(frame["Kuukausi"], errors="coerce").dt.to_period("M")
    frame["Koodi"] = frame["Koodi"].astype(str).str.strip()
    frame["Seloste"] = frame["Seloste"].astype(str).str.strip()
    frame["Lkm"] = to_number(frame["Lkm"]).fillna(0)
    frame["Summa €"] = to_number(frame["Summa €"]).fillna(0)

    if "a-hinta" in frame.columns:
        frame["a-hinta"] = to_number(frame["a-hinta"])
    if "Hinta" in frame.columns:
        frame["Hinta"] = to_number(frame["Hinta"])
    if "Alennus" in frame.columns:
        frame["Alennus"] = to_number(frame["Alennus"])

    frame["Palvelukategoria"] = frame["Seloste"].apply(classify_service)
    frame["Onko labra"] = frame.apply(is_lab_row, axis=1)

    return frame.dropna(subset=["Kuukausi"])


def normalize_headerless_excel(frame: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    frame = frame.copy()
    frame = frame.dropna(how="all")
    frame = frame.iloc[:, :7]

    if frame.shape[1] < 7:
        raise ValueError(f"Sheetissa {sheet_name} ei ole odotettua 7 sarakkeen rakennetta.")

    frame.columns = ["Koodi_KI", "Seloste", "a-hinta", "Hinta", "Alennus", "Lkm", "Summa €"]

    split_values = frame["Koodi_KI"].astype(str).str.split("\n", n=1, expand=True)
    frame["Koodi"] = split_values[0].str.strip()

    if split_values.shape[1] > 1:
        frame["KI"] = split_values[1].fillna("").str.strip()
    else:
        frame["KI"] = ""

    frame["Kuukausi"] = parse_month_from_sheet_name(sheet_name)
    frame["Seloste"] = frame["Seloste"].astype(str).str.strip()
    frame["a-hinta"] = to_number(frame["a-hinta"])
    frame["Hinta"] = to_number(frame["Hinta"])
    frame["Alennus"] = to_number(frame["Alennus"])
    frame["Lkm"] = to_number(frame["Lkm"]).fillna(0)
    frame["Summa €"] = to_number(frame["Summa €"]).fillna(0)

    frame = frame[frame["Koodi"].ne("")]
    frame = frame[frame["Seloste"].ne("")]
    frame["Palvelukategoria"] = frame["Seloste"].apply(classify_service)
    frame["Onko labra"] = frame.apply(is_lab_row, axis=1)

    return frame[
        [
            "Kuukausi",
            "Koodi",
            "KI",
            "Seloste",
            "a-hinta",
            "Hinta",
            "Alennus",
            "Lkm",
            "Summa €",
            "Palvelukategoria",
            "Onko labra",
        ]
    ]


def to_number(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series

    cleaned = (
        series.astype(str)
        .str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    cleaned = cleaned.replace({"nan": None, "None": None, "": None})
    return pd.to_numeric(cleaned, errors="coerce")


def infer_month_from_filename(stem: str) -> pd.Period:
    match = re.search(r"(20\d{2})[-_ ]?(\d{2})", stem)
    if not match:
        raise ValueError(f"Kuukautta ei voitu paatella tiedoston nimesta: {stem}")
    return pd.Period(f"{match.group(1)}-{match.group(2)}", freq="M")


def parse_month_from_sheet_name(sheet_name: str) -> pd.Period:
    normalized = (
        str(sheet_name).lower().replace("ä", "a").replace("ö", "o").replace(".pdf", "").strip()
    )

    match = re.search(r"([a-z]+)(20\d{2})", normalized)
    if not match:
        raise ValueError(f"Kuukautta ei voitu paatella sheetin nimesta: {sheet_name}")

    month_name = match.group(1)
    year = match.group(2)

    if month_name not in MONTH_NAME_MAP:
        raise ValueError(f"Tuntematon kuukausi sheetin nimessa: {sheet_name}")

    month = MONTH_NAME_MAP[month_name]
    return pd.Period(f"{year}-{month}", freq="M")


def classify_service(description: str) -> str:
    text = str(description).lower().replace("ä", "a").replace("ö", "o")

    if any(keyword in text for keyword in ["tpsy", "psyk", "mielenter", "terapia"]):
        return "Mielenterveys"
    if any(keyword in text for keyword in ["etavastaanotto", "eta", "puhelu", "neuvonta"]):
        return "Etapalvelut ja ohjaus"
    if any(keyword in text for keyword in ["rontgen", "kuvaus", "magneetti", "ultra"]):
        return "Kuvantaminen"
    if any(keyword in text for keyword in ["s-", "b-", "u-", "p-", "gluk", "hba1c", "ferrit", "psa", "tsh"]):
        return "Laboratorio"
    if any(keyword in text for keyword in ["laakari", "erikoislaakari"]):
        return "Laakaripalvelut"
    if any(keyword in text for keyword in ["hoitaja", "tth"]):
        return "Hoitajapalvelut"
    if any(keyword in text for keyword in ["kanta", "yleismaksu", "maksu", "raportointi"]):
        return "Hallinto ja maksut"
    return "Muut"


def is_lab_row(row: pd.Series) -> bool:
    code = str(row.get("Koodi", "")).strip()
    description = str(row.get("Seloste", "")).strip()
    return bool(LAB_CODE_PATTERN.match(code) or LAB_CODE_PATTERN.match(description))


def get_lab_frame(frame: pd.DataFrame, lab_reference_path: Path) -> pd.DataFrame:
    lab_frame = frame[frame["Onko labra"]].copy()
    if lab_frame.empty:
        return lab_frame

    reference = load_lab_reference(lab_reference_path)
    lab_frame["lab_code"] = lab_frame["Seloste"].where(
        lab_frame["Seloste"].astype(str).str.match(LAB_CODE_PATTERN), lab_frame["Koodi"]
    )
    lab_frame = lab_frame.merge(reference, how="left", on="lab_code")
    lab_frame["display_name"] = lab_frame["plain_name"].fillna(lab_frame["lab_code"])
    return lab_frame


def load_lab_reference(reference_path: Path) -> pd.DataFrame:
    if not reference_path.exists():
        return pd.DataFrame(columns=["lab_code", "plain_name", "description"])

    reference = pd.read_csv(reference_path)
    reference["lab_code"] = reference["lab_code"].astype(str).str.strip()
    return reference
