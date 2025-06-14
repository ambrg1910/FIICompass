# update_data.py
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

def get_fii_list():
    """Retorna a nossa lista mestre de FIIs para análise."""
    return sorted(['BTLG11', 'MXRF11', 'VGIR11', 'HGLG11', 'XPML11', 'KNCR11', 'VISC11','HGRU11', 'KNSC11', 'IRDM11', 'VILG11', 'CPTS11', 'RBRR11', 'MCCI11','XPLG11', 'RECR11', 'BCFF11', 'HGCR11', 'LVBI11', 'DEVA11', 'HGRE11','KNIP11', 'VRTA11', 'PVBI11', 'JSRE11', 'MALL11', 'GGRC11', 'ALZR11','BTCI11', 'BCRI11', 'BRCO11', 'VINO11', 'TORD11', 'RBRP11'])

def get_fii_types():
    """Retorna um dicionário com a classificação de cada FII."""
    return {
        'BTLG11': 'Tijolo', 'HGLG11': 'Tijolo', 'XPML11': 'Tijolo', 'VISC11': 'Tijolo',
        'HGRU11': 'Tijolo', 'VILG11': 'Tijolo', 'XPLG11': 'Tijolo', 'HGRE11': 'Tijolo',
        'LVBI11': 'Tijolo', 'PVBI11': 'Tijolo', 'JSRE11': 'Tijolo', 'MALL11': 'Tijolo',
        'GGRC11': 'Tijolo', 'ALZR11': 'Tijolo', 'BRCO11': 'Tijolo', 'VINO11': 'Tijolo',
        'RBRP11': 'Tijolo',
        'MXRF11': 'Papel', 'VGIR11': 'Papel', 'KNCR11': 'Papel', 'KNSC11': 'Papel',
        'IRDM11': 'Papel', 'CPTS11': 'Papel', 'RBRR11': 'Papel', 'MCCI11': 'Papel',
        'RECR11': 'Papel', 'HGCR11': 'Papel', 'DEVA11': 'Papel', 'KNIP11': 'Papel',
        'VRTA11': 'Papel', 'BTCI11': 'Papel', 'BCRI11': 'Papel', 'TORD11': 'Papel',
        'BCFF11': 'Fundo de Fundos'
    }

def collect_all_data():
    """
    Função principal que coleta os dados de todos os FIIs e salva em um arquivo CSV.
    Este é o coração da nossa nova arquitetura estável.
    """
    all_data = []
    failed_tickers = []
    fiis_list = get_fii_list()
    fii_types = get_fii_types()

    print("--- INICIANDO COLETA DE DADOS FII COMPASS ---")

    for i, ticker in enumerate(fiis_list):
        print(f"({i+1}/{len(fiis_list)}) Buscando dados para {ticker}...")
        try:
            fii = yf.Ticker(f"{ticker}.SA")
            info = fii.info

            price = info.get('regularMarketPrice', 0.0)

            # Cálculo manual e robusto do Dividend Yield
            dividends_series = fii.dividends
            one_year_ago = datetime.now() - pd.DateOffset(years=1)
            if dividends_series.index.tz is not None:
                one_year_ago = pd.to_datetime(one_year_ago).tz_localize(dividends_series.index.tz)

            dividends_last_12m = dividends_series.loc[dividends_series.index > one_year_ago].sum()
            dy_12m = (dividends_last_12m / price * 100) if price > 0 else 0.0

            all_data.append({
                'Ticker': ticker,
                'Tipo': fii_types.get(ticker, 'Outro'),
                'Preço Atual': price,
                'DY (12M)': dy_12m,
                'Liquidez Diária': info.get('averageVolume', 0),
            })
            print(f"  -> Sucesso!")

        except Exception as e:
            print(f"  -> FALHA ao buscar dados para {ticker}. Erro: {e}")
            failed_tickers.append(ticker)
        
        # A pausa estratégica que garante que a API não nos bloqueie.
        time.sleep(0.3)

    print("\n--- COLETA FINALIZADA ---")

    if all_data:
        df = pd.DataFrame(all_data)
        # Salvando o arquivo CSV que será a nossa fonte de dados primária
        df.to_csv('fiis_data.csv', index=False, float_format='%.2f')
        print(f"Sucesso! Arquivo 'fiis_data.csv' criado/atualizado com {len(all_data)} FIIs.")
        if failed_tickers:
            print(f"Tickers que falharam: {', '.join(failed_tickers)}")
    else:
        print("ERRO CRÍTICO: Nenhum dado foi coletado. O arquivo CSV não foi criado.")

if __name__ == "__main__":
    collect_all_data()
