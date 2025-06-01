import matplotlib
matplotlib.use('Agg')  # Set the backend to non-interactive
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


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
    
    def plot_pnl_boxplot(self, for_flask=False):
        df = self.data.copy()
        df['Year'] = pd.to_datetime(df['Date']).dt.year

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(data=df, x='Year', y='Portfolio_PnL_%', ax=ax)

        ax.set_title('Distribution of Portfolio PnL Percentage by Year')
        ax.set_xlabel('Year')
        ax.set_ylabel('PnL (%)')
        ax.grid(True)

        if for_flask:
            return fig
        plt.show()


    def plot_all(self, for_flask=False, cagr_data=None):
        plots = []
        plots.append(self.plot_portfolio_value(for_flask=for_flask))
        plots.append(self.plot_pnl_percentage(for_flask=for_flask))
        plots.append(self.plot_pnl_boxplot(for_flask=for_flask))
        return plots
    
    def get_plots(self, cagr_data=None):
        return self.plot_all(for_flask=True, cagr_data=cagr_data)
  