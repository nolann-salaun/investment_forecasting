from etfdataretrieval import ETFDataRetrieval
from visualizer import Visualizer
import pandas as pd
import numpy as np

class Portfolio:
    def __init__(self):
        self.investment_initial_amount = None
        self.investment_monthly_amount = None
        self.investment_start_date = None
        self.investment_durations = None
        self.etfs = None
        self.end_date = None
        self.df_etf = None
        self.visualizer = None
        self.cagr = None
        self.sharpe_ratio = None
        self.volatility = None
        self.investment_frequency = None
    
    def configure_from_input(self, initial_amount, monthly_amount, start_date, duration, etfs, frequency='M'):
        self.investment_initial_amount = initial_amount
        self.investment_monthly_amount = monthly_amount
        self.investment_start_date = pd.to_datetime(start_date)
        self.investment_durations = duration
        self.etfs = etfs
        self.end_date = (self.investment_start_date + pd.DateOffset(years=duration)).strftime("%Y-%m-%d")
        self.investment_frequency = frequency
        
        # Get ETF data
        etf_retriever = ETFDataRetrieval()
        data_dict = etf_retriever.portfolio_data_retrieval(etfs, start_date, self.end_date)
        self.df_etf = etf_retriever.data_cleaning(data_dict)
        self.df_etf['previous_day_price_closure'] = self.df_etf['Close'].shift(1)
        self.df_etf = self.df_etf.iloc[1:].sort_index()
        self.dict_of_dfs = {ticker: group for ticker, group in self.df_etf.groupby('ticker')}

    def apply_periodic_investment(self):
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

            # Determine frequency and first investment date
            if self.investment_frequency == 'M':
                freq_offset = pd.DateOffset(months=1)
                period = 'M'
            elif self.investment_frequency == 'Q':
                freq_offset = pd.DateOffset(months=3)
                period = 'Q'
            elif self.investment_frequency == '6M':
                freq_offset = pd.DateOffset(months=6)
                period = '6M'
            elif self.investment_frequency == 'Y':
                freq_offset = pd.DateOffset(years=1)
                period = 'Y'
            
            first_periodic_date = start_date + freq_offset
            
            # Get unique periods based on frequency
            periods = df.index.to_series().dt.to_period(period).unique()
            
            for p in periods:
                period_start = pd.Period(p).start_time
                if period_start >= first_periodic_date:
                    first_day = df[df.index.to_series().dt.to_period(period) == p].index.min()
                    if pd.notna(first_day):
                        df.at[first_day, 'investment'] = self.investment_monthly_amount * float(df.loc[first_day, 'etf_allocation'])

            df = df[df['investment'] != 0.0]
            df['etf_cumulative_investment'] = df['investment'].cumsum()
            dict_etf[ticker] = df
            
        return dict_etf

    def apply_ETF_purchase(self):
        dict_etf = self.apply_periodic_investment()
        
        for ticker, df in dict_etf.items():
            df = df.copy()
            
            df['etf_units_purchased'] = 0
            df['total_etf_units'] = 0
            df['cash'] = 0.0
            df['ETF_net_worth'] = 0.0
            df['ETF_PnL'] = 0.0
            df['ETF_PnL_%'] = 0.0
            df['ticker'] = ticker  
            
            leftover = 0.0
            total_units = 0.0

            for idx in df.index:
                investment = df.at[idx, 'investment'] + leftover
                price = df.at[idx, 'previous_day_price_closure'] * (1 + df.at[idx, 'fees'])                
                
                units_bought = np.floor(investment / price)
                spent = units_bought * price
                leftover = investment - spent
                total_units += units_bought

                df.at[idx, 'etf_units_purchased'] = units_bought
                df.at[idx, 'cash'] = leftover
                df.at[idx, 'total_etf_units'] = total_units
                df.at[idx, 'ETF_net_worth'] = total_units * price + leftover
                df.at[idx, 'ETF_PnL'] = df.at[idx, 'ETF_net_worth'] - df.at[idx, 'etf_cumulative_investment']
                df.at[idx, 'ETF_PnL_%'] = ((df.at[idx, 'ETF_net_worth'] / df.at[idx, 'etf_cumulative_investment'] - 1) * 100).round(2)
            
            dict_etf[ticker] = df
        
        # Merging ETF dataframe and sort per date
        consolidated_df = pd.concat(dict_etf).sort_index().sort_values(['Date', 'ticker'])

        daily_totals_Inv = consolidated_df.groupby('Date')['investment'].sum().reset_index()
        daily_totals_Inv['cumulative_investment'] = daily_totals_Inv['investment'].cumsum()
        consolidated_df = pd.merge(
            consolidated_df,
            daily_totals_Inv[['Date', 'cumulative_investment']],
            on='Date',
            how='left'
        )

        daily_totals_PnL = consolidated_df.groupby('Date')['ETF_PnL'].sum().reset_index()
        daily_totals_PnL['Portfolio_PnL'] = daily_totals_PnL['ETF_PnL']
        consolidated_df = pd.merge(
            consolidated_df,
            daily_totals_PnL[['Date', 'Portfolio_PnL']],
            on='Date',
            how='left'
        )
        
        daily_totals_networth = consolidated_df.groupby('Date')['ETF_net_worth'].sum().reset_index()
        daily_totals_networth['Portfolio_net_worth'] = daily_totals_networth['ETF_net_worth']
        consolidated_df = pd.merge(
            consolidated_df,
            daily_totals_networth[['Date', 'Portfolio_net_worth']],
            on='Date',
            how='left'
        )

        for idx in consolidated_df.index:
            consolidated_df.at[idx, 'Portfolio_PnL_%'] = ((consolidated_df.at[idx, 'Portfolio_net_worth'] / consolidated_df.at[idx, 'cumulative_investment'] - 1) * 100).round(2)

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
            'CAGR': [round(global_cagr, 2)]
        }, index=['TOTAL'])
        
        result = pd.concat([cagr, total_row])[['ETF_net_worth', 'etf_cumulative_investment', 'CAGR']]
        
        return result
    
    def apply_SHARPE_ratio(self):
        df = self.apply_ETF_purchase()
        volatility_df = df.groupby('ticker')['ETF_PnL_%'].std().round(2)
        volatility_df = volatility_df.to_frame(name='volatility')

        global_volatility = df['Portfolio_PnL_%'].std().round(2)
        total_row = pd.DataFrame({
        'volatility': [global_volatility],
        }, index=['TOTAL'])

        volatility_df = pd.concat([volatility_df, total_row])[['volatility']]

        sharpe_ratio = ((df['Portfolio_PnL_%'].iloc[-1] - 2) / volatility_df['volatility'].iloc[-1]).round(2)

        return volatility_df, sharpe_ratio
        
    def calculate_all_metrics(self):
        """Calculate all metrics and prepare visualizations"""
        df_result = self.apply_ETF_purchase()
        self.cagr = self.apply_CAGR_ratio()
        self.volatility, self.sharpe_ratio = self.apply_SHARPE_ratio()
        
        # Calculate ACWI metrics for comparison
        acwi_metrics = self.calculate_acwi_comparison()
        
        self.visualizer = Visualizer(df_result, acwi_data=acwi_metrics['acwi_data'])
        return {    
            "data": df_result,
            "cagr": self.cagr,
            "volatility": self.volatility, #To be removed?
            "sharpe_ratio": self.sharpe_ratio,
            "acwi_cagr": acwi_metrics['acwi_cagr'],
            "acwi_sharpe": acwi_metrics['acwi_sharpe'],
            "acwi_data": acwi_metrics['acwi_data'],
            "plots": self.visualizer.get_plots(cagr_data=self.cagr.iloc[:-1])
        }
    
    def calculate_acwi_comparison(self):
        # Calculate ACWI performance with same investment pattern
        # Create a temporary portfolio with 100% ACWI
        acwi_portfolio = Portfolio()
        acwi_portfolio.configure_from_input(
            self.investment_initial_amount,
            self.investment_monthly_amount,
            self.investment_start_date.strftime("%Y-%m-%d"),
            self.investment_durations,
            [('ACWI', 1.0)]
        )
        
        # Get ACWI data
        acwi_data = acwi_portfolio.apply_ETF_purchase()
        
        # Calculate ACWI CAGR
        acwi_cagr = acwi_portfolio.apply_CAGR_ratio().loc['TOTAL', 'CAGR']
        
        # Calculate ACWI Sharpe ratio
        _, acwi_sharpe = acwi_portfolio.apply_SHARPE_ratio()
        
        return {
            'acwi_data': acwi_data,
            'acwi_cagr': acwi_cagr,
            'acwi_sharpe': acwi_sharpe
        }
