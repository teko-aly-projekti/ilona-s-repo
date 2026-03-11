import camelot
import pandas as pd

pdf_file = "tammikuu 2023.pdf"   # vaihda tähän oman PDF:n nimi
output_excel = "tulos.xlsx"

# stream = paras kun PDF:ssä ei ole viivoja
tables = camelot.read_pdf(pdf_file, pages="all", flavor="stream")

print(f"Löytyi {tables.n} taulukkoa")

with pd.ExcelWriter(output_excel) as writer:
    for i, table in enumerate(tables):
        df = table.df
        df.to_excel(writer, sheet_name=f"Taulukko_{i+1}", index=False)

print("Valmis! Excel-tiedosto luotu.")
