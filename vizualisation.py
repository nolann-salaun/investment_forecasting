import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import base64
from io import BytesIO
# Configurer le backend non interactif pour Matplotlib
plt.switch_backend('Agg')

class Visualizer:
    def __init__(self, df):
        self.df = df.copy()
        self.df['Date'] = pd.to_datetime(self.df['Date'])
        self.df = self.df.sort_values('Date')
        self.df_portfolio = self.df.drop_duplicates(subset='Date')
        self.plots = {}
        
        # Configuration du style avec Seaborn
        sns.set_theme(style="whitegrid")
        # Créer une palette avec le nombre exact d'ETFs
        self.num_etfs = len(self.df['ticker'].unique())
        self.palette = sns.color_palette("husl", self.num_etfs)
    
    def _fig_to_base64(self, fig):
        """Convertit une figure matplotlib en base64"""
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    
    def plot_etf_prices(self, return_fig=False):
        fig, ax = plt.subplots(figsize=(14, 6))
        sns.lineplot(
            data=self.df, 
            x='Date', 
            y='previous_day_price_closure', 
            hue='ticker',
            palette=self.palette,
            ax=ax
        )
        ax.set_title('Évolution des prix des ETFs (J-1)')
        ax.set_xlabel('Date')
        ax.set_ylabel('Prix')
        ax.legend(title='ETF')
        plt.tight_layout()
        
        if return_fig:
            return fig
        plt.close()
    
    def plot_portfolio_value(self, return_fig=False):
        fig, ax = plt.subplots(figsize=(14, 6))
        sns.lineplot(
            data=self.df_portfolio, 
            x='Date', 
            y='Portfolio_net_worth',
            color=self.palette[0],
            ax=ax
        )
        ax.set_title('Valeur du portefeuille dans le temps')
        ax.set_xlabel('Date')
        ax.set_ylabel('Valeur (€)')
        plt.tight_layout()
        
        if return_fig:
            return fig
        plt.close()
    
    def plot_cumulative_investment(self, return_fig=False):
        fig, ax = plt.subplots(figsize=(14, 6))
        sns.lineplot(
            data=self.df_portfolio, 
            x='Date', 
            y='cumulative_investment',
            color=self.palette[1],
            ax=ax
        )
        ax.set_title('Sommes investies cumulées')
        ax.set_xlabel('Date')
        ax.set_ylabel('Montant investi (€)')
        plt.tight_layout()
        
        if return_fig:
            return fig
        plt.close()
    
    def plot_cagr_distribution(self, cagr_data, return_fig=False):
        """Nouvelle méthode pour visualiser le CAGR"""
        # Filtrer les valeurs négatives
        cagr_data = cagr_data[cagr_data['CAGR'] > 0]
        
        if len(cagr_data) == 0:
            return None  # Aucune donnée positive à afficher
            
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Utiliser un bar plot au lieu d'un pie chart
        sns.barplot(
            x=cagr_data.index,
            y='CAGR',
            data=cagr_data,
            palette=self.palette,
            ax=ax
        )
        ax.set_title('Performance des ETFs (CAGR)')
        ax.set_xlabel('ETF')
        ax.set_ylabel('CAGR (%)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if return_fig:
            return fig
        plt.close()
    
    def plot_all(self, for_flask=False, cagr_data=None):
        """Génère tous les graphiques"""
        if for_flask:
            self.plots['etf_prices'] = self._fig_to_base64(self.plot_etf_prices(return_fig=True))
            self.plots['portfolio_value'] = self._fig_to_base64(self.plot_portfolio_value(return_fig=True))
            self.plots['cumulative_investment'] = self._fig_to_base64(self.plot_cumulative_investment(return_fig=True))
            
            if cagr_data is not None:
                fig = self.plot_cagr_distribution(cagr_data, return_fig=True)
                if fig is not None:
                    self.plots['cagr_distribution'] = self._fig_to_base64(fig)
        else:
            self.plot_etf_prices()
            self.plot_portfolio_value()
            self.plot_cumulative_investment()
            if cagr_data is not None:
                self.plot_cagr_distribution(cagr_data)
    
    def get_plots(self):
        """Retourne les graphiques encodés pour Flask"""
        if not self.plots:
            self.plot_all(for_flask=True)
        return self.plots