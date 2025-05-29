#coefficient ( R^2 )

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import api_call_V2 as api

class Linear_Regression:
    def __init__(self):
        (
        self.investment_initial_amount, 
        self.investment_monthly_amount,
        self.investment_start_date, 
        self.investment_durations, 
        self.etfs, 
        self.end_date,
        self.df_etf
        ) = api.main_api_call()

        self.investment_start_date = pd.to_datetime(self.investment_start_date)
        self.df_etf = self.df_etf.iloc[1:].sort_index()
        #self.df['days_since_start'] = (df['Date'] - df['Date'].min()).dt.days #convert date to number for regression
        self.dict_of_dfs = {ticker: group for ticker, group in self.df_etf.groupby('ticker')}

    def training(self):
        # Dictionary to store ETFs
        dict_etf = {}
        
        for ticker, ticker_df in self.dict_of_dfs.items():
            df = ticker_df.copy()
            df = df.reset_index()
            df['Date_ordinal'] = df['Date'].map(pd.Timestamp.toordinal)
            X = df[['Date_ordinal']]
            y = df['Close']
            model = LinearRegression()
            model.fit(X, y)
            df['predicted_close'] = model.predict(X)
            dict_etf[ticker] = df
            horizon = 365
            future_days = np.arange(df['days_since_start'].max() + 1,
            df['days_since_start'].max() + horizon + 1).reshape(-1, 1)
            future_preds = model.predict(future_days)

        return dict_etf, future_preds

    

# Nombre de jours pour extrapoler (par exemple 365 jours dans le futur)


'''

# Tracé avec projection
plt.figure(figsize=(10, 5))
plt.plot(df_etf['Date'], df_etf['Close'], label='Prix réel')
plt.plot(df_etf['Date'], df_etf['predicted_close'], label='Prix prédit', linestyle='--')
future_dates = [df_etf['Date'].max() + pd.Timedelta(days=int(i)) for i in range(1, horizon + 1)]
plt.plot(future_dates, future_preds, label='Projection future', linestyle=':', color='red')
plt.title(f"Projection linéaire sur {ticker}")
plt.xlabel("Date")
plt.ylabel("Cours")
plt.legend()
plt.grid(True)
plt.show()
'''

def main_LR():
    LR = Linear_Regression()
    df_result = LR.training()

    print(df_result)


main_LR()
