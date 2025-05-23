import pandas as pd
from pandas.tseries.offsets import BDay
import yfinance as yf


'''
This class is used to collect the user input regarding the investment they want to make
    - Initial investment
    - Frequency
    - Investment duration
    - Starting date
    - Ticker(s)
    - Proportion
'''
class investment_input_manager:
    def __init__(self):
        self.investment_initial_amount = 0.0
        self.investment_amount_frequency = 0.0
        self.investment_start_date = None
        self.investment_durations = 0
        self.etfs = []


    def user_investment(self):
        # Error handling for the user input is required to make sure the integer are positive values
        investment_durations = int(input("Enter the duration of your investment in years: "))
        investment_start_date = input("Enter the start date of your investment (YYYY-MM-DD): ")
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
        return investment_initial_amount, investment_amount_frequency, investment_start_date, investment_durations

    def user_input(self, investment_start_date, investment_durations):
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
            return self.user_input(investment_start_date, investment_durations)
        investment_start_date = pd.to_datetime(investment_start_date, format="%Y-%m-%d")
        end_date = investment_start_date + pd.DateOffset(years=investment_durations)
        return etf_list, investment_start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

'''This class aims to retrieve the ETF information from the yfinance API on a daily basis within the period, and specifically the fees
    - fees
    - Opening, closing, highest and lowest price
    - Volume
    - Dividends
    - Stock Splits
    - Capital Gains
'''
class etf_data_retrieval:
    def get_etf_info(self, ticker_symbol):
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        return {'fees': info.get('netExpenseRatio'), 'ticker': info.get('ticker', ticker_symbol)}

    def portfolio_data_retrieval(self, etf_list, investment_start_date, end_date):
    # Retrieve and print historical data for each ETF in the list.
        data_dict = {}
        for etf in etf_list:
            etf_info = self.get_etf_info(etf[0])
            ticker_obj = yf.Ticker(etf[0])
            investment_start_date = pd.to_datetime(investment_start_date)
            investment_start_date = investment_start_date - BDay(1) #used to get the previous_day_price_closure in the metrics_test.py file
            end_date = pd.to_datetime(end_date)
            data = ticker_obj.history(start=investment_start_date, end=end_date)
            data['fees'] = etf_info['fees']
            data['ticker'] = etf_info['ticker']
            data['etf_allocation'] = etf[1]
            data_dict[etf] = data

        return data_dict

    '''This function is used to clean the data retrieved from the API call and merge the etfs in a single dataframe'''
    def data_cleaning(self, data_dict):
        cleaned_list = []
        for symbol, data in data_dict.items():
            df_clean = data.copy()
            df_clean = df_clean.dropna()
            df_clean = df_clean.round(2)
            cleaned_list.append(df_clean)

        if cleaned_list:
            df_clean = pd.concat(cleaned_list)
        return df_clean

def main_api_call():
    # Only runs when api_call.py is executed directly, not on import/ useful in the investment_strategies file
    test = investment_input_manager() #Create an instance of the class
    etf_test = etf_data_retrieval() #Create an instance of the class
    investment_initial_amount, investment_amount_frequency, investment_start_date, investment_durations = test.user_investment() #Retrieve inputs from user
    etfs, investment_start_date, end_date = test.user_input(investment_start_date,investment_durations) #Retrieve inputs from user
    data_dict = etf_test.portfolio_data_retrieval(etfs, investment_start_date, end_date) #agregate user inputs with yfinance datas
    df_clean = etf_test.data_cleaning(data_dict) #Perform cleaning on final df
    return investment_initial_amount, investment_amount_frequency, investment_start_date, investment_durations, etfs, end_date, df_clean