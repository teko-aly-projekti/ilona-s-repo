import camelot
import pandas as pd
import glob
import os

pdf_files = glob.glob("tampere-talo-data/*.pdf") # Laita kaikki pdf samaan kansioon
output_excel = "tamperetalo2023.xlsx" # Nimeä excel omalla vuodella

with pd.ExcelWriter(output_excel) as writer:

    for pdf in pdf_files:
        print(f"Käsitellään: {pdf}")

        tables = camelot.read_pdf(pdf, pages="all", flavor="stream")

        print(f"Löytyi {tables.n} taulukkoa")

        all_tables = []

        for table in tables:
            df = table.df

            df = df.iloc[1:]
            df = df.reset_index(drop=True)
            all_tables.append(df)

        if not all_tables:
            print("Ei taulukoita! Tarkista pdf!")
            continue

        final_df = pd.concat(all_tables, ignore_index=True)

        sheet_name = os.path.basename(pdf)

        final_df.to_excel(writer, sheet_name=sheet_name, index=False)

print("Valmis!")
