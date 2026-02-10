import requests
import pandas as pd
import numpy as np

# --- 1. CONFIGURAÇÕES INICIAIS ---
TOKEN = '3bdd9dc3e9954e86ab48d380eff5ede8'
HEADERS = {'X-Auth-Token': TOKEN}
URL = 'https://api.football-data.org/v4/competitions/BSA/matches?season=2024'

def extrair_dados():
    print("Buscando dados na API...")
    response = requests.get(URL, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro na API: {response.status_code}")
        return None

# --- 2. TRATAMENTO DOS DADOS ---
dados_brutos = extrair_dados()

if dados_brutos and 'matches' in dados_brutos:
    # Transformar o JSON em tabela
    df = pd.json_normalize(dados_brutos['matches'])
    nome_time = 'Corinthians' 
    df_time = df[
        ((df['homeTeam.name'].str.contains(nome_time, case=False)) | 
         (df['awayTeam.name'].str.contains(nome_time, case=False))) &
        (df['status'] == 'FINISHED')
    ].copy()

    # --- 3. CRIAÇÃO DAS MÉTRICAS PARA O DASHBOARD ---
    def calcular_metricas(row):
        is_home = nome_time.lower() in row['homeTeam.name'].lower()
        gols_pro = row['score.fullTime.home'] if is_home else row['score.fullTime.away']
        gols_contra = row['score.fullTime.away'] if is_home else row['score.fullTime.home']
        adversario = row['awayTeam.name'] if is_home else row['homeTeam.name']
        mando = 'Casa' if is_home else 'Fora'
        
        if gols_pro > gols_contra:
            res, pts = 'Vitória', 3
        elif gols_pro < gols_contra:
            res, pts = 'Derrota', 0
        else:
            res, pts = 'Empate', 1
            
        return res, pts, mando, gols_pro, gols_contra, adversario

    df_time[['Resultado', 'Pontos', 'Mando', 'Gols_Pro', 'Gols_Contra', 'Adversario']] = \
        df_time.apply(lambda r: calcular_metricas(r), axis=1, result_type='expand')
    df_time['Saldo'] = df_time['Gols_Pro'] - df_time['Gols_Contra']
    df_time = df_time.sort_values('utcDate')
    df_time['Pontos_Acumulados'] = df_time['Pontos'].cumsum()

    # --- 4. SELEÇÃO FINAL E EXPORTAÇÃO ---
    colunas_dashboard = [
        'utcDate', 'Adversario', 'Mando', 'Resultado', 
        'Gols_Pro', 'Gols_Contra', 'Saldo', 'Pontos', 'Pontos_Acumulados'
    ]
    
    df_final = df_time[colunas_dashboard]
    
    print("\n" + "="*30)
    print(f"RESUMO TEMPORADA: {nome_time}")
    print("="*30)
    print(df_final.tail(10))

    df_final.to_csv('dados_para_dashboard.csv', index=False, encoding='utf-8-sig')
    print("\nSUCESSO! O arquivo 'dados_para_dashboard.csv' foi gerado.")
else:
    print("Não foi possível processar os dados.")