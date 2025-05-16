import pandas as pd

#Scraping data from WikiPedia
def get_livret_a_rates():
    url = "https://fr.wikipedia.org/wiki/Livret_A"
    tables = pd.read_html(url)
    df = tables[1]
    df.columns = ["Date", "Taux"]

    #Data cleaning to get year and rate only
    df["Taux"] = df["Taux"].str.extract(r"(\d{1,2},\d{1,2})")[0]
    df["Taux"] = df["Taux"].str.replace(",", ".").astype(float)
    df["Date"] = df["Date"].str.extract(r"(\d{4})").astype(int)
    return df


df_wiki = get_livret_a_rates()
print(df_wiki)