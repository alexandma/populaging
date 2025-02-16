import pandas as pd

df = pd.read_csv('data/census_data.csv')

df_relevant = df[['Geographic name', 
                  'Broad Age Groups: 65 years and over (2016 Counts)', 
                  'Broad Age Groups: 85 years and over (2016 Counts)', 
                  'Total (2016 Counts)', 
                  'Broad Age Groups: 65 years and over (2011 Counts)', 
                  'Broad Age Groups: 85 years and over (2011 Counts)', 
                  'Total (2011 Counts)', 
                  'Latitude', 'Longitude']].copy()

# convert to numeric
numeric_columns = [
    'Broad Age Groups: 65 years and over (2016 Counts)',
    'Broad Age Groups: 85 years and over (2016 Counts)',
    'Total (2016 Counts)',
    'Broad Age Groups: 65 years and over (2011 Counts)',
    'Broad Age Groups: 85 years and over (2011 Counts)',
    'Total (2011 Counts)'
]
df_relevant[numeric_columns] = df_relevant[numeric_columns].apply(pd.to_numeric, errors='coerce')

# replace zeroes
df_relevant['Total (2016 Counts)'] = df_relevant['Total (2016 Counts)'].replace(0, pd.NA)
df_relevant['Total (2011 Counts)'] = df_relevant['Total (2011 Counts)'].replace(0, pd.NA)

# percents for 2016
df_relevant['percent elderly 65+ 2016'] = (
    df_relevant['Broad Age Groups: 65 years and over (2016 Counts)'] /
    df_relevant['Total (2016 Counts)']
) * 100

df_relevant['percent elderly 85+ 2016'] = (
    df_relevant['Broad Age Groups: 85 years and over (2016 Counts)'] /
    df_relevant['Total (2016 Counts)']
) * 100

# percents for 2011
df_relevant['percent elderly 65+ 2011'] = (
    df_relevant['Broad Age Groups: 65 years and over (2011 Counts)'] /
    df_relevant['Total (2011 Counts)']
) * 100

df_relevant['percent elderly 85+ 2011'] = (
    df_relevant['Broad Age Groups: 85 years and over (2011 Counts)'] /
    df_relevant['Total (2011 Counts)']
) * 100

# filter
df_relevant = df_relevant[
    pd.to_numeric(df_relevant['Latitude'], errors='coerce').notna() & 
    pd.to_numeric(df_relevant['Longitude'], errors='coerce').notna()
]
df_relevant = df_relevant[(df_relevant['Latitude'] != 0.0) & (df_relevant['Longitude'] != 0.0)]

# remove duplicates
df_final = df_relevant.drop_duplicates(subset=['Geographic name'], keep='first')

df_final = df_final[['Geographic name', 
                     'percent elderly 65+ 2016', 'percent elderly 85+ 2016', 
                     'percent elderly 65+ 2011', 'percent elderly 85+ 2011', 
                     'Latitude', 'Longitude']]

# save to new csv
df_final.to_csv('data/predictive_data.csv', index=False)
