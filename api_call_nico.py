import yfinance as yf
from datetime import datetime
import pandas as pd


# Call ticker
ticker_symbol = "QQQ"
ticker = yf.Ticker(ticker_symbol)

# Get data from period 
data = ticker.history(start="2024-01-01", end="2024-12-31")

# Get  Ticker code (symbol) and  ETF name (shortName)
info = ticker.info
symbol = info.get('symbol', ticker_symbol)
short_name = info.get('shortName', '')

# Add symbol and shortName column for each row
data['symbol'] = symbol
data['shortName'] = short_name

# Store data in DataFrame
df_etf = data.copy()

#Cleaning of NA values
df_etf = df_etf.dropna()

#Round up to 2 decimals
df_etf = df_etf.round(2)
print(df_etf)
