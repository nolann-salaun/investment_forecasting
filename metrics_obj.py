import pandas as pd
import api_call_V2 as api
from dateutil.relativedelta import relativedelta
import numpy as np

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
        self.df_etf = self.df_etf.iloc[1:].sort_index()
        self.dict_of_dfs = {ticker: group for ticker, group in self.df_etf.groupby('ticker')}


    def apply_monthly_investment(self):
        # Dictionary to store ETFs
        dict_etf = {}
        
        for ticker, ticker_df in self.dict_of_dfs.items():
            df = ticker_df.copy()
            df.index = pd.to_datetime(df.index)
            df.index = df.index.tz_localize(None)
            start_date = pd.to_datetime(self.investment_start_date)
            df['investment'] = 0.0

            # Initial investment
            if start_date in df.index:
                df.at[start_date, 'investment'] += self.investment_initial_amount * float(df.loc[start_date, 'etf_allocation'])
            else:
                closest = df.index[df.index >= start_date].min()
                if pd.notna(closest):
                    df.at[closest, 'investment'] += self.investment_initial_amount * float(df.loc[closest, 'etf_allocation'])
                    start_date = closest

            # Monthly investment (starting M+1)
            first_monthly_date = (start_date + pd.DateOffset(months=1)).replace(day=1)
            months = df.index.to_series().dt.to_period('M').unique()
            
            for month in months:
                month_start = pd.Period(month).start_time
                if month_start >= first_monthly_date:
                    first_day = df[df.index.to_series().dt.to_period('M') == month].index.min()
                    if pd.notna(first_day):
                        df.at[first_day, 'investment'] = self.investment_monthly_amount * float(df.loc[first_day, 'etf_allocation'])

            
            df = df[df['investment'] != 0.0]
            df['etf_cumulative_investment'] = df['investment'].cumsum()
            dict_etf[ticker] = df
            
        return dict_etf

    
    def apply_ETF_purchase(self):
        
        dict_etf = self.apply_monthly_investment()
        
        for ticker, df in dict_etf.items():
        
            df = df.copy()
            
            df['etf_units_purchased'] = 0
            df['total_etf_units'] = 0
            df['cash'] = 0.0
            df['ETF_net_worth'] = 0.0
            df['ETF_PnL'] = 0.0
            df['ETF_PnL %'] = 0.0
            df['ticker'] = ticker  
            
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
                df.at[idx, 'ETF_net_worth'] = total_units * price + leftover
                df.at[idx, 'ETF_PnL'] = df.at[idx, 'ETF_net_worth'] - df.at[idx, 'etf_cumulative_investment']
                df.at[idx, 'ETF_PnL %'] = ((df.at[idx, 'ETF_net_worth'] / df.at[idx, 'etf_cumulative_investment'] - 1) * 100).round(2)
            
            dict_etf[ticker] = df
        
        # Merging ETF dataframe and sort per date
        consolidated_df = pd.concat(dict_etf).sort_index().sort_values(['Date', 'ticker'])
        consolidated_df['cumulative_investment'] = consolidated_df['investment'].cumsum()
        return consolidated_df
    
    def apply_CAGR_ratio(self):
        df = self.apply_ETF_purchase()
        
        # Collection of last row for each ETF
        cagr = df.groupby('ticker').last()[['ETF_net_worth', 'etf_cumulative_investment']].copy()
        
        # ETF CAGR
        cagr['CAGR'] = (
            (cagr['ETF_net_worth'] / cagr['etf_cumulative_investment']) ** (1 / self.investment_durations) - 1
        ).round(4) * 100
        
        # Total CAGR
        total_net = cagr['ETF_net_worth'].sum()
        total_invest = cagr['etf_cumulative_investment'].sum()
        global_cagr = ((total_net / total_invest) ** (1 / self.investment_durations) - 1) * 100
        total_row = pd.DataFrame({
            'ETF_net_worth': [total_net],
            'etf_cumulative_investment': [total_invest],
            'CAGR': [round(global_cagr, 4)]
        }, index=['TOTAL'])
        
        result = pd.concat([cagr, total_row])[['ETF_net_worth', 'etf_cumulative_investment', 'CAGR']]
        
        return result
    


def main_metrics():
    portfolio = Portfolio()
    df_result = portfolio.apply_monthly_investment()
    df_result = portfolio.apply_ETF_purchase()
    cagr = portfolio.apply_CAGR_ratio()
    print(df_result)
    print(cagr)

main_metrics()


