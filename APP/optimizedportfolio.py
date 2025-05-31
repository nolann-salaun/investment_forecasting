from portfolio import Portfolio
import matplotlib.pyplot as plt

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
