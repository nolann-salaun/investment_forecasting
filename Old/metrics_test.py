import pandas as pd
import api_call_V2 as api
from dateutil.relativedelta import relativedelta

# Step 1: Get user input for ETFs and date range1
#etfs, start, end = api.user_input()
investment_initial_amount, investment_amount_frequency, investment_start_date, investment_durations, etfs, end_date, df_etf = api.main_api_call()
investment_start_date = pd.to_datetime(investment_start_date)
df_etf['previous_day_price_closure'] = df_etf['Close'].shift(1) #Get the price closure of the day before
df_etf = df_etf.iloc[1:]

def apply_monthly_investment(df, investment_initial_amount, investment_amount_frequency, investment_start_date, end_date):
    df = df.copy()
    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_localize(None)  # <-- Add this line
    investment_start_date = pd.to_datetime(investment_start_date)
    df['investment'] = 0.0

    # Filtrer la période
    '''  mask = (df.index >= start_date) & (df.index <= end_date)
    df_filtered = df.loc[mask]'''

    # Identifier les premiers jours de chaque mois dans la période
    months = df.index.to_series().dt.to_period('M').unique()
    for month in months:
        first_day = df[df.index.to_series().dt.to_period('M') == month].index.min()
        if pd.notna(first_day):
            df.at[first_day, 'investment'] = investment_amount_frequency

    # Ajouter l'investissement initial le premier jour
    if investment_start_date in df.index:
        df.at[investment_start_date, 'investment'] += investment_initial_amount
    else:
        # Si investment_start_date n'existe pas exactement dans l'index, on le place au plus proche après
        closest = df.index[df.index >= investment_start_date].min()
        if pd.notna(closest):
            df.at[closest, 'investment'] += investment_initial_amount

    df = df[df['investment'] != 0.0]

    return df

df_etf = apply_monthly_investment(df_etf, investment_initial_amount, investment_amount_frequency, investment_start_date, end_date)


print(df_etf)
