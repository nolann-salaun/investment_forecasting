import pandas as pd
import numpy as np
import pandas_ta as ta
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from API_call_V3 import ETFDataHandler, InvestmentInputManager

class ETFAnalyzer:
    def __init__(self, test_mode=True):
        self.data_handler = ETFDataHandler()
        self.input_manager = InvestmentInputManager(test_mode=test_mode)
        self.test_mode = test_mode
    
    def get_analysis_inputs(self):
        """Used to get input for the test mode on test data"""
        if self.test_mode:
            return ["QQQ", "QLD"], "2015-01-01"  
            
        print("\n=== Analysis Parameters ===")
        start_date = input("Enter analysis start date (YYYY-MM-DD): ")
        tickers = input("Enter ETF tickers (comma separated): ").upper().split(',')
        return [t.strip() for t in tickers], start_date

    def fetch_portfolio_data(self):
        """Alternative method that uses the investment parameters from data_fetcher"""
        initial, monthly, start, duration = self.input_manager.get_investment_parameters()
        etf_list, start, end = self.input_manager.get_etf_allocation(start, duration)
        tickers = [etf[0] for etf in etf_list]  # Extract just the ticker symbols
        return self.fetch_data(tickers, start)

    def fetch_data(self, tickers, start_date):
        """Universal data fetcher that works with both standalone and portfolio data"""
        today = pd.Timestamp.today().normalize()
        all_data = []
        
        for ticker in tickers:
            try:
                df = self.data_handler.fetch_historical_data(ticker, start_date, today)
                if not df.empty:
                    df['ETF'] = ticker
                    all_data.append(df)
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
        
        return pd.concat(all_data) if all_data else pd.DataFrame()

    def apply_to_etfs(self, df, func):
        """Apply a function to each ETF group in the DataFrame"""
        results = []
        for ticker, group in df.groupby('ETF'):
            result = func(group.copy(), ticker)
            results.append(result)
        return pd.concat(results).sort_index()

    def calculate_ema_regression(self, df, ticker):
        """Calculate EMA regression for a single ETF"""
        df.ta.ema(close='Close', length=10, append=True)
        df = df.dropna(subset=['EMA_10'])
        
        if df.empty:
            return pd.DataFrame()
            
        X_train, X_test, y_train, y_test = train_test_split(
            df[['Close']], df['EMA_10'], test_size=0.3, random_state=42
        )
        
        model = LinearRegression()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        results = pd.DataFrame({
            'ETF': ticker,
            'Date': X_test.index,
            'Actual_EMA_10': y_test,
            'Predicted_EMA_10': y_pred,
            'Close': X_test['Close'],
            'R²': r2_score(y_test, y_pred),
            'MAE': mean_absolute_error(y_test, y_pred),
            'intercept': model.intercept_,
            'slope': model.coef_[0]
        }).set_index('Date')
        
        return results

    def plot_results(self, results_df, plot_type='regression'):
        for etf, group in results_df.groupby('ETF'):
            if plot_type == 'regression':
                self._plot_regression_line(group, etf)
            elif plot_type == 'timeseries':
                self._plot_time_series(group, etf)

    def _plot_regression_line(self, df, etf):
        """Helper method to plot regression line"""
        plt.figure(figsize=(10, 6))
        plt.scatter(df['Close'], df['Actual_EMA_10'], alpha=0.6)
        x_line = np.array([df['Close'].min(), df['Close'].max()])
        y_line = df['intercept'].iloc[0] + df['slope'].iloc[0] * x_line
        plt.plot(x_line, y_line, 'r-')
        plt.title(f"{etf} EMA Regression")
        plt.show()

    def _plot_time_series(self, df, etf):
        """Helper method to plot time series"""
        plt.figure(figsize=(14, 7))
        plt.plot(df.index, df['Actual_EMA_10'], label='Actual')
        plt.plot(df.index, df['Predicted_EMA_10'], label='Predicted')
        plt.title(f"{etf} EMA Time Series")
        plt.legend()
        plt.show()

    def analyze_portfolio(self, portfolio_data=None):

        if portfolio_data is None:
            if self.test_mode:
                tickers, start_date = self.get_analysis_inputs()
                data = self.fetch_data(tickers, start_date)
            else:
                use_portfolio = input("Do you want to input all the information about your investment ? (y/n): ").lower() == 'y'
                data = self.fetch_portfolio_data() if use_portfolio else self.fetch_data(*self.get_analysis_inputs())
        else:
            data = portfolio_data

        if not data.empty:
            results = self.apply_to_etfs(data, self.calculate_ema_regression)
            self.generate_reports(results)
            self.plot_results(results, plot_type='regression')
            self.plot_results(results, plot_type='timeseries')
            return results
        return pd.DataFrame()

    def generate_reports(self, results_df):
        """Enhanced reporting with portfolio context"""
        print("\n=== Analysis Report ===")
        print(f"Period: {results_df.index.min().date()} to {results_df.index.max().date()}")
        
        for etf, group in results_df.groupby('ETF'):
            print(f"\nETF: {etf}")
            print(f"R²: {group['R²'].mean():.4f}")
            print(f"Regression Equation: EMA_10 = {group['intercept'].iloc[0]:.2f} + {group['slope'].iloc[0]:.2f}*Close")
            print(results_df[results_df['ETF'] == etf])

if __name__ == "__main__":
    analyzer = ETFAnalyzer(test_mode=False)
    portfolio_results = analyzer.analyze_portfolio()
