import pandas as pd
from pandas.tseries.offsets import BDay
import yfinance as yf

class InvestmentInputManager:
    def __init__(self, test_mode=False, test_data=None, test_etfs=None):
        self.test_mode = test_mode
        self.test_data = test_data
        self.test_etfs = test_etfs
    
    def get_numeric_input(self, prompt, min_val=0):
        while True:
            try:
                value = float(input(prompt))
                if value >= min_val:
                    return value
                print(f"Please enter a number ≥ {min_val}")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def get_investment_parameters(self):
        if self.test_mode and self.test_data:
            return self.test_data["initial_amount"], self.test_data["monthly_amount"], self.test_data["start_date"], self.test_data["duration"]
            
        duration = int(self.get_numeric_input("Enter investment duration (years): ", 1))
        start_date = input("Enter start date (YYYY-MM-DD): ")
        initial_amount = self.get_numeric_input("Enter initial investment amount: ")
        monthly_amount = self.get_numeric_input("Enter monthly investment amount: ")
        
        return initial_amount, monthly_amount, start_date, duration

    def get_etf_allocation(self, start_date, duration):
        if self.test_mode and self.test_etfs:
            etf_list = self.test_etfs
        else:
            etf_list = []
            etf_count = int(self.get_numeric_input("How many ETFs? ", 1))
            
            for i in range(etf_count):
                ticker = input(f"ETF ticker #{i+1}: ").upper()
                proportion = self.get_numeric_input(f"Proportion for {ticker} (0-1): ")
                while proportion < 0 or proportion > 1:
                    print("Proportion must be 0-1")
                    proportion = self.get_numeric_input(f"Proportion for {ticker} (0-1): ")
                etf_list.append((ticker, proportion))
        
        if sum(p for _, p in etf_list) != 1:
            print("Proportions must sum to 1. Please re-enter.")
            return self.get_etf_allocation(start_date, duration)
            
        start_date = pd.to_datetime(start_date)
        end_date = start_date + pd.DateOffset(years=duration)
        
        return etf_list, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


class ETFDataHandler:
    def __init__(self):
        pass
        
    def get_etf_info(self, ticker):
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        return {
            'fees': info.get('netExpenseRatio'),
            'ticker': info.get('symbol', ticker)
        }
    
    def fetch_historical_data(self, ticker, start_date, end_date):
        ticker_obj = yf.Ticker(ticker)
        start_date = pd.to_datetime(start_date) - BDay(1)
        return ticker_obj.history(start=start_date, end=end_date)
    
    def process_portfolio_data(self, etf_list, start_date, end_date):
        data_dict = {}
        for ticker, proportion in etf_list:
            etf_info = self.get_etf_info(ticker)
            data = self.fetch_historical_data(ticker, start_date, end_date)
            data['fees'] = etf_info['fees']
            data['ticker'] = etf_info['ticker']
            data['allocation'] = proportion
            data_dict[(ticker, proportion)] = data
        return data_dict
    
    def clean_data(self, data_dict):
        cleaned = [df.dropna().round(2) for df in data_dict.values()]
        return pd.concat(cleaned) if cleaned else pd.DataFrame()


if __name__ == "__main__":
    input_manager = InvestmentInputManager()
    data_handler = ETFDataHandler()
    
    initial, monthly, start, duration = input_manager.get_investment_parameters()
    etfs, start, end = input_manager.get_etf_allocation(start, duration)
    
    raw_data = data_handler.process_portfolio_data(etfs, start, end)
    clean_data = data_handler.clean_data(raw_data)