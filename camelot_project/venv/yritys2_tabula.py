import tabula
import pandas as pd

pdf_file = "tammikuu 2023.pdf"     
csv_file = "testi_tulos.csv"
excel_file = "testi_tulos.xlsx"

print("Aloitetaan tabula-testin ajo...")

# 1) Muunna PDF -> CSV
print("Testi 1: PDF -> CSV")
tabula.convert_into(pdf_file, csv_file, output_format="csv", pages="all")
print(" -> CSV valmis:", csv_file)

# 2) Lue CSV ja muunna Exceliksi
print("Testi 2: CSV -> Excel")
df = pd.read_csv(csv_file)
df.to_excel(excel_file, index=False)
print(" -> Excel valmis:", excel_file)

# 3) Näytä mitä tabula löysi taulukoina
print("\nTesti 3: Taulukoiden tunnistus")
tables = tabula.read_pdf(pdf_file, pages="all", multiple_tables=True)

print(f"Tabula löysi {len(tables)} taulukkoa")

for i, table in enumerate(tables):
    print(f"\nTaulukko {i+1}:")
    print(table.head())

print("\nTesti valmis!")
