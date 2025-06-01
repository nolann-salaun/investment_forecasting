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
        """Used to get input from the user to get thee data"""
        if self.test_mode:
            return ["QQQ", "QLD"], "2015-01-01"  
            
        print("\n=== Analysis Parameters ===")
        start_date = input("Enter analysis start date (YYYY-MM-DD): ")
        tickers = input("Enter ETF tickers (comma separated): ").upper().split(',')
        return [t.strip() for t in tickers], start_date

    def get_data(self, tickers, start_date):
        """Get the data for the ETFs from the API based on the user inputs"""
        today = pd.Timestamp.today().normalize() # getting today's date
        all_data = []

        for ticker in tickers: # fetching all historical data for each ETF(ticker) mentioned by the user
            try:
                df = self.data_handler.fetch_historical_data(ticker, start_date, today)
                if not df.empty:
                    df['ETF'] = ticker
                    all_data.append(df)
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
        
        return pd.concat(all_data) if all_data else pd.DataFrame()

    def apply_to_etfs(self, df, func):
        """Merges DataFrame of the various ETFs"""
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
        # Split the data into training and testing sets by arbitrarily choosing 30% for testing, we could have chosen other methods (K-fold...)
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
        '''Execution of the plots based on the ETFs'''
        for etf, group in results_df.groupby('ETF'):
            if plot_type == 'regression':
                self.plot_regression_line(group, etf)
            elif plot_type == 'timeseries':
                self.plot_time_series(group, etf)

    def plot_regression_line(self, df, etf):
        """ Plot regression line against the actual values with equation."""
        plt.figure(figsize=(10, 6))
        plt.scatter(df['Close'], df['Actual_EMA_10'], alpha=0.6, label='Actual EMA_10')
        intercept = df['intercept'].iloc[0]
        slope = df['slope'].iloc[0]
        x_line = np.array([df['Close'].min(), df['Close'].max()])
        y_line = intercept + slope * x_line
        plt.plot(x_line, y_line, 'r-', label='Regression Line')
        eqn = f"regression line = {slope:.2f}X + {intercept:.2f} "
        plt.text(0.05, 0.95, eqn, transform=plt.gca().transAxes, fontsize=11, verticalalignment='top',
                 bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))
        plt.legend()
        plt.title(f"{etf} EMA Regression")
        plt.xlabel('Close Price')
        plt.ylabel('Close Price')
        plt.tight_layout()
        plt.show()

    def plot_time_series(self, df, etf):
        """Plot time series with the predicted EMA10 results on past results."""
        plt.figure(figsize=(14, 7))
        plt.plot(df.index, df['Actual_EMA_10'], label='Actual')
        plt.plot(df.index, df['Predicted_EMA_10'], label='Predicted')
        plt.title(f"{etf} EMA Time Series")
        plt.xlabel('Date')
        plt.ylabel('EMA_10 Price')
        plt.legend()
        plt.tight_layout()
        plt.show()


    def analyze_portfolio(self, portfolio_data=None):
        '''Fetch all previous functions to get the data, do the linear regression and plots'''
        if portfolio_data is None:
            if self.test_mode:
                tickers, start_date = self.get_analysis_inputs()
                data = self.get_data(tickers, start_date)
            else:
                tickers, start_date = self.get_analysis_inputs()
                data = self.get_data(tickers, start_date)
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
        """Display key metrics for the analysis of the regression"""
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
