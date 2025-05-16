import yfinance as yf
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import api_call as api

# Step 1: Get user input for ETFs and date range
etfs, start, end = api.user_input()
# Step 2: Retrieve data for the selected ETFs
data_dict = api.portfolio_data_retrieval(etfs, start, end)  
dtf_etf = api.data_cleaning(data_dict)

dtf_etf['average_h_l'] = (dtf_etf['High'] + dtf_etf['Low']) / 2
dtf_etf['average_o_c'] = (dtf_etf['Open'] + dtf_etf['Close']) / 2
print(dtf_etf)