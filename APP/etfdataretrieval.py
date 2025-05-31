import pandas as pd
from pandas.tseries.offsets import BDay
import yfinance as yf



class ETFDataRetrieval:
    def get_etf_info(self, ticker_symbol):
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        return {'fees': info.get('netExpenseRatio'), 'ticker': info.get('ticker', ticker_symbol)}

    def portfolio_data_retrieval(self, etf_list, investment_start_date, end_date):
        data_dict = {}
        for etf in etf_list:
            etf_info = self.get_etf_info(etf[0])
            ticker_obj = yf.Ticker(etf[0])
            investment_start_date = pd.to_datetime(investment_start_date)
            investment_start_date = investment_start_date - BDay(1)  #used to get the previous_day_price_closure in the metrics_test.py file
            end_date = pd.to_datetime(end_date)
            data = ticker_obj.history(start=investment_start_date, end=end_date)
            data['fees'] = etf_info['fees']
            data['ticker'] = etf_info['ticker']
            data['etf_allocation'] = etf[1]
            data_dict[etf] = data
        return data_dict

    def data_cleaning(self, data_dict):
        cleaned_list = []
        for symbol, data in data_dict.items():
            df_clean = data.copy()
            df_clean = df_clean.dropna()
            if not df_clean.empty:  # Only add if we have data
                df_clean = df_clean.round(2)
                cleaned_list.append(df_clean)

        if cleaned_list:
            df_clean = pd.concat(cleaned_list)
            return df_clean
        return pd.DataFrame()  # Return empty DataFrame if no data
