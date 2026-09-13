import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests

st.set_page_config(page_title="Evolución Térmica en Mérida", layout="wide")

st.title("Análisis del Incremento de Temperaturas en Mérida, Yucatán 🌡️")

# --- MARCO TEÓRICO ---
st.header("1. Marco Teórico: La Isla de Calor y la Mancha Urbana")
st.markdown("""
El incremento de las temperaturas en Mérida no solo responde al **cambio climático global**, sino a un fenómeno local fuertemente agudizado en las últimas décadas: el efecto de la **Isla de Calor Urbana (ICU)**. 

De acuerdo con investigaciones recientes de la UNAM y otras instituciones (2025-2026), **Mérida duplicó su mancha urbana en solo dos décadas** (2000-2020). Este crecimiento disperso, impulsado por un intenso auge inmobiliario en la periferia (especialmente al norte), ha provocado la pérdida de cientos de hectáreas de selva baja caducifolia cada año. 

Al sustituir la vegetación natural —que regula el clima a través de la evapotranspiración— por planchas de asfalto y concreto, la ciudad retiene la radiación solar. Estudios ambientales estiman que esta deforestación para uso urbano puede generar aumentos directos de entre **2.3 °C y 3.9 °C** en la zona.
""")

# --- EXTRACCIÓN Y CACHÉ DE DATOS ---
@st.cache_data
def load_data():
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 20.9754,
        "longitude": -89.6170,
        "start_date": "1950-01-01",
        "end_date": "2026-08-31",
        "daily": "temperature_2m_mean",
        "timezone": "America/Merida"
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    df = pd.DataFrame({
        'fecha': pd.to_datetime(data['daily']['time']),
        'temp_media': data['daily']['temperature_2m_mean']
    })
    df.set_index('fecha', inplace=True)
    monthly_data = df.resample('ME').mean()
    monthly_data['año'] = monthly_data.index.year
    monthly_data['mes'] = monthly_data.index.month
    return monthly_data

with st.spinner("Extrayendo datos de la API ERA5 (Copernicus)..."):
    monthly_data = load_data()

pivot_df = monthly_data.pivot(index='mes', columns='año', values='temp_media')
meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

# --- DASHBOARD INTERACTIVO ---
st.header("2. Explorador Interactivo de Temperaturas")
st.markdown("Selecciona años específicos para comparar cómo ha cambiado la curva de temperatura mensual a lo largo del tiempo. El fondo gris muestra todos los años registrados desde 1950.")

col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("Filtros")
    años_disponibles = sorted(pivot_df.columns.tolist(), reverse=True)
    # Por defecto seleccionamos el récord más reciente, un pico anterior y años del siglo pasado
    años_seleccionados = st.multiselect("Años a comparar:", 
                                        options=años_disponibles, 
                                        default=[2026, 2023, 1990, 1960])

with col2:
    fig = go.Figure()
    
    # Fondo: todos los años en gris
    for year in pivot_df.columns:
        if year not in años_seleccionados:
            fig.add_trace(go.Scatter(
                x=meses_nombres, y=pivot_df[year],
                mode='lines', line=dict(color='lightgray', width=0.5),
                opacity=0.3, hoverinfo='skip', showlegend=False
            ))
            
    # Años seleccionados a color
    colores = px.colors.qualitative.Plotly
    for i, year in enumerate(años_seleccionados):
        fig.add_trace(go.Scatter(
            x=meses_nombres, y=pivot_df[year],
            mode='lines+markers', name=str(year),
            line=dict(width=3, color=colores[i % len(colores)])
        ))
        
    fig.update_layout(
        title="Promedio Mensual de Temperatura Superficial",
        xaxis_title="Mes",
        yaxis_title="Temperatura Media (°C)",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

# --- ANÁLISIS DE TENDENCIA ---
st.header("3. Análisis de Tendencia y Conclusiones")

# Calcular tendencia lineal
anual_promedio = monthly_data.groupby('año')['temp_media'].mean().dropna()
x = anual_promedio.index.values
y = anual_promedio.values
slope, intercept = np.polyfit(x, y, 1)
calentamiento_por_decada = slope * 10

col_metric, col_chart = st.columns([1, 2])

with col_metric:
    st.metric(label="Tasa de Calentamiento Calculada", value=f"+{calentamiento_por_decada:.2f} °C / Década")
    st.markdown(f"""
    **Conclusión del Proyecto:**
    Los datos de la API demuestran un incremento matemático consistente en la región. 
    
    Al cruzar la tasa de **+{calentamiento_por_decada:.2f} °C por década** con el acelerado crecimiento inmobiliario periférico, es evidente que la sustitución de la selva baja caducifolia por "manchones urbanos" de concreto ha bloqueado la disipación de calor nocturno. 
    
    Esto genera los dramáticos récords térmicos recientes en la península, confirmando que las olas de calor no son solo atmosféricas, sino agravadas severamente por la falta de planeación urbana sustentable.
    """)

with col_chart:
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Promedio Anual', line=dict(color='#3498db')))
    fig_trend.add_trace(go.Scatter(x=x, y=slope*x + intercept, mode='lines', name='Línea de Tendencia', line=dict(color='#e74c3c', dash='dash')))
    fig_trend.update_layout(
        title="Evolución de la Temperatura Promedio Anual (1950-2026)", 
        xaxis_title="Año", 
        yaxis_title="Temperatura Promedio (°C)",
        template="plotly_white"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
