import pandas as pd
import numpy as np
import api_call_V2 as api
#import metrics_obj as mo

"This function allocates the monthly investment based on the proportion given by the user for each period"
def apply_monthly_investment_to_etf(df, start_date, initial_amount, monthly_amount, allocation):
    df = df.copy()
    #removes the timezone information to avoid confusion
    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_localize(None)
    df['etf_allocation'] = allocation
    df['investment'] = 0.0
    #checking the type of start_date column
    start_date = pd.to_datetime(start_date)

    # Initiate the investment from the user input from the start_date or the nearest date from start_date
    if start_date in df.index:
        df.at[start_date, 'investment'] += initial_amount * allocation
    else:
        closest_start_date = df.index[df.index >= start_date].min()
        if pd.notna(closest_start_date):
            df.at[closest_start_date, 'investment'] += initial_amount * allocation
            start_date = closest_start_date

    # Initiate the monthly investment amount one moonth after the start_date on the first opening day
    first_monthly_date = (start_date + pd.DateOffset(months=1)).replace(day=1)
    months = df.index.to_series().dt.to_period('M').unique()
    for month in months:
        month_start = pd.Period(month).start_time
        if month_start >= first_monthly_date:
            first_day = df[df.index.to_series().dt.to_period('M') == month].index.min()
            if pd.notna(first_day):
                df.at[first_day, 'investment'] = monthly_amount * allocation
    # Store tin the datframe only the necessary rows where investment were done, remaining rows are useless
    df = df[df['investment'] != 0.0]
    # Calculate cumulative investment containing initial investment + monthly investments
    df['etf_cumulative_investment'] = df['investment'].cumsum()
    return df

# Create the desired column (future metrics) for the ACWI ETF
def apply_etf_purchase_to_acwi(df, ticker=None):
    df = df.copy()
    if ticker is not None:
        df['ticker'] = ticker
    df['etf_units_purchased'] = 0.0
    df['total_etf_units'] = 0.0
    df['cash'] = 0.0
    df['ETF_net_worth'] = 0.0
    df['ETF_PnL'] = 0.0
    df['ETF_PnL_%'] = 0.0
    leftover = 0.0 # corresponds to the cash left after buying x part of an etf
    total_units = 0.0

# For loop iterates over each investment period in the dataframe and calculates the number of etf that can be purchased
    for idx in df.index:
        investment = df.at[idx, 'investment'] + leftover # investment of N+1 + leftover of N corresponds to the investment on N+1
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
        df.at[idx, 'ETF_PnL_%'] = ((df.at[idx, 'ETF_net_worth'] / df.at[idx, 'etf_cumulative_investment'] - 1) * 100).round(2)

    df = df.reset_index().rename(columns={"index": "Date"})
    df['cumulative_investment'] = df['investment'].cumsum()
    df['Portfolio_PnL'] = df['ETF_PnL']
    df['Portfolio_net_worth'] = df['ETF_net_worth']
    df['Portfolio_PnL_%'] = ((df['Portfolio_net_worth'] / df['cumulative_investment'] - 1) * 100).round(2)
    return df

# Calculates the VAGR for the etf of each portfolio and the global portfolio (user portfolio vs ACWI portfolio)
def apply_cagr_ratio(df, investment_durations):
    df = df.copy()
    cagr = df.groupby('ticker').last()[['ETF_net_worth', 'etf_cumulative_investment']].copy()
    cagr['CAGR'] = (
        (cagr['ETF_net_worth'] / cagr['etf_cumulative_investment']) ** (1 / investment_durations) - 1
    ).round(4) * 100
    total_net = cagr['ETF_net_worth'].sum()
    total_invest = cagr['etf_cumulative_investment'].sum()
    global_cagr = ((total_net / total_invest) ** (1 / investment_durations) - 1) * 100
    total_row = pd.DataFrame({
        'ETF_net_worth': [total_net],
        'etf_cumulative_investment': [total_invest],
        'CAGR': [round(global_cagr, 2)]
    }, index=['TOTAL'])
    result = pd.concat([cagr, total_row])[['ETF_net_worth', 'etf_cumulative_investment', 'CAGR']]
    return result

# Collect the ACWI ETF data in order to make the comparison possible
def get_acwi_data(investment_start_date, end_date, initial_amount, monthly_amount):
    acwi_ticker = "IMIE.PA"
    acwi_allocation = 1.0
    acwi_etf_list = [(acwi_ticker, acwi_allocation)]
    etf_manager = api.etf_data_retrieval()
    #Call to retrieve the data from the API through the etf_manager object (see the class in api_call_V2.py)
    acwi_data_dict = etf_manager.portfolio_data_retrieval(acwi_etf_list, investment_start_date, end_date)
    df_acwi = etf_manager.data_cleaning(acwi_data_dict)
    df_acwi['previous_day_price_closure'] = df_acwi['Close'].shift(1)
    df_acwi = df_acwi.iloc[1:]
    # Call the function to apply the monthly investment to the ACWI ETF (see above function for the details)
    df_acwi = apply_monthly_investment_to_etf(
        df_acwi,
        investment_start_date,
        initial_amount,
        monthly_amount,
        acwi_allocation
    )
    return df_acwi

''' Aligning the investment start date between the user portfolio and the ACWI ETF data.
The investment start date for the user portfolio can't happen earlier than the creation of the ACWI ETF.'''
def align_portfolio_start_date_with_acwi(df_portfolio, df_acwi):
    # Convert index to datetime with UTC timezone if it's timezone-aware
    df_portfolio.index = pd.to_datetime(df_portfolio.index, utc=True)
    # Remove timezone information
    df_portfolio.index = df_portfolio.index.tz_localize(None)
    df_acwi.index = pd.to_datetime(df_acwi.index, utc=True)
    df_acwi.index = df_acwi.index.tz_localize(None)
    acwi_start_date = df_acwi.index.min()
    portfolio_start_date = df_portfolio.index.min()
    
    if portfolio_start_date < acwi_start_date:
        return df_portfolio[df_portfolio.index >= acwi_start_date].copy()
    else:
        return df_portfolio


def apply_to_each_etf(df, func, *args, **kwargs):
    results = []
    for ticker, group in df.groupby('ticker'):
        group_result = func(group, *args, **kwargs)
        group_result['ticker'] = ticker
        results.append(group_result)
    return pd.concat(results).sort_index()

# Moving the ticker in the dataframe for better visibility while testing
def move_ticker_to_seventh_column(df):
    cols = list(df.columns)
    if 'ticker' in cols:
        cols.remove('ticker')
        cols.insert(6, 'ticker')
        df = df[cols]
    return df

# Main function to launch the investment strategy and all the functions above
def main():
    # Gathering the user inputs from the API call file
    (initial_amount, monthly_amount, investment_start_date,
     investment_durations, etfs, end_date, df_clean) = api.main_api_call()

    # Preparing final dataframe and metrics for ACWI ETF
    df_acwi = get_acwi_data(investment_start_date, end_date, initial_amount, monthly_amount)
    df_acwi_full = apply_etf_purchase_to_acwi(df_acwi)
    cagr_result = apply_cagr_ratio(df_acwi_full, investment_durations)

    # Preparing data for the user portfolio, calculating metrics on the adjusted start date portfolio
    etf_manager = api.etf_data_retrieval()
    portfolio_data_dict = etf_manager.portfolio_data_retrieval(etfs, investment_start_date, end_date)
    df_portfolio = etf_manager.data_cleaning(portfolio_data_dict)
    df_portfolio['previous_day_price_closure'] = df_portfolio['Close'].shift(1)
    df_portfolio = df_portfolio.iloc[1:]
    df_portfolio_aligned = align_portfolio_start_date_with_acwi(df_portfolio, df_acwi)

    df_portfolio_aligned = apply_to_each_etf(
        df_portfolio_aligned,
        lambda group, start_date, initial_amount, monthly_amount: apply_monthly_investment_to_etf(
            group,
            group.index.min(),
            initial_amount,
            monthly_amount,
            float(group['etf_allocation'].iloc[0])
        ),
        None,
        initial_amount,
        monthly_amount
    )

    df_portfolio_metrics = apply_to_each_etf(
        df_portfolio_aligned,
        apply_etf_purchase_to_acwi
    )
    # Sort the Column Date and adapt the formatiing of the dataframe
    df_portfolio_metrics = move_ticker_to_seventh_column(df_portfolio_metrics)
    df_portfolio_metrics = df_portfolio_metrics.sort_values(by="Date")

    # Calculates the key metrics to compare the portfolio and ACWI : PnL% (weighted by allocation) and the CAGRs
    cagr_portfolio = apply_cagr_ratio(df_portfolio_metrics, investment_durations)
    acwi_pnl = df_acwi_full['Portfolio_PnL_%'].iloc[-1] # Take the last row of ACWI dataframe for the PnL%
    last_rows = df_portfolio_metrics.groupby('ticker').tail(1) # Take the last rows for each ETF 
    weighted_pnl = (last_rows['Portfolio_PnL_%'] * last_rows['etf_allocation']).sum() # To create the PnL% based on the allocation given by the user

    # OUTPUT to display results
    print("\n ACWI CAGR RESULT")
    print(cagr_result)
    print("\n ETF PORTFOLIO CAGR RESULT")
    print(cagr_portfolio)
    print("\n ACWI DataFrame with Metrics")
    print(df_acwi_full)
    print("\n Adjusted ETF Portfolio DataFrame with Metrics")
    print(df_portfolio_metrics)
    print("\n Portfolio_PnL_% Comparison")
    print(f"ACWI Portfolio_PnL_%: {acwi_pnl:.2f}%")
    print(f"User ETF Portfolio  Portfolio_PnL_%: {weighted_pnl:.2f}%")

# Execute the main function when the script is run directly
if __name__ == "__main__":
    main()


