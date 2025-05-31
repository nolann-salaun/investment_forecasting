from flask import Flask, render_template, request
import base64
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive
import matplotlib.pyplot as plt
from portfolio import Portfolio
from optimizedportfolio import OptimizedPortfolio

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

if __name__ == '__main__':
    app.run(debug=True)