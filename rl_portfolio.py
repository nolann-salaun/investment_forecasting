import yfinance as yf
import pandas as pd
from datetime import datetime
import pandas_ta as ta
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import numpy as np

# Test on data 
TEST_MODE = True  
TEST_START_DATE = "2015-01-01"
TEST_ETFS = ["QQQ", "QLD", "R2US.L"]

def get_user_inputs():
    if TEST_MODE:
        print("Test data")
        start_date = TEST_START_DATE
        etfs = TEST_ETFS
    else:
        start_date = input("Enter start date (YYYY-MM-DD): ")
        etfs = input("Enter ETF tickers separated by commas (e.g. QQQ,QLD,R2US.L): ").split(",")
        etfs = [etf.strip().upper() for etf in etfs]
    return pd.to_datetime(start_date), etfs

def fetch_etf_data(etfs, start_date):
    today = pd.Timestamp.today().normalize()
    all_data = []
    for etf in etfs:
        try:
            ticker = yf.Ticker(etf)
            df = ticker.history(
                start=start_date,
                end=today + pd.Timedelta(days=1),  
                auto_adjust=True,
                actions=True
            )
            if df.empty:
                print(f"No data found for {etf}")
                continue
            df['ETF'] = etf
            all_data.append(df)
        except Exception as e:
            print(f"Error fetching data for {etf}: {e}")
            continue
    if all_data:
        for i in range(len(all_data)):
            all_data[i].index = pd.to_datetime(all_data[i].index)
            all_data[i].index = all_data[i].index.tz_localize(None)
        result = pd.concat(all_data)
        return result
    else:
        print("No data collected for any ETF.")
        return pd.DataFrame()

def apply_to_each_etf(df, func, *args, **kwargs):
    # Group each ETF in the DataFrame
    results = []
    # Group by the ETF column( corresponding to the ticker entered by the user)
    for ticker, group in df.groupby('ETF'):
        result = func(group, ticker, *args, **kwargs)
        results.append(result)
    combined = pd.concat(results)
    combined = combined.reset_index().rename(columns={'index': 'Date'})
    combined = combined.sort_values(['ETF', 'Date'])
    combined = combined.set_index('Date')
    return combined

''' Linear Regression to estimate the future closing price of each ETF based on its 10-day EMA
 We have choosen to use a 10-day estimated average (EMA) as our variable on which we will be running the regression model in order to 
 avoid the noise of daily volatility especially during the "bear" timeperiod or following a particular event.
'''

def linear_regression(df, ticker):
    df = df.copy()
    # Used the library pandas_ta to estimate the 10-day EMA
    df.ta.ema(close='Close', length=10, append=True)
    df = df.dropna(subset=['EMA_10'])
    if df.empty:
        print(f"No data for regression for {ticker}")
        return pd.DataFrame()
    
    # Basic preparation for the linear regression model, we choose arbitrary of a 30% of the data for testing, we also could have choose a different number or different technqiues (K-fold...)
    X_train, X_test, y_train, y_test = train_test_split(df[['Close']], df['EMA_10'], test_size=0.3, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    # Results of the regression model are stored in a DataFrame
    results_df = pd.DataFrame({
        'ETF': ticker,
        'Date': X_test.index,
        'Actual_EMA_10': y_test,
        'Predicted_EMA_10': y_pred,
        'Close': X_test['Close'],
        'R²': r2_score(y_test, y_pred),
        'Mean_Absolute_Error': mean_absolute_error(y_test, y_pred),
        'Mean_Squared_Error': mean_squared_error(y_test, y_pred),
        'intercept': model.intercept_,
        'slope': model.coef_[0]
    })
    results_df.set_index('Date', inplace=True)
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    print(f"\nETF: {ticker}; R²: {r2:.4f}; MAE: {mae:.4f}; MSE: {mse:.4f}")
    # Regression equation of the style y = ax + b
    print(f"Regression equation: EMA_10 = {model.intercept_:.4f} + {model.coef_[0]:.4f} * Close")

    # We have choosen to predict the data for next year (starting from today's date collected with pandas)
    last_date = df.index.max()
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=365, freq='B')  
    last_close = df['Close'].iloc[-1]
    future_close = pd.DataFrame({'Close': [last_close]*len(future_dates)}, index=future_dates)
    future_pred = model.predict(future_close[['Close']])
    future_df = pd.DataFrame({
        'ETF': ticker,
        'Actual_EMA_10': [None]*len(future_dates),
        'Predicted_EMA_10': future_pred,
        'Close': last_close,
        'R²': [None]*len(future_dates),
        'Mean_Absolute_Error': [None]*len(future_dates),
        'Mean_Squared_Error': [None]*len(future_dates),
        'intercept': model.intercept_,
        'slope': model.coef_[0]
    }, index=future_dates)
    
    # Ensure both DataFrames have the same columns and dtypes
    future_df = future_df.reindex(columns=results_df.columns)
    future_df = future_df.where(pd.notnull(future_df), np.nan)
    results_df = results_df.where(pd.notnull(results_df), np.nan)

    # Drop columns that are all-NA in both DataFrames
    all_na_cols = [col for col in results_df.columns if results_df[col].isna().all() and future_df[col].isna().all()]
    results_df = results_df.drop(columns=all_na_cols)
    future_df = future_df.drop(columns=all_na_cols)
    combined = pd.concat([results_df, future_df])
    combined = combined.sort_index()
    return combined

def plot_actual_vs_regression_line(df, etfs):
    """
    Plotting the regression line (it's intercept and slope format) of predicted EMA_10 against the actual Close price for each ETF (in a scatter plot).
    """
    for etf in etfs:
        etf_df = df[df['ETF'] == etf]
        historical_data = etf_df[etf_df['Actual_EMA_10'].notna()]
        if historical_data.empty:
            print(f"No historical data to plot for {etf}")
            continue

        intercept = historical_data['intercept'].iloc[0]
        slope = historical_data['slope'].iloc[0]
        r2 = historical_data['R²'].iloc[0] if 'R²' in historical_data.columns else 0
        min_close = historical_data['Close'].min()
        max_close = historical_data['Close'].max()
        x_line = np.array([min_close, max_close])
        y_line = intercept + slope * x_line
        plt.figure(figsize=(10, 6))
        plt.scatter(historical_data['Close'], historical_data['Actual_EMA_10'], color='blue', alpha=0.6, label='Actual EMA_10')
        plt.plot(x_line, y_line, color='red', linewidth=2, label=f'Linear Regression Line: y={intercept:.2f}+{slope:.2f}x')
        plt.title(f"{etf} EMA_10 vs Close with Linear Regression\nRegression: y = {intercept:.2f} + {slope:.2f}x (R²={r2:.2f})")
        plt.xlabel('Close Price', fontsize=12)
        plt.ylabel('EMA_10 Value', fontsize=12)
        plt.legend(loc='upper left', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

def plot_actual_vs_predicted_timeseries(df, etfs):
    """
    Plots the actual EMA_10 data against the predicted EMA_10 as a time series graph for each ETF.
    """
    for etf in etfs:
        etf_df = df[df['ETF'] == etf]
        plot_df = etf_df.dropna(subset=['Actual_EMA_10', 'Predicted_EMA_10'])
        if plot_df.empty:
            print(f"No data to plot for {etf}")
            continue

        plt.figure(figsize=(14, 7))
        plt.plot(plot_df.index, plot_df['Actual_EMA_10'], color='blue', linewidth=1.5, label='Actual EMA_10')
        plt.plot(plot_df.index, plot_df['Predicted_EMA_10'], color='red', linewidth=1.5, linestyle='--', label='Predicted EMA_10')
        plt.title(f"{etf} - Actual vs Predicted EMA_10 (Time Series)", fontsize=14)
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('EMA_10 Value', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(loc='upper left', fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

def main():
    start_date, etfs = get_user_inputs()
    df = fetch_etf_data(etfs, start_date)
    if not df.empty:
        regression_results = apply_to_each_etf(df, linear_regression)
        print("\nRegression Results between actual prices and predicted close prices")
        print(regression_results)
        plot_actual_vs_regression_line(regression_results, etfs)
        plot_actual_vs_predicted_timeseries(regression_results, etfs)

if __name__ == "__main__":
    main()