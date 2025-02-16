import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

df = pd.read_csv('data/predictive_data.csv')

required_cols = [
    'percent elderly 65+ 2011', 
    'percent elderly 65+ 2016', 
    'percent elderly 85+ 2011', 
    'percent elderly 85+ 2016'
]

df = df.dropna(subset=required_cols)

# --- prediction function ---
def predict_future(row, future_year=2017):
    years = np.array([2011, 2016]).reshape(-1, 1)
    
    # 65+ population regression
    perc65 = np.array([row['percent elderly 65+ 2011'], row['percent elderly 65+ 2016']])
    model65 = LinearRegression().fit(years, perc65)
    pred65 = model65.predict(np.array([[future_year]]))[0]
    
    # 85+ population regression
    perc85 = np.array([row['percent elderly 85+ 2011'], row['percent elderly 85+ 2016']])
    model85 = LinearRegression().fit(years, perc85)
    pred85 = model85.predict(np.array([[future_year]]))[0]
    
    return pd.Series({'predicted 65+': pred65, 'predicted 85+': pred85})

df[['predicted 65+', 'predicted 85+']] = df.apply(predict_future, axis=1)

# [0, 100] range ---
df[['predicted 65+', 'predicted 85+']] = df[['predicted 65+', 'predicted 85+']].clip(lower=0, upper=100)

# save
df.to_csv('data/predicted_census_data_1.csv', index=False)
