import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date, timedelta

# --- Configuración y Título ---
st.set_page_config(
    page_title="Dashboard de Stock por Archivo Local",
    layout="wide", # Usa el ancho completo de la pantalla
    initial_sidebar_state="expanded"
)

st.title("📈 Visualización y Análisis de Stock (Carga de Archivo Local)")
st.markdown("---")

# --- 1. Carga de Archivo CSV (Única forma segura desde el PC del usuario) ---
#st.subheader("1. Carga de Datos")
#st.warning("⚠️ Nota: Por seguridad, las aplicaciones web no pueden acceder a rutas locales (ej: C:/datos.csv). Debes usar el botón 'Browse files' para seleccionar y subir el archivo desde tu PC.")
uploaded_file = "Stock.csv" #st.file_uploader("Stock", type=["csv"])

# Lógica principal que se ejecuta solo si se sube un archivo
if uploaded_file is not None:
    try:
        # Cargar datos desde el archivo subido
        df = pd.read_csv(uploaded_file)
        
        st.markdown("---")
        st.subheader("Información del Formato CSV")
        st.info("La aplicación intentará inferir las columnas de 'Fecha', 'Precio_Cierre' y 'Ticker' (Símbolo) basadas en nombres comunes. Si los cálculos no son correctos, por favor verifica que tu CSV contenga dichas columnas.")

        # --- Preprocesamiento de Datos (Asumiendo columnas de stock) ---
        
        # 1. Identificar y convertir la columna de Fecha
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'fecha' in c.lower() or 'time' in c.lower()]
        if not date_cols:
            st.error("No se encontró una columna de Fecha/Time. Asegúrate de que el CSV tenga una columna con un nombre como 'Fecha' o 'Date'.")
            st.stop()
        
        df['Fecha'] = pd.to_datetime(df[date_cols[0]])
        df.set_index('Fecha', inplace=True)
        df.sort_index(inplace=True)

        # 2. Identificar y renombrar la columna de Precio
        price_cols = [c for c in df.columns if 'close' in c.lower() or 'precio' in c.lower() or 'price' in c.lower()]
        if not price_cols:
            st.error("No se encontró una columna de Precio de Cierre. Asegúrate de que el CSV tenga una columna con un nombre como 'Precio_Cierre' o 'Close'.")
            st.stop()
        
        price_col_name = price_cols[0]
        df.rename(columns={price_col_name: 'Precio_Cierre'}, inplace=True)

        # 3. Identificar y renombrar la columna de Ticker (Símbolo)
        ticker_cols = [c for c in df.columns if 'ticker' in c.lower() or 'symbol' in c.lower() or 'simbolo' in c.lower()]
        if not ticker_cols:
             # Si no hay columna Ticker, asumimos que es un solo stock
             df['Ticker'] = 'STOCK_PRINCIPAL'
        else:
             df['Ticker'] = df[ticker_cols[0]]

        # Limpieza de datos
        df = df.dropna(subset=['Precio_Cierre'])
        
        # --- 2. Sidebar (Filtros) ---
        st.sidebar.header("Filtros de Datos")

        # Filtro de Ticker (Similar a Región)
        tickers = df['Ticker'].unique()
        ticker_seleccionado = st.sidebar.multiselect(
            "Seleccionar Ticker:",
            options=tickers,
            # Selecciona por defecto todos los tickers si son menos de 5, o los primeros 5
            default=tickers if len(tickers) < 5 else tickers[:5] 
        )

        # Filtro de Rango de Fechas
        min_date = df.index.min().date()
        max_date = df.index.max().date()

        date_range = st.sidebar.date_input(
            "Seleccionar Rango de Fechas:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Asegurarse de que el rango de fechas sea válido
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = min_date
            end_date = max_date

        # Aplicar filtros
        df_filtrado = df[
            (df.index.date >= start_date) & 
            (df.index.date <= end_date) &
            (df['Ticker'].isin(ticker_seleccionado))
        ]
        
        if df_filtrado.empty:
            st.warning("No hay datos para la selección actual de filtros. Por favor, ajusta tu rango de fechas o Tickers.")
            st.stop()
        
        
        # --- 3. Métrica de KPIs (Stock-centric) ---
        st.header("KPIs Clave de Rendimiento")

        # Calcular KPIs
        # 1. Último Precio (basado en el índice de fecha más reciente en los datos filtrados)
        ultimo_precio = df_filtrado['Precio_Cierre'].iloc[-1].round(2)
        
        # 2. Retorno Diario Promedio
        # Se calcula el retorno diario del promedio de precios si hay múltiples Tickers
        df_returns = df_filtrado.groupby(df_filtrado.index.normalize())['Precio_Cierre'].mean().pct_change().dropna()
        retorno_diario_promedio = df_returns.mean() * 100
        
        # 3. Volatilidad Anualizada (Desviación estándar de los retornos)
        # Asume 252 días de trading por año
        volatilidad_anualizada = df_returns.std() * np.sqrt(252) * 100 
        
        # 4. Total de Días Analizados
        total_dias = df_filtrado.index.normalize().nunique()

        # Definir columnas para las métricas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Último Precio de Cierre",
                value=f"${ultimo_precio:,.2f}",
                delta=f"{retorno_diario_promedio:.2f}% (Retorno Diario Prom.)", # Muestra el retorno como delta
                delta_color="normal" if retorno_diario_promedio >= 0 else "inverse"
            )

        with col2:
            st.metric(
                label="Volatilidad Anualizada",
                value=f"{volatilidad_anualizada:.2f}%",
                delta_color="off"
            )

        with col3:
            st.metric(
                label="Días Analizados",
                value=f"{total_dias:,}",
                delta_color="off"
            )

        st.markdown("---")

        # --- 4. Gráficos Interactivos (Tendencia y Distribución) ---

        col4, col5 = st.columns(2)

        with col4:
            st.subheader("Tendencia del Precio de Cierre")
            # Gráfico de línea para la tendencia del precio por Ticker
            fig_line = px.line(
                df_filtrado.reset_index(), 
                x='Fecha', 
                y='Precio_Cierre', 
                color='Ticker',
                title='Precio de Cierre a lo largo del Tiempo',
                labels={'Precio_Cierre': 'Precio de Cierre ($)', 'Fecha': 'Fecha'}
            )
            st.plotly_chart(fig_line, use_container_width=True)

        with col5:
            st.subheader("Distribución de Retornos Diarios")
            # Calcular retornos diarios por Ticker para el histograma
            df_retornos_ticker = df_filtrado.groupby('Ticker')['Precio_Cierre'].pct_change().dropna().reset_index()
            df_retornos_ticker.columns = ['Fecha', 'Ticker', 'Retorno']
            
            fig_hist = px.histogram(
                df_retornos_ticker,
                x='Retorno',
                color='Ticker',
                nbins=50,
                title='Distribución de Retornos Diarios',
                labels={'Retorno': 'Retorno Diario'},
                marginal="box" # Añade un box plot en el margen
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        # --- 5. Desglose de Datos (Tabla) ---
        st.subheader("Datos Detallados (Primeras 100 Filas)")
        # Muestra las primeras 100 filas de los datos filtrados
        st.dataframe(df_filtrado.head(100), use_container_width=True)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo CSV: {e}")
        st.info("Asegúrate de que el archivo CSV esté bien formado y que las columnas de fecha y precio sean parseables.")
        
else:
    # Mensaje cuando no se ha subido ningún archivo
    st.info("Sube un archivo CSV con datos históricos de precios de stock para visualizar el dashboard.")
    st.sidebar.markdown("---")
    st.sidebar.error("Esperando archivo CSV...")
