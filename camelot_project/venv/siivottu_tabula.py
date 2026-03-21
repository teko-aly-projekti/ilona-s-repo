import tabula
import pandas as pd

pdf_file = "tammikuu 2023.pdf"      # vaihda oman PDF:n nimi
csv_file = "testi_tulos.csv"
excel_file = "testi_tulos_siivottu.xlsx"

print("Aloitetaan siivous...")

# 1) Muunna PDF -> CSV
tabula.convert_into(pdf_file, csv_file, output_format="csv", pages="all")
print(" -> CSV valmis:", csv_file)

# 2) Lue CSV Pandasilla
df = pd.read_csv(csv_file)

# 3) Poista Unnamed-sarakkeet
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

# 4) Siivoa sarakeotsikot
df.columns = df.columns.str.strip()

# 5) Poista tyhjät rivit
df = df.dropna(how="all")

# 6) Muunna numerot numeroiksi (uusi tapa Pandas 2.x)
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col])

# 7) Muunna aika-arvot tunneiksi (esim. "1:30" -> 1.5)
def time_to_hours(x):
    if isinstance(x, str) and ":" in x:
        parts = x.split(":")
        if len(parts) == 2:
            h, m = parts
            try:
                return int(h) + int(m)/60
            except:
                return x
    return x

if "Tunnit" in df.columns:
    df["Tunnit"] = df["Tunnit"].apply(time_to_hours)

# 8) Tallenna siistitty Excel
df.to_excel(excel_file, index=False)
print(" -> Siivottu Excel valmis:", excel_file)

print("\nSiivous valmis!")

