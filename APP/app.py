from flask import Flask, render_template, request
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive
import matplotlib.pyplot as plt
from portfolio import Portfolio
from optimizedportfolio import OptimizedPortfolio
import numpy as np
from etfanalyzer import ETFAnalyzer

app = Flask(__name__)


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
        
        return render_template('index.html', results=results)
    
    return render_template('index.html')

@app.route('/analyze', methods=['GET', 'POST'])
def analyze_etfs():
    if request.method == 'POST':
        # Get form data
        tickers = request.form['tickers'].upper().split(',')
        tickers = [t.strip() for t in tickers]
        start_date = request.form['start_date']
        
        # Perform analysis
        analyzer = ETFAnalyzer()
        data = analyzer.get_data(tickers, start_date)
        
        if data.empty:
            return "Error: No data found for the given ETFs and date range", 400
        
        results = analyzer.apply_to_etfs(data, analyzer.calculate_ema_regression)
        
        # Generate plots
        plots = []
        
        # Regression plots
        for etf, group in results.groupby('ETF'):
            fig = plt.figure(figsize=(10, 6))
            plt.scatter(group['Close'], group['Actual_EMA_10'], alpha=0.6, label='Actual EMA_10')
            intercept = group['intercept'].iloc[0]
            slope = group['slope'].iloc[0]
            x_line = np.array([group['Close'].min(), group['Close'].max()])
            y_line = intercept + slope * x_line
            plt.plot(x_line, y_line, 'r-', label='Regression Line')
            eqn = f"EMA_10 = {slope:.2f}*Close + {intercept:.2f}"
            plt.text(0.05, 0.95, eqn, transform=plt.gca().transAxes, fontsize=11, 
                    verticalalignment='top', bbox=dict(facecolor='white', alpha=0.7))
            plt.legend()
            plt.title(f"{etf} EMA Regression")
            plt.xlabel('Close Price')
            plt.ylabel('EMA_10 Price')
            plt.tight_layout()
            plots.append(fig_to_base64(fig))
            plt.close(fig)
        
        # Time series plots
        for etf, group in results.groupby('ETF'):
            fig = plt.figure(figsize=(14, 7))
            plt.plot(group.index, group['Actual_EMA_10'], label='Actual')
            plt.plot(group.index, group['Predicted_EMA_10'], label='Predicted')
            plt.title(f"{etf} EMA Time Series")
            plt.xlabel('Date')
            plt.ylabel('EMA_10 Price')
            plt.legend()
            plt.tight_layout()
            plots.append(fig_to_base64(fig))
            plt.close(fig)
        
        # Prepare metrics for display
        metrics = []
        for etf, group in results.groupby('ETF'):
            metrics.append({
                'ticker': etf,
                'r2': group['R²'].mean(),
                'mae': group['MAE'].mean(),
                'equation': f"EMA_10 = {group['slope'].iloc[0]:.2f}*Close + {group['intercept'].iloc[0]:.2f}"
            })
        
        return render_template('analyze.html', 
                             plots=plots, 
                             metrics=metrics,
                             tickers=", ".join(tickers),
                             start_date=start_date)
    
    return render_template('analyze.html')

if __name__ == '__main__':
    app.run(debug=True)