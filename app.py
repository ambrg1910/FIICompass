# app.py

import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard de Análise de FIIs",
    page_icon="📊",
    layout="wide"
)

# -----------------------------------------------------------------------------
# FUNÇÕES DE BUSCA DE DADOS (O Robô que coleta as informações)
# -----------------------------------------------------------------------------

# Usamos o cache do Streamlit para não sobrecarregar os sites e deixar o app mais rápido.
# O cache será atualizado a cada 15 minutos (900 segundos).
@st.cache_data(ttl=900)
def get_fii_data(ticker):
    """
    Busca os dados de um FII específico no site Status Invest.
    """
    url = f"https://statusinvest.com.br/fundos-imobiliarios/{ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lança um erro para status HTTP ruins (4xx ou 5xx)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- Buscando os dados específicos ---
        # Preço Atual
        price_element = soup.find('strong', class_='value')
        price = float(price_element.text.replace(',', '.')) if price_element else 0.0

        # Valor Patrimonial por Cota (VP)
        vp_element = soup.find('div', title='Valor patrimonial por cota').find_next('strong', class_='value')
        vp = float(vp_element.text.replace(',', '.')) if vp_element else 0.0

        # Dividend Yield (DY) 12M
        dy_element = soup.find('div', title='Dividend Yield com base nos últimos 12 meses').find_next('strong', class_='value')
        dy = float(dy_element.text.replace(',', '.')) if dy_element else 0.0
        
        return {
            'Preço Atual': price,
            'VP por Cota': vp,
            'DY (12M)': dy
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao buscar dados para {ticker}: {e}")
        return None
    except (AttributeError, ValueError) as e:
        st.error(f"Erro ao processar dados da página para {ticker}. O site pode ter mudado. Erro: {e}")
        return None

@st.cache_data(ttl=3600) # SELIC muda com menos frequência, cache de 1 hora
def get_selic_rate():
    """
    Busca a taxa SELIC atual.
    """
    # Usaremos o Status Invest também para a SELIC para manter a consistência da fonte
    url = "https://statusinvest.com.br/taxas/selic"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        selic_element = soup.find_all('strong', class_='value')[0] # O primeiro valor 'strong' da página é a SELIC
        selic = float(selic_element.text.replace(',', '.'))
        return selic
    except Exception as e:
        st.warning(f"Não foi possível buscar a taxa SELIC automaticamente. Usando valor padrão de 10.5%. Erro: {e}")
        return 10.5 # Valor de fallback caso a busca falhe

# -----------------------------------------------------------------------------
# O CÉREBRO: LÓGICA DE PONTUAÇÃO (Nossa Estratégia em Código)
# -----------------------------------------------------------------------------

def calculate_scores(fii_info, selic):
    """
    Calcula os scores de P/VP, DY e o Score Final com base nas nossas regras.
    """
    # --- Passo 1: Calcular o P/VP ---
    if fii_info['VP por Cota'] > 0:
        p_vp = fii_info['Preço Atual'] / fii_info['VP por Cota']
    else:
        p_vp = 0
    fii_info['P/VP'] = p_vp

    # --- Passo 2: Pontuação de P/VP ---
    score_pvp = 0
    if fii_info['Tipo'] == 'Tijolo':
        if p_vp < 0.98: score_pvp = 3
        elif 0.98 <= p_vp < 1.02: score_pvp = 2
        elif 1.02 <= p_vp < 1.05: score_pvp = 1
    elif fii_info['Tipo'] == 'Papel':
        if p_vp < 1.01: score_pvp = 3
        elif 1.01 <= p_vp < 1.04: score_pvp = 2
        elif 1.04 <= p_vp < 1.06: score_pvp = 1
    
    # --- Passo 3: Pontuação de Dividend Yield (DY) ---
    score_dy = 0
    dy = fii_info['DY (12M)']
    if fii_info['Tipo'] == 'Tijolo':
        if dy > selic + 2.0: score_dy = 3
        elif dy > selic: score_dy = 2
        elif dy >= selic - 2.0: score_dy = 1
    elif fii_info['Tipo'] == 'Papel':
        if dy > selic + 3.0: score_dy = 3
        elif dy > selic + 1.5: score_dy = 2
        elif dy > selic: score_dy = 1

    # --- Passo 4: Calcular Score Final com Pesos ---
    score_final = 0
    if fii_info['Tipo'] == 'Tijolo':
        score_final = (score_pvp * 2) + (score_dy * 1)
    elif fii_info['Tipo'] == 'Papel':
        score_final = (score_pvp * 1) + (score_dy * 2)

    fii_info['Score Final'] = score_final
    return fii_info

# -----------------------------------------------------------------------------
# INTERFACE DO USUÁRIO (O que aparece na tela)
# -----------------------------------------------------------------------------

# --- Título e Descrição ---
st.title('📊 Dashboard de Apoio à Decisão de FIIs')
st.markdown(f"Análise baseada na estratégia de pontuação para FIIs de Tijolo e Papel. Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

# --- Nossa lista de FIIs ---
fiis_a_analisar = [
    {'Ticker': 'BTLG11', 'Tipo': 'Tijolo'},
    {'Ticker': 'MXRF11', 'Tipo': 'Papel'},
    {'Ticker': 'VGIR11', 'Tipo': 'Papel'},
]

# --- Barra lateral com informações de mercado ---
selic_rate = get_selic_rate()
st.sidebar.header("Condições de Mercado")
st.sidebar.metric(label="Taxa SELIC Atual", value=f"{selic_rate:.2f}%")
st.sidebar.info("Este dashboard utiliza a SELIC como referência para avaliar o retorno dos FIIs.")

# --- Processamento e Exibição dos Dados ---
if st.button('Analisar Meus FIIs'):
    with st.spinner('Buscando dados e calculando scores... Por favor, aguarde.'):
        
        lista_final = []
        for fii in fiis_a_analisar:
            dados = get_fii_data(fii['Ticker'])
            if dados:
                fii_completo = {**fii, **dados}
                fii_analisado = calculate_scores(fii_completo, selic_rate)
                lista_final.append(fii_analisado)
        
        if lista_final:
            # Criar um DataFrame com o Pandas para exibir a tabela
            df = pd.DataFrame(lista_final)

            # Ordenar pelo Score Final (do maior para o menor)
            df = df.sort_values(by='Score Final', ascending=False).reset_index(drop=True)

            # Adicionar a coluna de Recomendação
            df['Recomendação'] = ''
            if not df.empty:
                df.loc[0, 'Recomendação'] = '🏆 Aporte do Mês'
                
                # Regra da trava de segurança
                if df.loc[0, 'Score Final'] < 4:
                    df.loc[0, 'Recomendação'] = '⚠️ Nenhuma Oportunidade Clara'


            # Formatação final para exibição
            df_display = df[['Ticker', 'Tipo', 'Preço Atual', 'P/VP', 'DY (12M)', 'Score Final', 'Recomendação']]

            st.subheader("Ranking de Atratividade para Aporte")
            
            # Função para estilizar a tabela
            def highlight_top(s):
                return ['background-color: #2E8B57; color: white' if v == '🏆 Aporte do Mês' else '' for v in s]
            
            st.dataframe(
                df_display.style.format({
                    'Preço Atual': 'R$ {:.2f}',
                    'P/VP': '{:.2f}',
                    'DY (12M)': '{:.2f}%'
                }).apply(highlight_top, subset=['Recomendação']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.error("Não foi possível obter dados para nenhum dos FIIs. Tente novamente mais tarde.")

st.markdown("---")
st.markdown("Desenvolvido com base na estratégia do Expert em Investimentos.")
