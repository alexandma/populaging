import pandas as pd

df = pd.read_csv('data/census_data.csv')

df_relevant = df[['Geographic name', 'Broad Age Groups: 65 years and over (2016 Counts)', 
                  'Broad Age Groups: 85 years and over (2016 Counts)', 
                  'Total (2016 Counts)', 'Latitude', 'Longitude']].copy()

# convert to numeric
df_relevant['Broad Age Groups: 65 years and over (2016 Counts)'] = pd.to_numeric(df_relevant['Broad Age Groups: 65 years and over (2016 Counts)'], errors='coerce')
df_relevant['Broad Age Groups: 85 years and over (2016 Counts)'] = pd.to_numeric(df_relevant['Broad Age Groups: 85 years and over (2016 Counts)'], errors='coerce')
df_relevant['Total (2016 Counts)'] = pd.to_numeric(df_relevant['Total (2016 Counts)'], errors='coerce')

df_relevant['Total (2016 Counts)'].replace(0, pd.NA, inplace=True)

df_relevant['percent elderly 65+'] = (df_relevant['Broad Age Groups: 65 years and over (2016 Counts)'] / df_relevant['Total (2016 Counts)']) * 100
df_relevant['percent elderly 85+'] = (df_relevant['Broad Age Groups: 85 years and over (2016 Counts)'] / df_relevant['Total (2016 Counts)']) * 100

df_relevant = df_relevant[pd.to_numeric(df_relevant['Latitude'], errors='coerce').notna() & pd.to_numeric(df_relevant['Longitude'], errors='coerce').notna()]

df_final = df_relevant[['Geographic name', 'percent elderly 65+', 'percent elderly 85+', 'Latitude', 'Longitude']]

df_final = df_final[(df_final['Latitude'] != 0.0) & (df_final['Longitude'] != 0.0)]

# save to new csv
df_final.to_csv('data/filtered_census_data.csv', index=False)
