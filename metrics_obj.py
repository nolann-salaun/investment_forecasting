import pandas as pd
import api_call_V2 as api
from dateutil.relativedelta import relativedelta
import numpy as np

# Step 1: Get user input for ETFs and date range1
#etfs, start, end = api.user_input()
class Portfolio:
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
        self.df_etf['previous_day_price_closure'] = self.df_etf['Close'].shift(1) #Get the price closure of the day before
        self.df_etf = self.df_etf.iloc[1:]

    def apply_monthly_investment(self):
        df = self.df_etf.copy()
        df.index = pd.to_datetime(df.index)
        df.index = df.index.tz_localize(None)
        start_date = pd.to_datetime(self.investment_start_date)
        df['investment'] = 0.0

         # Add initial investment on the closest available date
        if start_date in df.index:
            df.at[start_date, 'investment'] += self.investment_initial_amount
        else:
            closest = df.index[df.index >= start_date].min()
            if pd.notna(closest):
                df.at[closest, 'investment'] += self.investment_initial_amount
                start_date = closest  # Adjust to actual start date found in index

        # Get the next month after the initial investment
        first_monthly_investment_date = (start_date + pd.DateOffset(months=1)).replace(day=1)

        # Apply monthly investments starting from M+1
        months = df.index.to_series().dt.to_period('M').unique()
        for month in months:
            month_start_date = pd.Period(month).start_time
            if month_start_date >= first_monthly_investment_date:
                first_day = df[df.index.to_series().dt.to_period('M') == month].index.min()
                if pd.notna(first_day):
                    df.at[first_day, 'investment'] = self.investment_monthly_amount

        df = df[df['investment'] != 0.0]
        df['cumulative_investment'] = df['investment'].cumsum()
        return df
    

    def apply_ETF_purchase(self):
        df = self.apply_monthly_investment()
        df['etf_units_purchased'] = 0
        df['total_etf_units'] = 0
        df['cash'] = 0.0
        df['net_worth'] = 0.0
        df['global_PnL'] = 0.0
        df['global_PnL %'] = 0.0
        leftover = 0.0
        total_units = 0.0

        for idx in df.index:
            investment = df.at[idx, 'investment'] + leftover
            price = df.at[idx, 'previous_day_price_closure']
            units_bought = np.floor(investment / price)
            spent = units_bought * price
            leftover = investment - spent
            total_units += units_bought

            df.at[idx, 'etf_units_purchased'] = units_bought
            df.at[idx, 'cash'] = leftover
            df.at[idx, 'total_etf_units'] = total_units
            df.at[idx, 'net_worth'] = df.at[idx, 'total_etf_units'] * df.at[idx, 'previous_day_price_closure'] + leftover
            df.at[idx, 'global_PnL'] = df.at[idx, 'net_worth'] - df.at[idx, 'cumulative_investment']
            df.at[idx, 'global_PnL %'] = ((df.at[idx, 'net_worth'] / df.at[idx, 'cumulative_investment'] - 1) * 100).round(2)
        return df

def main_metrics():
    portfolio = Portfolio()
    df_result = portfolio.apply_monthly_investment()
    df_result = portfolio.apply_ETF_purchase()
    print(df_result)

main_metrics()


