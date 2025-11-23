import pandas as pd

# Einlesen der Quelldatei (mit Header in Zeile 1)
df = pd.read_csv('scripts/source_raw/spi_qogdata_23_11_2025.csv', header=0, sep=';')

# Spalten: B = country, C = year, J = Value
country_col = df.columns[1]
year_col = df.columns[2]
value_col = df.columns[9]

# Extrahiere und benenne die Spalten
result = df[[country_col, year_col, value_col]].copy()
result = result.rename(columns={country_col: 'country', year_col: 'year', value_col: 'value'})

# Optional: Werte runden, falls numerisch
result['value'] = result['value'].astype(str).str.replace(',', '.', regex=False)
result['value'] = pd.to_numeric(result['value'], errors='coerce').round(2)

# Speichern im Zielverzeichnis
result.to_csv('scripts/source_csv/social_progress_index.csv', index=False)
print('Saved to scripts/source_csv/social_progress_index.csv')
