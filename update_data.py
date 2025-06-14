# update_data.py (versão Final - Usando Fundamentus para Estabilidade)
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def get_fii_list():
    return sorted(['BTLG11', 'MXRF11', 'VGIR11', 'HGLG11', 'XPML11', 'KNCR11', 'VISC11','HGRU11', 'KNSC11', 'IRDM11', 'VILG11', 'CPTS11', 'RBRR11', 'MCCI11','XPLG11', 'RECR11', 'BCFF11', 'HGCR11', 'LVBI11', 'DEVA11', 'HGRE11','KNIP11', 'VRTA11', 'PVBI11', 'JSRE11', 'MALL11', 'GGRC11', 'ALZR11','BTCI11', 'BCRI11', 'BRCO11', 'VINO11', 'TORD11', 'RBRP11'])

def get_fii_types():
    return {'BTLG11':'Tijolo','HGLG11':'Tijolo','XPML11':'Tijolo','VISC11':'Tijolo','HGRU11':'Tijolo','VILG11':'Tijolo','XPLG11':'Tijolo','HGRE11':'Tijolo','LVBI11':'Tijolo','PVBI11':'Tijolo','JSRE11':'Tijolo','MALL11':'Tijolo','GGRC11':'Tijolo','ALZR11':'Tijolo','BRCO11':'Tijolo','VINO11':'Tijolo','RBRP11':'Tijolo','MXRF11':'Papel','VGIR11':'Papel','KNCR11':'Papel','KNSC11':'Papel','IRDM11':'Papel','CPTS11':'Papel','RBRR11':'Papel','MCCI11':'Papel','RECR11':'Papel','HGCR11':'Papel','DEVA11':'Papel','KNIP11':'Papel','VRTA11':'Papel','BTCI11':'Papel','BCRI11':'Papel','TORD11':'Papel','BCFF11':'Fundo de Fundos'}

def collect_fii_data_from_fundamentus():
    all_data, failed_tickers = [], []
    fiis_list, fii_types = get_fii_list(), get_fii_types()
    
    print("--- INICIANDO COLETA DE DADOS DO FUNDAMENTUS ---")

    for i, ticker in enumerate(fiis_list):
        print(f"({i+1}/{len(fiis_list)}) Buscando {ticker}...", end='')
        try:
            url = f"https://www.fundamentus.com.br/detalhes.php?papel={ticker}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            def get_value(label):
                element = soup.find(text=re.compile(label))
                return element.find_next('span', class_='txt').text.strip() if element else '0'

            data = {
                'Ticker': ticker,
                'Tipo': fii_types.get(ticker, 'Outro'),
                'Preço Atual': float(get_value('Cotação').replace(',', '.')),
                'P/VP': float(get_value('P/VP').replace(',', '.')),
                'DY (12M)': float(get_value('Div. Yield').replace('%', '').replace(',', '.')),
                'Liquidez Diária': int(get_value('Liq. 2 meses').replace('.', '')),
            }
            all_data.append(data)
            print(" Sucesso!")
        except Exception as e:
            print(f" FALHA. Erro: {e}")
            failed_tickers.append(ticker)
        time.sleep(0.1) # Pausa segura
        
    print("\n--- COLETA FINALIZADA ---")
    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv('fiis_data.csv', index=False, float_format='%.2f')
        print(f"Sucesso! 'fiis_data.csv' criado com {len(all_data)} FIIs.")
        if failed_tickers: print(f"Falha ao buscar: {', '.join(failed_tickers)}")
    else:
        print("ERRO: Nenhum dado foi coletado.")

if __name__ == "__main__":
    collect_fii_data_from_fundamentus()
