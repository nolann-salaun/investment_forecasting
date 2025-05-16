import yfinance as yf
from datetime import datetime
import pandas as pd
import api_call as api
from dateutil.relativedelta import relativedelta

# Step 1: Get user input for ETFs and date range1
etfs, start, end = api.user_input()
# Step 2: Retrieve data for the selected ETFs
data_dict = api.portfolio_data_retrieval(etfs, start, end)  
df_etf = api.data_cleaning(data_dict)
df_etf['previous_day_price_closure'] = df_etf['Close'].shift(1)


investment_initial_amount, investment_amount_frequency, investment_start_date, investment_durations = api.user_investment()


def apply_monthly_investment(df, investment_initial_amount, investment_amount_frequency, start_date):
    df = df.copy()
    df['investment'] = 0.0

    # Convertir la date de départ et calculer la date de fin
    start_date = pd.to_datetime(start_date)
    end_date = df_etf['Date'][-1]

    # Filtrer la période
    mask = (df.index >= start_date) & (df.index <= end_date)
    df_filtered = df.loc[mask]

    # Identifier les premiers jours de chaque mois dans la période
    months = df_filtered.index.to_series().dt.to_period('M').unique()

    # Ajouter le montant investi chaque mois
    for month in months:
        first_day = df_filtered[df_filtered.index.to_series().dt.to_period('M') == month].index.min()
        if pd.notna(first_day):
            df.at[first_day, 'investment'] = investment_amount_frequency

    # Ajouter l'investissement initial le premier jour
    if start_date in df.index:
        df.at[start_date, 'investment'] += investment_initial_amount
    else:
        # Si start_date n'existe pas exactement dans l'index, on le place au plus proche après
        closest = df.index[df.index >= start_date].min()
        if pd.notna(closest):
            df.at[closest, 'investment'] += investment_initial_amount

    return df

df_etf = apply_monthly_investment(df_etf, investment_initial_amount, investment_amount_frequency, investment_start_date)


print(df_etf)