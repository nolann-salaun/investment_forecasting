from flask import Flask, render_template_string, request
import pandas as pd
from pandas.tseries.offsets import BDay
import yfinance as yf
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

# Template HTML remains the same as in your original code
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Investment Simulation</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input, select { width: 100%; padding: 8px; box-sizing: border-box; }
        button { background: #4CAF50; color: white; padding: 10px 15px; border: none; cursor: pointer; margin: 5px; }
        .results { margin-top: 30px; }
        .metrics { display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 30px; }
        .metric-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; min-width: 200px; }
        .comparison-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }
        .comparison-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .plots { display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; }
        .plot img { max-width: 100%; height: auto; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .better { color: green; font-weight: bold; }
        .worse { color: red; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Investment Parameters</h1>
    <form method="POST">
        <div class="form-group">
            <label for="initial_amount">Initial Investment Amount ($):</label>
            <input type="number" step="0.01" min="0" name="initial_amount" value="{{ request.form.initial_amount if request.form.initial_amount }}" required>
        </div>
        
        <div class="form-group">
            <label for="monthly_amount">Periodic Investment Amount ($):</label>
            <input type="number" step="0.01" min="0" name="monthly_amount" value="{{ request.form.monthly_amount if request.form.monthly_amount }}" required>
        </div>
        
        <div class="form-group">
            <label for="start_date">Start Date:</label>
            <input type="date" name="start_date" value="{{ request.form.start_date if request.form.start_date }}" required>
        </div>
        
        <div class="form-group">
            <label for="duration">Investment Duration (years):</label>
            <input type="number" min="1" name="duration" value="{{ request.form.duration if request.form.duration }}" required>
        </div>
        
        <div class="form-group">
            <label for="investment_frequency">Investment Frequency:</label>
            <select name="investment_frequency" required>
                <option value="M" {% if request.form.investment_frequency == 'M' %}selected{% endif %}>Monthly</option>
                <option value="Q" {% if request.form.investment_frequency == 'Q' %}selected{% endif %}>Quarterly</option>
                <option value="6M" {% if request.form.investment_frequency == '6M' %}selected{% endif %}>Semi-Annually</option>
                <option value="Y" {% if request.form.investment_frequency == 'Y' %}selected{% endif %}>Annually</option>
            </select>
        </div>

        <div id="etfs-container">
            <h3>ETF Allocation</h3>
            {% for i in range(1, 10) %}
                {% if request.form.get('etf_ticker_' ~ i) %}
                    <div class="etf-group">
                        <label>ETF {{ i }}:</label>
                        <input type="text" name="etf_ticker_{{ i }}" placeholder="Ticker symbol" value="{{ request.form.get('etf_ticker_' ~ i) }}" required>
                        <input type="number" step="0.01" min="0" max="1" name="etf_proportion_{{ i }}" placeholder="Proportion (0-1)" value="{{ request.form.get('etf_proportion_' ~ i) }}" required>
                    </div>
                {% elif loop.first %}
                    <div class="etf-group">
                        <label>ETF 1:</label>
                        <input type="text" name="etf_ticker_1" placeholder="Ticker symbol" required>
                        <input type="number" step="0.01" min="0" max="1" name="etf_proportion_1" placeholder="Proportion (0-1)" required>
                    </div>
                {% endif %}
            {% endfor %}
        </div>
        
        <button type="button" onclick="addEtfField()">Add Another ETF</button>
        <button type="submit">Simulate Portfolio</button>
    </form>
    {% if results %}
    <div class="results">
        <h1>Simulation Results</h1>
        
        <div class="metrics">
            <div class="metric-card">
                <h3>Sharpe Ratio</h3>
                <p>{{ results.sharpe_ratio }}</p>
            </div>
            <div class="metric-card">
                <h3>Global CAGR</h3>
                <p>{{ results.global_cagr }}%</p>
            </div>
        </div>

        <div class="comparison-metrics">
            <div class="comparison-card">
                <h3>ACWI Benchmark Comparison</h3>
                <p>CAGR: {{ results.acwi_cagr }}% 
                    {% if results.global_cagr > results.acwi_cagr %}
                        <span class="better">(Better)</span>
                    {% else %}
                        <span class="worse">(Worse)</span>
                    {% endif %}
                </p>
                <p>Sharpe Ratio: {{ results.acwi_sharpe }}
                    {% if results.sharpe_ratio > results.acwi_sharpe %}
                        <span class="better">(Better)</span>
                    {% else %}
                        <span class="worse">(Worse)</span>
                    {% endif %}
                </p>
            </div>
        </div>

        <!-- Add this section after the ACWI comparison -->
        <div class="comparison-card">
            <h3>Top 5 ETFs Portfolio Comparison</h3>
            <p>Optimized Portfolio Composition: {{ results.optimized_composition }}</p>
            <p>CAGR: {{ results.optimized_cagr }}% 
                {% if results.global_cagr > results.optimized_cagr %}
                    <span class="better">(Better)</span>
                {% else %}
                    <span class="worse">(Worse)</span>
                {% endif %}
            </p>
            <p>Sharpe Ratio: {{ results.optimized_sharpe }}
                {% if results.sharpe_ratio > results.optimized_sharpe %}
                    <span class="better">(Better)</span>
                {% else %}
                    <span class="worse">(Worse)</span>
                {% endif %}
            </p>
        </div>

        <h2>Detailed Performance</h2>
        <h3>CAGR by ETF</h3>
        {{ results.cagr_table|safe }}
        
        <h2>Visualizations</h2>
        <div class="plots">
            {% for plot in results.plots %}
            <div class="plot">
                <img src="data:image/png;base64,{{ plot }}" alt="Financial plot">
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <script>
    function addEtfField() {
        const container = document.getElementById('etfs-container');
        const etfGroups = container.querySelectorAll('.etf-group');
        const nextIndex = etfGroups.length + 1;
        
        // Only allow up to 10 ETFs
        if (nextIndex > 10) {
            alert('Maximum of 10 ETFs allowed');
            return;
        }
        
        const newGroup = document.createElement('div');
        newGroup.className = 'etf-group';
        newGroup.innerHTML = `
            <label>ETF ${nextIndex}:</label>
            <input type="text" name="etf_ticker_${nextIndex}" placeholder="Ticker symbol" required>
            <input type="number" step="0.01" min="0" max="1" name="etf_proportion_${nextIndex}" placeholder="Proportion (0-1)" required>
        `;
        
        container.appendChild(newGroup);
    }
    </script>
    <script>
    // Format all numeric values as dollars in tables
    document.addEventListener('DOMContentLoaded', function() {
        // Format all cells with class 'dollar'
        document.querySelectorAll('.dollar').forEach(cell => {
            const value = parseFloat(cell.textContent);
            if (!isNaN(value)) {
                cell.textContent = value.toLocaleString('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
        });
        
        // Format specific columns in tables (alternative approach)
        document.querySelectorAll('td:nth-child(2), td:nth-child(3)').forEach(cell => {
            const value = parseFloat(cell.textContent);
            if (!isNaN(value)) {
                cell.textContent = value.toLocaleString('en-US', {
                    style: 'currency',
                    currency: 'USD'
                });
            }
        });
    });
    </script>
</body>
</html>
"""

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

class Visualizer:
    def __init__(self, data, acwi_data=None):
        self.data = data
        self.acwi_data = acwi_data
    
    def plot_portfolio_value(self, for_flask=False):
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Get portfolio value and cumulative investment
        portfolio_data = self.data.groupby('Date').agg({
            'Portfolio_net_worth': 'first',
            'cumulative_investment': 'first'
        })
        
        # Plot both lines
        portfolio_data['Portfolio_net_worth'].plot(ax=ax, label='Your Portfolio Value')
        portfolio_data['cumulative_investment'].plot(ax=ax, label='Cumulative Investment', linestyle='--')
        
       
        
        ax.set_title('Portfolio Value vs Benchmark Over Time')
        ax.set_ylabel('Value ($)')
        ax.grid(True)
        ax.legend()
        
        if for_flask:
            return fig
        plt.show()
    
    def plot_pnl_percentage(self, for_flask=False):
        fig, ax = plt.subplots(figsize=(10, 6))
        pnl = self.data.groupby('Date')['Portfolio_PnL_%'].first()
        pnl.plot(ax=ax, label='Your Portfolio')
        
        # Add ACWI comparison if available
        if self.acwi_data is not None:
            acwi_pnl = self.acwi_data.groupby('Date')['Portfolio_PnL_%'].first()
            acwi_pnl.plot(ax=ax, label='ACWI', color='green')
        
        ax.set_title('Portfolio PnL Percentage vs Benchmark')
        ax.set_ylabel('PnL (%)')
        ax.grid(True)
        ax.legend()
        
        if for_flask:
            return fig
        plt.show()
    
    def plot_all(self, for_flask=False, cagr_data=None):
        plots = []
        plots.append(self.plot_portfolio_value(for_flask=for_flask))
        plots.append(self.plot_pnl_percentage(for_flask=for_flask))
        return plots
    
    def get_plots(self, cagr_data=None):
        return self.plot_all(for_flask=True, cagr_data=cagr_data)
    
class Portfolio:
    def __init__(self):
        self.investment_initial_amount = None
        self.investment_monthly_amount = None
        self.investment_start_date = None
        self.investment_durations = None
        self.etfs = None
        self.end_date = None
        self.df_etf = None
        self.visualizer = None
        self.cagr = None
        self.sharpe_ratio = None
        self.volatility = None
        self.investment_frequency = None
    
    def configure_from_input(self, initial_amount, monthly_amount, start_date, duration, etfs, frequency='M'):
        self.investment_initial_amount = initial_amount
        self.investment_monthly_amount = monthly_amount
        self.investment_start_date = pd.to_datetime(start_date)
        self.investment_durations = duration
        self.etfs = etfs
        self.end_date = (self.investment_start_date + pd.DateOffset(years=duration)).strftime("%Y-%m-%d")
        self.investment_frequency = frequency
        
        # Get ETF data
        etf_retriever = ETFDataRetrieval()
        data_dict = etf_retriever.portfolio_data_retrieval(etfs, start_date, self.end_date)
        self.df_etf = etf_retriever.data_cleaning(data_dict)
        self.df_etf['previous_day_price_closure'] = self.df_etf['Close'].shift(1)
        self.df_etf = self.df_etf.iloc[1:].sort_index()
        self.dict_of_dfs = {ticker: group for ticker, group in self.df_etf.groupby('ticker')}

    def apply_periodic_investment(self):
        dict_etf = {}
        
        for ticker, ticker_df in self.dict_of_dfs.items():
            df = ticker_df.copy()
            df.index = pd.to_datetime(df.index)
            df.index = df.index.tz_localize(None)
            start_date = pd.to_datetime(self.investment_start_date)
            df['investment'] = 0.0

            # Initial investment
            if start_date in df.index:
                df.at[start_date, 'investment'] += self.investment_initial_amount * float(df.loc[start_date, 'etf_allocation'])
            else:
                closest = df.index[df.index >= start_date].min()
                if pd.notna(closest):
                    df.at[closest, 'investment'] += self.investment_initial_amount * float(df.loc[closest, 'etf_allocation'])
                    start_date = closest

            # Determine frequency and first investment date
            if self.investment_frequency == 'M':
                freq_offset = pd.DateOffset(months=1)
                period = 'M'
            elif self.investment_frequency == 'Q':
                freq_offset = pd.DateOffset(months=3)
                period = 'Q'
            elif self.investment_frequency == '6M':
                freq_offset = pd.DateOffset(months=6)
                period = '6M'
            elif self.investment_frequency == 'Y':
                freq_offset = pd.DateOffset(years=1)
                period = 'Y'
            
            first_periodic_date = start_date + freq_offset
            
            # Get unique periods based on frequency
            periods = df.index.to_series().dt.to_period(period).unique()
            
            for p in periods:
                period_start = pd.Period(p).start_time
                if period_start >= first_periodic_date:
                    first_day = df[df.index.to_series().dt.to_period(period) == p].index.min()
                    if pd.notna(first_day):
                        df.at[first_day, 'investment'] = self.investment_monthly_amount * float(df.loc[first_day, 'etf_allocation'])

            df = df[df['investment'] != 0.0]
            df['etf_cumulative_investment'] = df['investment'].cumsum()
            dict_etf[ticker] = df
            
        return dict_etf

    def apply_ETF_purchase(self):
        dict_etf = self.apply_periodic_investment()
        
        for ticker, df in dict_etf.items():
            df = df.copy()
            
            df['etf_units_purchased'] = 0
            df['total_etf_units'] = 0
            df['cash'] = 0.0
            df['ETF_net_worth'] = 0.0
            df['ETF_PnL'] = 0.0
            df['ETF_PnL_%'] = 0.0
            df['ticker'] = ticker  
            
            leftover = 0.0
            total_units = 0.0

            for idx in df.index:
                investment = df.at[idx, 'investment'] + leftover
                price = df.at[idx, 'previous_day_price_closure'] * (1 + df.at[idx, 'fees'])                
                
                units_bought = np.floor(investment / price)
                spent = units_bought * price
                leftover = investment - spent
                total_units += units_bought

                df.at[idx, 'etf_units_purchased'] = units_bought
                df.at[idx, 'cash'] = leftover
                df.at[idx, 'total_etf_units'] = total_units
                df.at[idx, 'ETF_net_worth'] = total_units * price + leftover
                df.at[idx, 'ETF_PnL'] = df.at[idx, 'ETF_net_worth'] - df.at[idx, 'etf_cumulative_investment']
                df.at[idx, 'ETF_PnL_%'] = ((df.at[idx, 'ETF_net_worth'] / df.at[idx, 'etf_cumulative_investment'] - 1) * 100).round(2)
            
            dict_etf[ticker] = df
        
        # Merging ETF dataframe and sort per date
        consolidated_df = pd.concat(dict_etf).sort_index().sort_values(['Date', 'ticker'])

        daily_totals_Inv = consolidated_df.groupby('Date')['investment'].sum().reset_index()
        daily_totals_Inv['cumulative_investment'] = daily_totals_Inv['investment'].cumsum()
        consolidated_df = pd.merge(
            consolidated_df,
            daily_totals_Inv[['Date', 'cumulative_investment']],
            on='Date',
            how='left'
        )

        daily_totals_PnL = consolidated_df.groupby('Date')['ETF_PnL'].sum().reset_index()
        daily_totals_PnL['Portfolio_PnL'] = daily_totals_PnL['ETF_PnL']
        consolidated_df = pd.merge(
            consolidated_df,
            daily_totals_PnL[['Date', 'Portfolio_PnL']],
            on='Date',
            how='left'
        )
        
        daily_totals_networth = consolidated_df.groupby('Date')['ETF_net_worth'].sum().reset_index()
        daily_totals_networth['Portfolio_net_worth'] = daily_totals_networth['ETF_net_worth']
        consolidated_df = pd.merge(
            consolidated_df,
            daily_totals_networth[['Date', 'Portfolio_net_worth']],
            on='Date',
            how='left'
        )

        for idx in consolidated_df.index:
            consolidated_df.at[idx, 'Portfolio_PnL_%'] = ((consolidated_df.at[idx, 'Portfolio_net_worth'] / consolidated_df.at[idx, 'cumulative_investment'] - 1) * 100).round(2)

        return consolidated_df
    
    def apply_CAGR_ratio(self):
        df = self.apply_ETF_purchase()
        
        # Collection of last row for each ETF
        cagr = df.groupby('ticker').last()[['ETF_net_worth', 'etf_cumulative_investment']].copy()
        
        # ETF CAGR
        cagr['CAGR'] = (
            (cagr['ETF_net_worth'] / cagr['etf_cumulative_investment']) ** (1 / self.investment_durations) - 1
        ).round(4) * 100
        
        # Total CAGR
        total_net = cagr['ETF_net_worth'].sum()
        total_invest = cagr['etf_cumulative_investment'].sum()

        global_cagr = ((total_net / total_invest) ** (1 / self.investment_durations) - 1) * 100

        total_row = pd.DataFrame({
            'ETF_net_worth': [total_net],
            'etf_cumulative_investment': [total_invest],
            'CAGR': [round(global_cagr, 2)]
        }, index=['TOTAL'])
        
        result = pd.concat([cagr, total_row])[['ETF_net_worth', 'etf_cumulative_investment', 'CAGR']]
        
        return result
    
    def apply_SHARPE_ratio(self):
        df = self.apply_ETF_purchase()
        volatility_df = df.groupby('ticker')['ETF_PnL_%'].std().round(2)
        volatility_df = volatility_df.to_frame(name='volatility')

        global_volatility = df['Portfolio_PnL_%'].std().round(2)
        total_row = pd.DataFrame({
        'volatility': [global_volatility],
        }, index=['TOTAL'])

        volatility_df = pd.concat([volatility_df, total_row])[['volatility']]

        sharpe_ratio = ((df['Portfolio_PnL_%'].iloc[-1] - 2) / volatility_df['volatility'].iloc[-1]).round(2)

        return volatility_df, sharpe_ratio
        
    def calculate_all_metrics(self):
        """Calculate all metrics and prepare visualizations"""
        df_result = self.apply_ETF_purchase()
        self.cagr = self.apply_CAGR_ratio()
        self.volatility, self.sharpe_ratio = self.apply_SHARPE_ratio()
        
        # Calculate ACWI metrics for comparison
        acwi_metrics = self.calculate_acwi_comparison()
        
        self.visualizer = Visualizer(df_result, acwi_data=acwi_metrics['acwi_data'])
        return {    
            "data": df_result,
            "cagr": self.cagr,
            "volatility": self.volatility, #To be removed?
            "sharpe_ratio": self.sharpe_ratio,
            "acwi_cagr": acwi_metrics['acwi_cagr'],
            "acwi_sharpe": acwi_metrics['acwi_sharpe'],
            "acwi_data": acwi_metrics['acwi_data'],
            "plots": self.visualizer.get_plots(cagr_data=self.cagr.iloc[:-1])
        }
    
    def calculate_acwi_comparison(self):
        # Calculate ACWI performance with same investment pattern
        # Create a temporary portfolio with 100% ACWI
        acwi_portfolio = Portfolio()
        acwi_portfolio.configure_from_input(
            self.investment_initial_amount,
            self.investment_monthly_amount,
            self.investment_start_date.strftime("%Y-%m-%d"),
            self.investment_durations,
            [('ACWI', 1.0)]
        )
        
        # Get ACWI data
        acwi_data = acwi_portfolio.apply_ETF_purchase()
        
        # Calculate ACWI CAGR
        acwi_cagr = acwi_portfolio.apply_CAGR_ratio().loc['TOTAL', 'CAGR']
        
        # Calculate ACWI Sharpe ratio
        _, acwi_sharpe = acwi_portfolio.apply_SHARPE_ratio()
        
        return {
            'acwi_data': acwi_data,
            'acwi_cagr': acwi_cagr,
            'acwi_sharpe': acwi_sharpe
        }

class OptimizedPortfolio(Portfolio):
    def __init__(self):
        super().__init__()
        self.etf_categories = {
            'US Large Cap': ['SPY'],          # SPDR S&P 500 ETF (most popular)
            'US Growth': ['QQQ'],             # Invesco QQQ (Nasdaq-100, very popular)
            'US Value': ['VTV'],              # Vanguard Value ETF
            'US Small Cap': ['IWM'],          # iShares Russell 2000 ETF
            'International Developed': ['VEA'], # Vanguard FTSE Developed Markets
            'Emerging Markets': ['VWO'],      # Vanguard FTSE Emerging Markets
            'Sector ETFs': ['XLK'],           # Technology Select Sector SPDR
            'Fixed Income': ['BND'],          # Vanguard Total Bond Market ETF
            'Real Estate': ['VNQ'],           # Vanguard Real Estate ETF
            'Commodities': ['GLD'],           # SPDR Gold Shares
            'Alternative': ['ARKK'],          # ARK Innovation ETF
            'Thematic': ['SOXX'],             # iShares Semiconductor ETF
            'Factor ETFs': ['MTUM'],          # iShares MSCI USA Momentum Factor
            'Dividend': ['SCHD']              # Schwab US Dividend Equity ETF
        }
    
    def calculate_etf_performance(self, initial_amount, monthly_amount, start_date, duration, frequency):
        """Calculate performance of all ETFs in our categories"""
        etf_performance = {}
        
        # Test each ETF individually
        for category, etfs in self.etf_categories.items():
            for etf in etfs:
                try:
                    # Create portfolio with 100% allocation to this ETF
                    temp_portfolio = Portfolio()
                    temp_portfolio.configure_from_input(
                        initial_amount,
                        monthly_amount,
                        start_date,
                        duration,
                        [(etf, 1.0)],
                        frequency
                    )
                    
                    # Get the performance data
                    temp_data = temp_portfolio.apply_ETF_purchase()
                    
                    # Get the final PnL%
                    final_pnl = temp_data['ETF_PnL_%'].iloc[-1]
                    
                    # Store the performance
                    etf_performance[etf] = {
                        'category': category,
                        'final_pnl': final_pnl,
                        'data': temp_data
                    }
                except Exception as e:
                    print(f"Error processing {etf}: {str(e)}")
                    continue
        
        return etf_performance
    
    def get_top_performers(self, etf_performance, top_n=5):
        """Get the top performing ETFs"""
        # Sort by final PnL% in descending order
        sorted_etfs = sorted(
            etf_performance.items(),
            key=lambda x: x[1]['final_pnl'],
            reverse=True
        )
        
        # Take top N
        top_etfs = sorted_etfs[:top_n]
        
        # Calculate equal allocation (1/N for each)
        allocation = 1.0 / len(top_etfs)
        
        # Prepare the optimized portfolio composition
        optimized_composition = [(etf[0], allocation) for etf in top_etfs]
        
        # Get the performance data for each top ETF
        top_performers_data = {etf[0]: etf[1]['data'] for etf in top_etfs}
        
        return optimized_composition, top_performers_data
    
    def create_optimized_portfolio(self, initial_amount, monthly_amount, start_date, duration, frequency):
        """Create an optimized portfolio from top performers"""
        # Calculate performance of all ETFs
        etf_performance = self.calculate_etf_performance(
            initial_amount, monthly_amount, start_date, duration, frequency
        )
        
        # Get top performers
        optimized_composition, top_performers_data = self.get_top_performers(etf_performance)
        
        # Create the optimized portfolio
        self.configure_from_input(
            initial_amount,
            monthly_amount,
            start_date,
            duration,
            optimized_composition,
            frequency
        )
        
        return optimized_composition, top_performers_data
    
    def compare_with_user_portfolio(self, user_portfolio_data):
        """Compare optimized portfolio with user's portfolio"""
        # Get our portfolio data
        optimized_data = self.apply_ETF_purchase()
        
        # Prepare comparison data
        comparison_data = {
            'user': user_portfolio_data.groupby('Date')['Portfolio_PnL_%'].first(),
            'optimized': optimized_data.groupby('Date')['Portfolio_PnL_%'].first()
        }
        
        # Create comparison plot
        fig, ax = plt.subplots(figsize=(10, 6))
        comparison_data['user'].plot(ax=ax, label='Your Portfolio')
        comparison_data['optimized'].plot(ax=ax, label='Optimized Portfolio')
        
        ax.set_title('Portfolio PnL Comparison: Your Portfolio vs Top 5 ETFs')
        ax.set_ylabel('PnL (%)')
        ax.grid(True)
        ax.legend()
        
        return fig

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 encoded image"""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.route('/', methods=['GET', 'POST'])
def investment_form():
    if request.method == 'POST':
        # Get form data
        initial_amount = float(request.form['initial_amount'])
        monthly_amount = float(request.form['monthly_amount'])
        start_date = request.form['start_date']
        duration = int(request.form['duration'])
        frequency = request.form['investment_frequency']
        
        # Get ETFs from form
        etfs = []
        i = 1
        while f'etf_ticker_{i}' in request.form:
            ticker = request.form[f'etf_ticker_{i}']
            proportion = float(request.form[f'etf_proportion_{i}'])
            etfs.append((ticker, proportion))
            i += 1
        
        # Check proportions sum to 1
        total_prop = sum([p for _, p in etfs])
        if abs(total_prop - 1.0) > 0.001:
            return "Error: The sum of proportions must equal 1", 400 
        
        # Calculate metrics for user's portfolio
        portfolio = Portfolio()
        portfolio.configure_from_input(initial_amount, monthly_amount, start_date, duration, etfs, frequency)
        metrics = portfolio.calculate_all_metrics()
        
        # Create and compare with optimized portfolio
        optimized_portfolio = OptimizedPortfolio()
        optimized_composition, _ = optimized_portfolio.create_optimized_portfolio(
            initial_amount, monthly_amount, start_date, duration, frequency
        )
        
        # Generate comparison plot
        comparison_fig = optimized_portfolio.compare_with_user_portfolio(metrics['data'])
        comparison_plot = fig_to_base64(comparison_fig)
        plt.close(comparison_fig)
        
        # Generate plots
        plots = []
        for fig in metrics['plots']:
            plots.append(fig_to_base64(fig))
            plt.close(fig)
        
        # Add comparison plot
        plots.append(comparison_plot)
        
        # Format optimized composition for display
        optimized_display = "\n".join([
            f"{etf[0]} ({etf[1]*100:.1f}%)" for etf in optimized_composition
        ])
             
        # Prepare results
        results = {
            'sharpe_ratio': metrics['sharpe_ratio'],
            'global_cagr': metrics['cagr'].loc['TOTAL', 'CAGR'],
            'acwi_cagr': metrics['acwi_cagr'],
            'acwi_sharpe': metrics['acwi_sharpe'],
            'cagr_table': metrics['cagr'].to_html(classes='data-table', float_format='%.2f'),
            'plots': plots,
            'optimized_composition': optimized_display,
            'optimized_cagr': optimized_portfolio.apply_CAGR_ratio().loc['TOTAL', 'CAGR'],
            'optimized_sharpe': optimized_portfolio.apply_SHARPE_ratio()[1]
        }
        
        return render_template_string(HTML_TEMPLATE, results=results)
    
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True)