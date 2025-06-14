# update_data.py (versão Final)
import yfinance as yf
import pandas as pd
from datetime import datetime
import time
import requests

def get_fii_list():
    return sorted(['BTLG11', 'MXRF11', 'VGIR11', 'HGLG11', 'XPML11', 'KNCR11', 'VISC11','HGRU11', 'KNSC11', 'IRDM11', 'VILG11', 'CPTS11', 'RBRR11', 'MCCI11','XPLG11', 'RECR11', 'BCFF11', 'HGCR11', 'LVBI11', 'DEVA11', 'HGRE11','KNIP11', 'VRTA11', 'PVBI11', 'JSRE11', 'MALL11', 'GGRC11', 'ALZR11','BTCI11', 'BCRI11', 'BRCO11', 'VINO11', 'TORD11', 'RBRP11'])

def get_fii_types():
    return {'BTLG11':'Tijolo','HGLG11':'Tijolo','XPML11':'Tijolo','VISC11':'Tijolo','HGRU11':'Tijolo','VILG11':'Tijolo','XPLG11':'Tijolo','HGRE11':'Tijolo','LVBI11':'Tijolo','PVBI11':'Tijolo','JSRE11':'Tijolo','MALL11':'Tijolo','GGRC11':'Tijolo','ALZR11':'Tijolo','BRCO11':'Tijolo','VINO11':'Tijolo','RBRP11':'Tijolo','MXRF11':'Papel','VGIR11':'Papel','KNCR11':'Papel','KNSC11':'Papel','IRDM11':'Papel','CPTS11':'Papel','RBRR11':'Papel','MCCI11':'Papel','RECR11':'Papel','HGCR11':'Papel','DEVA11':'Papel','KNIP11':'Papel','VRTA11':'Papel','BTCI11':'Papel','BCRI11':'Papel','TORD11':'Papel','BCFF11':'Fundo de Fundos'}

def get_selic_rate():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados/ultimos/1?formato=json"
        response = requests.get(url)
        response.raise_for_status()
        selic_diaria = float(response.json()[0]['valor'])
        selic_anual = (1 + (selic_diaria / 100))**252 - 1
        return selic_anual * 100
    except:
        return 10.5 # Valor de fallback

def collect_all_data():
    all_data, failed_tickers = [], []
    fiis_list, fii_types = get_fii_list(), get_fii_types()
    selic = get_selic_rate()

    print(f"--- INICIANDO COLETA (SELIC de Referência: {selic:.2f}%) ---")
    
    for i, ticker in enumerate(fiis_list):
        print(f"({i+1}/{len(fiis_list)}) Buscando {ticker}...", end='')
        try:
            fii = yf.Ticker(f"{ticker}.SA")
            info = fii.info
            price = info.get('regularMarketPrice', info.get('previousClose', 0.0))
            
            dy_12m = (info.get('trailingAnnualDividendYield', 0.0) * 100) if info.get('trailingAnnualDividendYield') else 0.0
            if dy_12m == 0.0: # Fallback para cálculo manual se API não fornecer DY
                dividends_series = fii.dividends
                one_year_ago = datetime.now() - pd.DateOffset(years=1)
                if dividends_series.index.tz is not None:
                    one_year_ago = pd.to_datetime(one_year_ago).tz_localize(dividends_series.index.tz)
                dividends_last_12m = dividends_series.loc[dividends_series.index > one_year_ago].sum()
                dy_12m = (dividends_last_12m / price * 100) if price > 0 else 0.0
            
            score = 1
            if dy_12m > selic + 2: score = 5
            elif dy_12m > selic: score = 4
            elif dy_12m > selic - 2: score = 3
            elif dy_12m > selic - 4: score = 2

            all_data.append({
                'Ticker': ticker, 'Tipo': fii_types.get(ticker, 'Outro'),
                'Preço Atual': price, 'DY (12M)': dy_12m,
                'Liquidez Diária': info.get('averageVolume', 0),
                'Compass Score': score
            })
            print(" Sucesso!")
        except Exception:
            print(" FALHA.")
            failed_tickers.append(ticker)
        time.sleep(0.3)
        
    print("\n--- COLETA FINALIZADA ---")
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv('fiis_data.csv', index=False, float_format='%.2f')
        print(f"Sucesso! 'fiis_data.csv' criado com {len(all_data)} FIIs.")
        if failed_tickers: print(f"Falha ao buscar: {', '.join(failed_tickers)}")
    else: print("ERRO: Nenhum dado foi coletado.")

if __name__ == "__main__":
    collect_all_data()
