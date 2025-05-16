import pandas as pd
import numpy as np
import yfinance as yf


'''This function is used to collect the user input regarding the ETF they want to add in their portfolio
    based on their Ticker and the start and end date for the data they want to retrieve.'''
def user_input():
    # list to store tickers
    etf_list = []
    etf_num = int(input("How many ETFs do you want to enter? "))
    # Loop to collect each ETF
    for i in range(etf_num):
        etf = input(f"Enter ETF ticker #{i + 1}: ")
        etf_list.append(etf)
    start_date = input("Enter the start date (YYYY-MM-DD): ")
    end_date = input("Enter the end date (YYYY-MM-DD): ")
    return etf_list, start_date, end_date

'''This function aims to retrieve the ETF information from the yfinance API and specifically the fees'''
def get_etf_info(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info    
    return {'fees': info.get('netExpenseRatio'),'ticker': info.get('ticker', ticker_symbol)}


'''This function retrieves the historical data for the ETFs inputed by the user
    based on the start and end date they provided.'''
def portfolio_data_retrieval(etf_list, start_date, end_date):
    # Retrieve and print historical data for each ETF in the list.
    data_dict = {}
    for etf in etf_list:
        # TBC if etf_obj can be used in the get_etf_info function to remove redundancies and lines of code
        etf_obj = yf.Ticker(etf)
        info = get_etf_info(etf)
        data = etf_obj.history(start=start_date, end=end_date)
        data['fees'] = info['fees']
        data['ticker'] = info['ticker']
        data_dict[etf] = data
    return data_dict

# Call the user_input function to get the ETF list and date range
etfs, start, end = user_input()
# Call the portfolio_data_retrieval function to get the data in a dictionary
data_dict = portfolio_data_retrieval(etfs, start, end)


'''This function is used to clean the data retrieved from the API call and merge the etfs in a single dataframe'''
def data_cleaning(data_dict):
    cleaned_list = []
    for symbol, data in data_dict.items():
        df_clean = data.copy()
        df_clean = df_clean.dropna()
        df_clean = df_clean.round(2)
        cleaned_list.append(df_clean)

    if cleaned_list:
        df_clean = pd.concat(cleaned_list)

    return df_clean

print(data_cleaning(data_dict))

'''This function is used to collect the user input regarding the investment they want to make'''
def user_investment():
    initial_amount = float(input("Enter the initial amount you want to invest: "))
    recurrent_amount_investment = float(input("Enter the amount you want to invest every month: "))
    recurrence_time_investment = int(input("Enter the duration of your investment in months: "))
    return f' Your initial investment amount is of ${initial_amount}, every month you allocate ${recurrent_amount_investment}, investment_duration is {recurrence_time_investment} months'

print(user_investment())