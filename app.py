import requests
import pandas as pd
import streamlit as st
from datetime import datetime

# === CONFIG INICIAL ===
st.set_page_config(page_title="Consulta de Odds", layout="wide")
st.title("Consulta de Odds via API-Football")

# === CHAVE DE API ===
API_KEY = 'f8004fe5cca0e75109a44ae6b4cdd9a2'
HEADERS = {'x-apisports-key': API_KEY}

# === INPUT DE DATA ===
data_input = st.date_input("Selecione a data da partida", datetime.today()).strftime("%Y-%m-%d")

# === BUSCA JOGOS COM ODDS ===
st.info(f"Buscando partidas com odds para {data_input}...")
url_odds = f"https://v3.football.api-sports.io/odds?date={data_input}"
resp = requests.get(url_odds, headers=HEADERS)
odds_response = resp.json().get('response', [])

if not odds_response:
    st.warning("Nenhuma partida com odds disponíveis para essa data.")
    st.stop()

# === PREPARAR LISTA DE PARTIDAS ===
partidas = []
for jogo in odds_response:
    fixture_id = jogo['fixture']['id']
    dt_jogo = datetime.fromisoformat(jogo['fixture']['date']).strftime('%d/%m %H:%M')

    # Buscar nomes dos times
    fix_url = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}"
    fix_resp = requests.get(fix_url, headers=HEADERS)
    dados_fixture = fix_resp.json()['response'][0]
    home = dados_fixture['teams']['home']['name']
    away = dados_fixture['teams']['away']['name']

    jogo['teams'] = {'home': home, 'away': away}
    partidas.append({
        'label': f"{dt_jogo} | {home} x {away}",
        'value': fixture_id,
        'jogo': jogo
    })

# === SELECIONAR PARTIDA ===
options = [p['label'] for p in partidas]
selecionada = st.selectbox("Escolha a partida para ver odds:", options)

if selecionada:
    jogo_escolhido = next(p['jogo'] for p in partidas if p['label'] == selecionada)
    home = jogo_escolhido['teams']['home']
    away = jogo_escolhido['teams']['away']
    fixture_id = jogo_escolhido['fixture']['id']

    st.subheader(f"Odds para: {home} x {away}")

    # === COLETAR ODDS EM TABELA ===
    csv_data = []
    for bookmaker in jogo_escolhido['bookmakers']:
        casa = bookmaker['name']
        for bet in bookmaker['bets']:
            mercado = bet['name']
            for val in bet['values']:
                csv_data.append({
                    'Casa': casa,
                    'Mercado': mercado,
                    'Linha': val['value'],
                    'Odd': val['odd']
                })

    df_odds = pd.DataFrame(csv_data)
    st.dataframe(df_odds)

    # === DOWNLOAD DO CSV ===
    csv_file = df_odds.to_csv(index=False).encode('utf-8')
    nome_arquivo = f"odds_{home}_vs_{away}_{data_input}.csv".replace(' ', '_').replace('/', '-')
    st.download_button(
        label="📥 Baixar arquivo CSV",
        data=csv_file,
        file_name=nome_arquivo,
        mime='text/csv'
    )
