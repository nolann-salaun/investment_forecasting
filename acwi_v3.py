import pandas as pd
import numpy as np
from pandas.tseries.offsets import BDay
import yfinance as yf
from API_call_V3 import InvestmentInputManager, ETFDataHandler

class InvestmentSimulator:
    """Contains all the investment simulation logic from original acwi_v3"""
    @staticmethod
    def apply_monthly_investment_to_etf(df, start_date, initial_amount, monthly_amount, allocation):
        df = df.copy()
        df.index = pd.to_datetime(df.index).tz_localize(None)  # Remove timezone for consistency
        df['etf_allocation'] = allocation
        df['investment'] = 0.0
        start_date = pd.to_datetime(start_date).tz_localize(None)  # Ensure start_date is timezone-naive

        if start_date in df.index:
            df.at[start_date, 'investment'] += initial_amount * allocation
        else:
            closest_start_date = df.index[df.index >= start_date].min()
            if pd.notna(closest_start_date):
                df.at[closest_start_date, 'investment'] += initial_amount * allocation
                start_date = closest_start_date

        first_monthly_date = (start_date + pd.DateOffset(months=1)).replace(day=1)
        months = df.index.to_series().dt.to_period('M').unique()
        
        for month in months:
            month_start = pd.Period(month).start_time
            if month_start >= first_monthly_date:
                first_day = df[df.index.to_series().dt.to_period('M') == month].index.min()
                if pd.notna(first_day):
                    df.at[first_day, 'investment'] = monthly_amount * allocation
        
        df = df[df['investment'] != 0.0]
        df['etf_cumulative_investment'] = df['investment'].cumsum()
        return df

    @staticmethod
    def apply_etf_purchase_to_portfolio(df, ticker=None):
        df = df.copy()
        if ticker is not None:
            df['ticker'] = ticker
            
        df['etf_units_purchased'] = 0.0
        df['total_etf_units'] = 0.0
        df['cash'] = 0.0
        df['ETF_net_worth'] = 0.0
        df['ETF_PnL'] = 0.0
        df['ETF_PnL_%'] = 0.0
        
        leftover = 0.0
        total_units = 0.0

        for idx in df.index:
            investment = df.at[idx, 'investment'] + leftover
            price = df.at[idx, 'Close']
            units_bought = np.floor(investment / price)
            spent = units_bought * price
            leftover = investment - spent
            total_units += units_bought

            df.at[idx, 'etf_units_purchased'] = units_bought
            df.at[idx, 'cash'] = leftover
            df.at[idx, 'total_etf_units'] = total_units
            df.at[idx, 'ETF_net_worth'] = total_units * price + leftover
            df.at[idx, 'ETF_PnL'] = df.at[idx, 'ETF_net_worth'] - df.at[idx, 'etf_cumulative_investment']
            df.at[idx, 'ETF_PnL_%'] = (df.at[idx, 'ETF_net_worth'] / df.at[idx, 'etf_cumulative_investment'] - 1) * 100

        df = df.reset_index().rename(columns={"index": "Date"})
        df['cumulative_investment'] = df['investment'].cumsum()
        df['Portfolio_PnL'] = df['ETF_PnL']
        df['Portfolio_net_worth'] = df['ETF_net_worth']
        df['Portfolio_PnL_%'] = (df['Portfolio_net_worth'] / df['cumulative_investment'] - 1) * 100
        return df.round(2)

    @staticmethod
    def calculate_cagr(df, investment_duration):
        cagr = df.groupby('ticker').last()[['ETF_net_worth', 'etf_cumulative_investment']].copy()
        cagr['CAGR'] = (
            (cagr['ETF_net_worth'] / cagr['etf_cumulative_investment']) ** (1 / investment_duration) - 1
        ).round(4) * 100
        
        total_net = cagr['ETF_net_worth'].sum()
        total_invest = cagr['etf_cumulative_investment'].sum()
        global_cagr = ((total_net / total_invest) ** (1 / investment_duration) - 1) * 100
        
        total_row = pd.DataFrame({
            'ETF_net_worth': [total_net],
            'etf_cumulative_investment': [total_invest],
            'CAGR': [round(global_cagr, 2)]
        }, index=['TOTAL'])
        
        return pd.concat([cagr, total_row])[['ETF_net_worth', 'etf_cumulative_investment', 'CAGR']]

    @staticmethod
    def align_start_dates(df_portfolio, df_benchmark):
        df_portfolio.index = pd.to_datetime(df_portfolio.index).tz_localize(None)
        df_benchmark.index = pd.to_datetime(df_benchmark.index).tz_localize(None)
        benchmark_start = df_benchmark.index.min()
        portfolio_start = df_portfolio.index.min()
        
        if portfolio_start < benchmark_start:
            return df_portfolio[df_portfolio.index >= benchmark_start].copy()
        return df_portfolio


def main():
    # Initialize components
    input_manager = InvestmentInputManager()
    data_handler = ETFDataHandler()
    simulator = InvestmentSimulator()

    # Get user inputs
    initial_amount, monthly_amount, start_date, duration = input_manager.get_investment_parameters()
    etfs, start_date, end_date = input_manager.get_etf_allocation(start_date, duration)

    # Get benchmark data (ACWI)
    acwi_ticker = "IMIE.PA"
    acwi_data = data_handler.process_portfolio_data([(acwi_ticker, 1.0)], start_date, end_date)
    df_acwi = data_handler.clean_data(acwi_data)
    df_acwi = simulator.apply_monthly_investment_to_etf(df_acwi, start_date, initial_amount, monthly_amount, 1.0)
    df_acwi = simulator.apply_etf_purchase_to_portfolio(df_acwi, acwi_ticker)

    # Get user portfolio data
    portfolio_data = data_handler.process_portfolio_data(etfs, start_date, end_date)
    df_portfolio = data_handler.clean_data(portfolio_data)
    
    # Ensure all datetimes are timezone-naive for comparison
    df_acwi['Date'] = pd.to_datetime(df_acwi['Date']).dt.tz_localize(None)
    acwi_start_date = df_acwi['Date'].min()
    
    # Process each ETF in the portfolio using the same start date as ACWI
    processed_etfs = []
    for ticker, group in df_portfolio.groupby('ticker'):
        group.index = pd.to_datetime(group.index).tz_localize(None)  # Remove timezone
        allocation = group['allocation'].iloc[0]
        # Filter the group to start from the same date as ACWI
        group = group[group.index >= acwi_start_date]
        if not group.empty:
            etf_data = simulator.apply_monthly_investment_to_etf(
                group, acwi_start_date, initial_amount, monthly_amount, allocation
            )
            etf_data = simulator.apply_etf_purchase_to_portfolio(etf_data, ticker)
            processed_etfs.append(etf_data)
    
    if not processed_etfs:
        raise ValueError("No valid portfolio data available after aligning start dates with ACWI")
    
    df_portfolio_metrics = pd.concat(processed_etfs).sort_values("Date")

    # Calculate metrics
    acwi_cagr = simulator.calculate_cagr(df_acwi, duration)
    portfolio_cagr = simulator.calculate_cagr(df_portfolio_metrics, duration)
    
    acwi_pnl = df_acwi['Portfolio_PnL_%'].iloc[-1]
    last_rows = df_portfolio_metrics.groupby('ticker').last()
    weighted_pnl = (last_rows['Portfolio_PnL_%'] * last_rows['allocation']).sum()

    # Display results
    print("\nACWI CAGR RESULT")
    print(acwi_cagr)
    print("\nETF PORTFOLIO CAGR RESULT")
    print(portfolio_cagr)
    print("\nPortfolio_PnL_% Comparison")
    print(f"ACWI Portfolio_PnL_%: {acwi_pnl:.2f}%")
    print(f"User ETF Portfolio Portfolio_PnL_%: {weighted_pnl:.2f}%")

    return {
        'acwi_data': df_acwi,
        'portfolio_data': df_portfolio_metrics,
        'acwi_cagr': acwi_cagr,
        'portfolio_cagr': portfolio_cagr
    }


if __name__ == "__main__":
    main()