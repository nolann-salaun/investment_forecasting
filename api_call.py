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

# Call the function and store the result
etfs, start, end = user_input()

'''This function retrieves the historical data for the ETFs inputed by the user
    based on the start and end date they provided.'''

def portfolio_data_retrieval(etf_list, start_date, end_date):
    # Retrieve and print historical data for each ETF in the list.
    data_dict = {}
    for etf in etf_list:
        etf_obj = yf.Ticker(etf)
        data = etf_obj.history(start=start_date, end=end_date)
        data['ticker'] = etf
        #data['shortName'] = etf_obj.info.get('shortName', 'N/A')
        data_dict[etf] = data
    return data_dict

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