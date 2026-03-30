import pandas as pd

# Lue kaikki sheetit dictiin
all_sheets = pd.read_excel("elokuu2023.xlsx", sheet_name=None)

# Yhdistä kaikki DataFrame-objektit yhdeksi
combined = pd.concat(all_sheets.values(), ignore_index=True)

# Tallenna uusi Excel
combined.to_excel("yhdistetty.xlsx", index=False)
