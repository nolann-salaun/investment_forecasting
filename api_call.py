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

# Print the results
'''
print("ETFs:", etfs)
print("Start date:", start)
print("End date:", end)
'''

'''This function retrieves the historical data for the ETFs inputed by the user
    based on the start and end date they provided.'''

def portfolio_data_retrieval(etf_list, start_date, end_date):
    # Retrieve and print historical data for each ETF in the list.
    for etf in etf_list:
        etf_obj = yf.Ticker(etf)
        data = etf_obj.history(start=start_date, end=end_date)
        print(f"Data for {etf}:")
        print(data.head(20))

portfolio_data_retrieval(etfs, start, end)


