import pandas as pd
import numpy as np
import yfinance as yf


'''This function is used to collect the user input regarding the ETF they want to add in their portfolio
    based on their Ticker and the start and end date for the data they want to retrieve.'''
def user_input():
    etf_list = []
    etf_num = int(input("How many ETFs do you want to enter? "))
    # Loop to collect each ETF
    for i in range(etf_num):
        etf = input(f"Enter ETF ticker #{i + 1}: ")
        while True:
            etf_proportion = float(input(f"Enter the proportion of ETF {etf} in your portfolio (0-1): "))
            if 0 <= etf_proportion <= 1:
                break
            else:
                print("Proportion must be between 0 and 1.")
        etf_list.append((etf, str(etf_proportion)))
    # Check if the sum of proportions is 1
    total_prop = sum([float(i[1]) for i in etf_list])
    if total_prop != 1:
        print("The sum of proportions must equal 1. Please re-enter your ETFs and proportions.")
        return user_input()
    start_date = input("Enter the start date (YYYY-MM-DD): ")
    end_date = input("Enter the end date (YYYY-MM-DD): ")
    return etf_list, start_date, end_date

'''This function aims to retrieve the ETF information from the yfinance API and specifically the fees'''
def get_etf_info(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    return {'fees': info.get('netExpenseRatio'), 'ticker': info.get('ticker', ticker_symbol)}

'''This function retrieves the historical data for the ETFs inputed by the user
    based on the start and end date they provided.'''
def portfolio_data_retrieval(etf_list, start_date, end_date):
    # Retrieve and print historical data for each ETF in the list.
    data_dict = {}
    for etf in etf_list:
        etf_info = get_etf_info(etf[0])
        ticker_obj = yf.Ticker(etf[0])
        data = ticker_obj.history(start=start_date, end=end_date)
        data['fees'] = etf_info['fees']
        data['ticker'] = etf_info['ticker']
        data['etf_allocation'] = etf[1]
        data_dict[etf] = data
    return data_dict

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

'''This function is used to collect the user input regarding the investment they want to make'''
def user_investment():
    #Error handling for the user input is required to make sure the integer are positive values
    while True:
        try:
            investment_initial_amount = float(input("Enter the initial amount you want to invest: "))
            if investment_initial_amount > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid positive number.")

    while True:
        try:
            investment_amount_frequency = float(input("Enter the amount you want to invest every month: "))
            if investment_amount_frequency > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid positive number.")

    while True:
        try:
            investment_plan_frequency = int(input("Enter the frequency of your investment in months: "))
            if investment_plan_frequency > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid positive number.")

    while True:
        try:
            investment_durations = int(input("Enter the duration of your investment in years: "))
            if investment_durations > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid positive number.")

    return f'Your initial investment amount is ${investment_initial_amount}, every {investment_plan_frequency} month you allocate ${investment_amount_frequency}, investment duration is {investment_durations} years'

if __name__ == "__main__":
    # Only runs when api_call.py is executed directly, not on import/ useful in the investment_strategies file
    etfs, start, end = user_input()
    data_dict = portfolio_data_retrieval(etfs, start, end)
    print(data_cleaning(data_dict))
    print(user_investment())