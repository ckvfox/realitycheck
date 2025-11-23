import pandas as pd

# Load the NRI Excel file (adjust path if needed)
df = pd.read_excel('scripts/source_raw/nri-2024-dataset.xlsx', sheet_name=None)

# Inspect sheet names and structure
print('Sheets:', df.keys())


# Main sheet
sheet = list(df.keys())[0]
data = df[sheet]

# Extract relevant columns: Spalte A (country), Spalte G (NRI score)
# Assume columns: A = 'Country or Area', G = 'NRI Score'
country_col = data.columns[0]
nri_col = data.columns[6]


# Add year (2024) as required by Ziel-CSV
result = data[[country_col, nri_col]].copy()
result['year'] = 2024
result = result.rename(columns={country_col: 'country', nri_col: 'value'})
result = result[['country', 'year', 'value']]

# Werte kaufmännisch auf zwei Nachkommastellen runden (nur für numerische Werte)
import numpy as np
def safe_round(x):
	try:
		return round(float(x), 2)
	except (ValueError, TypeError):
		return np.nan
result['value'] = result['value'].apply(safe_round)
# Entferne Zeilen ohne gültigen Wert
result = result[result['value'].notnull()]

# Save as CSV
result.to_csv('scripts/source_csv/network_readiness_index.csv', index=False)
print('Saved to scripts/source_csv/network_readiness_index.csv')
