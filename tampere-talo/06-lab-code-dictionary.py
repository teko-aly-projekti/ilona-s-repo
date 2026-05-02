from __future__ import annotations

from pathlib import Path

from helpers import is_lab_row, read_clean_rows


EXCEL_FILE = "tamperetalo2023.xlsx"
OUTPUT_DIR = "output"

LAB_CODE_DICT = {
    "1026": "S-ALAT: alaniiniaminotransferaasi, maksa-arvo",
    "1046": "S-AFOS: alkalinen fosfataasi",
    "1216": "S-CRP: tulehdusarvo",
    "1395": "S-Ferrit: ferritiini, rautavarastot",
    "1468": "fP-Gluk: paastoglukoosi",
    "1471": "P-Gluk: plasman glukoosi",
    "2001": "S-K: kalium",
    "2143": "S-Krea: kreatiniini, munuaistoiminta",
    "2245": "fS-Lipidit: veren rasva-arvot",
    "2382": "S-Na: natrium",
    "2474": "B-PVK+T: perusverenkuva ja trombosyytit",
    "2832": "S-TSH: tyreotropiini",
    "2836": "S-T4-V: vapaa tyroksiini",
    "3642": "S-PSA: eturauhasspesifinen antigeeni",
    "6128": "B-HbA1c: pitkäaikainen verensokeri",
}


def main():
    out = Path(OUTPUT_DIR)
    out.mkdir(exist_ok=True)

    df = read_clean_rows(EXCEL_FILE)
    lab = df[df.apply(lambda r: is_lab_row(r["Seloste"], r["Koodi"]), axis=1)].copy()

    dictionary = (
        lab[["Koodi", "Seloste"]]
        .drop_duplicates()
        .sort_values(["Koodi", "Seloste"])
        .copy()
    )

    dictionary["Selite"] = dictionary["Koodi"].map(LAB_CODE_DICT).fillna("Täydennä selite käsin")
    print(dictionary)

    dictionary.to_csv(out / "06_lab_koodiselitteet.csv", index=False)

    lines = [
        "# Labrakoodien selitteet",
        "",
        "| Koodi | Seloste | Selite |",
        "|---|---|---|",
    ]

    for _, row in dictionary.iterrows():
        lines.append(f"| {row['Koodi']} | {row['Seloste']} | {row['Selite']} |")

    (out / "06_lab_koodiselitteet.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Valmis: {out / '06_lab_koodiselitteet.csv'}")


if __name__ == "__main__":
    main()
