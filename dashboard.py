"""
Dashboard Interativo - Copa do Mundo FIFA (1930-2022)
Streamlit + Plotly + Pandas
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# Configuração da página
st.set_page_config(
    page_title="Copa do Mundo Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tema personalizado
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.8;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# CARREGAMENTO DOS DADOS
# ============================================================================
@st.cache_data
def load_data():
    data_path = Path('archive')

    world_cup_df = pd.read_csv(data_path / 'world_cup.csv')
    fifa_ranking_df = pd.read_csv(data_path / 'fifa_ranking_2022-10-06.csv')
    matches_df = pd.read_csv(data_path / 'matches_1930_2022.csv')

    # Tratamento dos dados de partidas
    matches_df['Year'] = pd.to_numeric(matches_df['Year'], errors='coerce')
    matches_df = matches_df.dropna(subset=['home_score', 'away_score', 'Year'])
    matches_df['home_score'] = matches_df['home_score'].astype(int)
    matches_df['away_score'] = matches_df['away_score'].astype(int)
    matches_df['total_goals'] = matches_df['home_score'] + matches_df['away_score']

    # Calcular vitórias
    matches_df['home_winner'] = (matches_df['home_score'] > matches_df['away_score']).astype(int)
    matches_df['away_winner'] = (matches_df['away_score'] > matches_df['home_score']).astype(int)

    return world_cup_df, fifa_ranking_df, matches_df

world_cup_df, fifa_ranking_df, matches_df = load_data()

# ============================================================================
# HEADER
# ============================================================================
st.title("⚽ Copa do Mundo FIFA - Dashboard Analítico")
st.markdown("Análise completa de dados de 1930 a 2022")

# ============================================================================
# SIDEBAR - FILTROS
# ============================================================================
st.sidebar.header("🎯 Filtros")

years_available = sorted(matches_df['Year'].unique())
year_range = st.sidebar.slider(
    "Selecione o intervalo de anos",
    min_value=int(years_available[0]),
    max_value=int(years_available[-1]),
    value=(int(years_available[0]), int(years_available[-1]))
)

# Filtrar dados por ano
matches_filtered = matches_df[
    (matches_df['Year'] >= year_range[0]) &
    (matches_df['Year'] <= year_range[1])
]

# ============================================================================
# KPIs - LINHA 1
# ============================================================================
st.header("📊 Indicadores Principais (KPIs)")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_partidas = len(matches_filtered)
    st.metric(
        label="Total de Partidas",
        value=f"{total_partidas:,}",
        delta=f"{year_range[0]}-{year_range[1]}"
    )

with col2:
    total_gols = int(matches_filtered['total_goals'].sum())
    st.metric(
        label="Gols Marcados",
        value=f"{total_gols:,}",
        delta=f"Média: {matches_filtered['total_goals'].mean():.2f}/jogo"
    )

with col3:
    maior_goleada = matches_filtered['total_goals'].max()
    st.metric(
        label="Maior Goleada",
        value=f"{int(maior_goleada)} gols",
        delta="Em uma partida"
    )

with col4:
    zeros = len(matches_filtered[matches_filtered['total_goals'] == 0])
    st.metric(
        label="Partidas 0x0",
        value=f"{zeros}",
        delta=f"{(zeros/total_partidas*100):.1f}% do total"
    )

with col5:
    campeonatos = len(world_cup_df[
        (world_cup_df['Year'] >= year_range[0]) &
        (world_cup_df['Year'] <= year_range[1])
    ])
    st.metric(
        label="Edições da Copa",
        value=f"{campeonatos}",
        delta="Torneios analisados"
    )

# ============================================================================
# SEÇÃO 1: CAMPEÕES E PERFORMANCE
# ============================================================================
st.header("🏆 Campeões e Desempenho")

tab1, tab2, tab3 = st.tabs(["Campeões Históricos", "Top Times", "Gols por Time"])

with tab1:
    col1, col2 = st.columns(2)

    with col1:
        # Gráfico 1: Títulos por país
        champions_data = world_cup_df['Champion'].value_counts().head(10)
        fig_champions = px.bar(
            x=champions_data.values,
            y=champions_data.index,
            orientation='h',
            title="Top 10 Campeões Mundiais",
            labels={'x': 'Número de Títulos', 'y': 'País'},
            color=champions_data.values,
            color_continuous_scale='Viridis'
        )
        fig_champions.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig_champions, use_container_width=True)

    with col2:
        # Gráfico 2: Finais - Campeões vs Vice
        final_data = pd.DataFrame({
            'Campeão': world_cup_df['Champion'].value_counts(),
            'Vice': world_cup_df['Runner-Up'].value_counts()
        }).fillna(0).head(8)

        fig_finals = go.Figure(data=[
            go.Bar(name='Campeão', x=final_data.index, y=final_data['Campeão'], marker_color='gold'),
            go.Bar(name='Vice', x=final_data.index, y=final_data['Vice'], marker_color='silver')
        ])
        fig_finals.update_layout(
            title="Finais - Campeões vs Vice-campeões",
            barmode='group',
            height=500,
            xaxis_title='País',
            yaxis_title='Frequência'
        )
        st.plotly_chart(fig_finals, use_container_width=True)

with tab2:
    # Top times por vitórias
    home_wins = matches_filtered.groupby('home_team')['home_winner'].sum()
    away_wins = matches_filtered.groupby('away_team')['away_winner'].sum()
    total_wins = home_wins.add(away_wins, fill_value=0).sort_values(ascending=False).head(15)

    fig_top_teams = px.bar(
        x=total_wins.values,
        y=total_wins.index,
        orientation='h',
        title="Top 15 Seleções com Mais Vitórias",
        labels={'x': 'Número de Vitórias', 'y': 'Seleção'},
        color=total_wins.values,
        color_continuous_scale='Blues'
    )
    fig_top_teams.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig_top_teams, use_container_width=True)

with tab3:
    # Times que mais marcaram gols
    gols_home = matches_filtered.groupby('home_team')['home_score'].sum()
    gols_away = matches_filtered.groupby('away_team')['away_score'].sum()
    total_gols_time = gols_home.add(gols_away, fill_value=0).sort_values(ascending=False).head(15)

    fig_gols_time = px.bar(
        x=total_gols_time.values,
        y=total_gols_time.index,
        orientation='h',
        title="Top 15 Seleções com Mais Gols Marcados",
        labels={'x': 'Total de Gols', 'y': 'Seleção'},
        color=total_gols_time.values,
        color_continuous_scale='Reds'
    )
    fig_gols_time.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig_gols_time, use_container_width=True)

# ============================================================================
# SEÇÃO 2: ANÁLISE TEMPORAL
# ============================================================================
st.header("📈 Evolução Histórica da Copa")

col1, col2 = st.columns(2)

with col1:
    # Gols por édição
    gols_por_ano = matches_filtered.groupby('Year').agg({
        'total_goals': 'sum',
        'home_team': 'count'
    }).rename(columns={'home_team': 'Partidas'})
    gols_por_ano['Media_Gols'] = gols_por_ano['total_goals'] / gols_por_ano['Partidas']

    fig_gols_ano = go.Figure()
    fig_gols_ano.add_trace(go.Scatter(
        x=gols_por_ano.index,
        y=gols_por_ano['Media_Gols'],
        mode='lines+markers',
        name='Média de Gols',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    fig_gols_ano.update_layout(
        title="Evolução da Média de Gols por Partida",
        xaxis_title="Ano",
        yaxis_title="Gols por Partida (Média)",
        height=450,
        hovermode='x unified'
    )
    st.plotly_chart(fig_gols_ano, use_container_width=True)

with col2:
    # Distribuição de gols
    fig_dist_gols = go.Figure(data=[
        go.Histogram(
            x=matches_filtered['total_goals'],
            nbinsx=int(matches_filtered['total_goals'].max()) + 1,
            marker_color='#ff7f0e',
            name='Frequência'
        )
    ])
    fig_dist_gols.update_layout(
        title="Distribuição de Gols por Partida",
        xaxis_title="Gols na Partida",
        yaxis_title="Frequência",
        height=450,
        showlegend=False
    )
    st.plotly_chart(fig_dist_gols, use_container_width=True)

# ============================================================================
# SEÇÃO 3: ANÁLISE POR CONFEDERAÇÃO
# ============================================================================
st.header("🌍 Análise por Confederação")

col1, col2 = st.columns(2)

with col1:
    # Ranking médio por confederação
    conf_ranking = fifa_ranking_df.groupby('association').agg({
        'points': 'mean',
        'rank': 'count'
    }).rename(columns={'rank': 'Num_Times'}).sort_values('points', ascending=False)

    fig_conf = px.bar(
        x=conf_ranking['points'].values,
        y=conf_ranking.index,
        orientation='h',
        title="Força Média das Confederações (Oct 2022)",
        labels={'x': 'Pontos Médios', 'y': 'Confederação'},
        color=conf_ranking['points'].values,
        color_continuous_scale='Greens'
    )
    fig_conf.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig_conf, use_container_width=True)

with col2:
    # Top 10 times do ranking
    top_10_fifa = fifa_ranking_df.head(10)

    fig_top_fifa = px.bar(
        x=top_10_fifa['points'],
        y=top_10_fifa['team'],
        orientation='h',
        title="Top 10 - Ranking FIFA (Outubro 2022)",
        labels={'points': 'Pontos', 'team': 'Seleção'},
        color=top_10_fifa['points'],
        color_continuous_scale='Purples'
    )
    fig_top_fifa.update_layout(height=500, showlegend=False)
    st.plotly_chart(fig_top_fifa, use_container_width=True)

# ============================================================================
# SEÇÃO 4: ESTATÍSTICAS DA COPA
# ============================================================================
st.header("📋 Estatísticas da Copa do Mundo")

col1, col2, col3 = st.columns(3)

with col1:
    # Número de times por edição
    copa_stats = world_cup_df[
        (world_cup_df['Year'] >= year_range[0]) &
        (world_cup_df['Year'] <= year_range[1])
    ]

    fig_teams = go.Figure()
    fig_teams.add_trace(go.Scatter(
        x=copa_stats['Year'],
        y=copa_stats['Teams'],
        mode='lines+markers',
        fill='tozeroy',
        name='Número de Times',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=10)
    ))
    fig_teams.update_layout(
        title="Evolução: Número de Times",
        xaxis_title="Ano",
        yaxis_title="Quantidade de Times",
        height=450,
        showlegend=False
    )
    st.plotly_chart(fig_teams, use_container_width=True)

with col2:
    # Número de partidas por edição
    fig_matches = go.Figure()
    fig_matches.add_trace(go.Bar(
        x=copa_stats['Year'],
        y=copa_stats['Matches'],
        name='Partidas',
        marker_color='#d62728'
    ))
    fig_matches.update_layout(
        title="Número de Partidas por Edição",
        xaxis_title="Ano",
        yaxis_title="Quantidade de Partidas",
        height=450,
        showlegend=False
    )
    st.plotly_chart(fig_matches, use_container_width=True)

with col3:
    # Público total
    fig_attendance = go.Figure()
    fig_attendance.add_trace(go.Bar(
        x=copa_stats['Year'],
        y=copa_stats['Attendance'] / 1e6,
        name='Público',
        marker_color='#9467bd'
    ))
    fig_attendance.update_layout(
        title="Público Total por Edição",
        xaxis_title="Ano",
        yaxis_title="Público (Milhões)",
        height=450,
        showlegend=False
    )
    st.plotly_chart(fig_attendance, use_container_width=True)

# ============================================================================
# SEÇÃO 5: TABELA DE DADOS
# ============================================================================
st.header("📑 Dados Detalhados")

tab_matches, tab_ranking = st.tabs(["Últimas Partidas", "Ranking FIFA"])

with tab_matches:
    # Mostrar últimas partidas
    matches_display = matches_filtered[['Date', 'home_team', 'home_score', 'away_score', 'away_team', 'Venue', 'Round']].copy()
    matches_display = matches_display.sort_values('Date', ascending=False).head(20)
    matches_display.columns = ['Data', 'Time Casa', 'Gols Mandante', 'Gols Visitante','Time Visitante', 'Estádio', 'Fase']

    st.dataframe(matches_display, use_container_width=True, hide_index=True)

with tab_ranking:
    # Ranking FIFA
    ranking_display = fifa_ranking_df[['rank', 'team', 'association', 'points', 'previous_rank']].copy()
    ranking_display.columns = ['Posição', 'Seleção', 'Confederação', 'Pontos', 'Posição Anterior']

    st.dataframe(ranking_display, use_container_width=True, hide_index=True)

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
    <div style='text-align: center; color: #888; font-size: 12px;'>
    📊 Dashboard de Copa do Mundo FIFA • Dados: 1930-2022 •
    Atualizado: Outubro 2022
    </div>
""", unsafe_allow_html=True)
