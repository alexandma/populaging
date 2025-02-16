import pandas as pd

df = pd.read_csv('data/healthcare_facilities.csv')

df_relevant = df[['facility_name', 'odhf_facility_type', 'latitude', 'longitude']].copy()

# capitalize facility names
df_relevant['facility_name'] = df_relevant['facility_name'].apply(lambda x: ' '.join([word.capitalize() for word in x.split()]))

df_relevant = df_relevant[pd.to_numeric(df_relevant['latitude'], errors='coerce').notna() & pd.to_numeric(df_relevant['longitude'], errors='coerce').notna()]

df_relevant = df_relevant[(df_relevant['latitude'] != 0.0) & (df_relevant['longitude'] != 0.0)]

# save to new csv
df_relevant.to_csv('data/filtered_healthcare.csv', index=False)

