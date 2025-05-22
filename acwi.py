import yfinance as yf
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import api_call as api

def get_acwi_data(start, end, ticker="IMIE.PA"):
    # Retrieve data for the ACWI ETF
    acwi_data = api.portfolio_data_retrieval([ticker], start, end)
    acwi_df = api.data_cleaning(acwi_data)
    return acwi_df

df_acwi = get_acwi_data(start=start, end=end)
print(df_acwi)

'''
months = df_etf.index.to_series().dt.to_period('M').unique()
for month in months:
    first_day = df_etf[df_etf.index.to_period('M') == month].index.min()
    if pd.notna(first_day):
        df_etf.at[first_day, 'investment'] = amount_invested_per_month


cash_left = 0
etf_total = 0

first_business_days = df_etf.groupby([df_etf.index.year, df_etf.index.month]).apply(lambda x: x.index.min())
first_business_days = first_business_days.tolist()

for idx in df_etf.index:
    if idx in first_business_days:
        somme = amount_invested_per_month + cash_left
        price = df_etf.at[idx, 'average']  # Assure-toi que la colonne 'average' existe
        etf_bought = int(somme // price)
        invested = etf_bought * price
        cash_left = somme - invested
        etf_total += etf_bought

        df_etf.at[idx, 'investment'] = invested
        df_etf.at[idx, 'somme_a_investir'] = somme
        df_etf.at[idx, 'ETF_count'] = etf_total
    else:
        # Reporter les valeurs du jour précédent
        prev_idx = df_etf.index[df_etf.index.get_loc(idx) - 1]
        df_etf.at[idx, 'ETF_count'] = df_etf.at[prev_idx, 'ETF_count']
        df_etf.at[idx, 'somme_a_investir'] = cash_left



# Créer la colonne cumulée
df_etf['investment_cumulative'] = df_etf['investment'].cumsum()
df_etf['capital_net'] = df_etf['ETF_count'] * df_etf['average'] + df_etf['somme_a_investir']
df_etf['rendement'] = df_etf['capital_net'] - (df_etf['investment_cumulative'] + df_etf['somme_a_investir'])
df_etf['rendement %'] = ((df_etf['rendement'] / (df_etf['investment_cumulative'] + df_etf['somme_a_investir']))*100).round(4)

print(df_etf)

# Regrouper par mois et prendre la dernière valeur du cumul (à la fin de chaque mois)
monthly_cumulative = df_etf['ETF_count'].resample('M').last()

# Tracer la courbe
plt.figure(figsize=(10, 6))
plt.plot(monthly_cumulative.index, monthly_cumulative.values, marker='o', linestyle='-', color='blue')
plt.title(f"Investissement cumulé sur {ticker_symbol} (par mois)")
plt.xlabel("Date")
plt.ylabel("Montant total investi (€)")
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()'''