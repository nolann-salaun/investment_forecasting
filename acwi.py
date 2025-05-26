import pandas as pd
import matplotlib.pyplot as plt
import api_call_V2 as api
import metrics_obj as mo

def get_acwi_data(investment_start_date, end_date):
    """Retrieve and prepare ACWI data as the reference index for comparison"""
    acwi_ticker = "IMIE.PA"
    acwi_allocation = 1.0
    acwi_etf_list = [(acwi_ticker, acwi_allocation)]
    
    etf_manager = api.etf_data_retrieval()
    acwi_data_dict = etf_manager.portfolio_data_retrieval(acwi_etf_list, investment_start_date, end_date)
    df_acwi = etf_manager.data_cleaning(acwi_data_dict)
    
    acwi_portfolio = mo.Portfolio()
    acwi_portfolio.df_etf = df_acwi
    acwi_portfolio.df_etf['previous_day_price_closure'] = acwi_portfolio.df_etf['Close'].shift(1)
    acwi_portfolio.df_etf = acwi_portfolio.df_etf.iloc[1:]  
    return acwi_portfolio.df_etf

if __name__ == "__main__":
    (initial_amount, monthly_amount, investment_start_date, 
     investment_durations, etfs, end_date, df_clean) = api.main_api_call()
    
    df_acwi = get_acwi_data(investment_start_date, end_date)
    print(df_acwi)