import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date, timedelta

# --- Configuración y Título ---
st.set_page_config(
    page_title="Dashboard de KPIs Empresariales",
    layout="wide", # Usa el ancho completo de la pantalla
    initial_sidebar_state="expanded"
)

st.title("💰 Dashboard de KPIs de Ventas Empresariales")
st.markdown("---")

# --- 1. Generación de Datos (Simulación) ---
@st.cache_data
def load_data(n_rows=1000):
    """Genera un DataFrame simulado de datos de ventas."""
    
    # Crear un rango de fechas
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    dates = pd.to_datetime(np.random.choice(pd.date_range(start_date, end_date), n_rows))

    data = pd.DataFrame({
        'Fecha': dates,
        'Monto_Venta': np.random.normal(loc=150, scale=50, size=n_rows).round(2).clip(10, None), # Monto con distribución normal, mínimo 10
        'Region': np.random.choice(['Norte', 'Sur', 'Este', 'Oeste'], n_rows),
        'Vendedor': np.random.choice([f'Vendedor {i}' for i in range(1, 11)], n_rows),
        'Producto': np.random.choice(['Licencia A', 'Servicio B', 'Hardware C'], n_rows),
        'Unidades': np.random.randint(1, 10, n_rows)
    })
    
    # Asegurar que la fecha sea el índice
    data.set_index('Fecha', inplace=True)
    data.sort_index(inplace=True)
    return data

df = load_data()

# --- 2. Sidebar (Filtros) ---
st.sidebar.header("Filtros de Datos")

# Filtro de Región
regiones = df['Region'].unique()
region_seleccionada = st.sidebar.multiselect(
    "Seleccionar Región:",
    options=regiones,
    default=regiones
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

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    # Caso para cuando solo se selecciona una fecha (o no hay selección completa)
    start_date = min_date
    end_date = max_date


# Aplicar filtros
df_filtrado = df[
    (df.index.date >= start_date) & 
    (df.index.date <= end_date) &
    (df['Region'].isin(region_seleccionada))
]

# --- 3. Métrica de KPIs (Usando columnas de Streamlit) ---
st.header("KPIs Clave (Key Performance Indicators)")

# Calcular KPIs
total_ventas = df_filtrado['Monto_Venta'].sum().round(2)
total_transacciones = df_filtrado.shape[0]
venta_promedio = (total_ventas / total_transacciones).round(2) if total_transacciones > 0 else 0

# Definir columnas para las métricas
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total de Ingresos",
        value=f"${total_ventas:,.2f}",
        delta="15%" # Puedes añadir lógica de comparación real aquí
    )

with col2:
    st.metric(
        label="Total de Transacciones",
        value=f"{total_transacciones:,}",
        delta_color="off"
    )

with col3:
    st.metric(
        label="Venta Promedio",
        value=f"${venta_promedio:.2f}",
        delta="-3%", # Puedes añadir lógica de comparación real aquí
        delta_color="inverse"
    )

st.markdown("---")

# --- 4. Gráficos Interactivos (Distribución) ---

col4, col5 = st.columns(2)

with col4:
    st.subheader("Ventas por Región")
    # Gráfico de barras de ventas por región
    ventas_region = df_filtrado.groupby('Region')['Monto_Venta'].sum().reset_index()
    fig_region = px.bar(
        ventas_region, 
        x='Region', 
        y='Monto_Venta', 
        color='Region',
        title="Ventas Totales por Región"
    )
    st.plotly_chart(fig_region, use_container_width=True)

with col5:
    st.subheader("Tendencia de Ingresos Diarios")
    # Gráfico de línea para la tendencia de ventas
    ventas_diarias = df_filtrado.resample('D')['Monto_Venta'].sum().reset_index()
    fig_line = px.line(
        ventas_diarias, 
        x='Fecha', 
        y='Monto_Venta',
        title='Tendencia Diaria de Ingresos'
    )
    st.plotly_chart(fig_line, use_container_width=True)

# --- 5. Desglose de Datos (Tabla) ---
st.subheader("Desglose de Ventas por Vendedor")
ventas_vendedor = df_filtrado.groupby('Vendedor')['Monto_Venta'].agg(['sum', 'count', 'mean']).reset_index()
ventas_vendedor.columns = ['Vendedor', 'Ventas Totales', 'Transacciones', 'Venta Promedio']
ventas_vendedor['Ventas Totales'] = ventas_vendedor['Ventas Totales'].map('${:,.2f}'.format)
ventas_vendedor['Venta Promedio'] = ventas_vendedor['Venta Promedio'].map('${:,.2f}'.format)

st.dataframe(ventas_vendedor, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.success("Dashboard actualizado con datos simulados.")