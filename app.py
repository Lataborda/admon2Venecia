import streamlit as st
import pandas as pd
import psycopg2

st.set_page_config(page_title="Cartera Venecia", page_icon="🏡", layout="wide")

@st.cache_data(ttl=600)
def cargar_datos():
    conexion = psycopg2.connect(
    host=st.secrets["supabase"]["host"],
    port=st.secrets["supabase"]["port"],
    dbname=st.secrets["supabase"]["dbname"],
    user=st.secrets["supabase"]["user"],
    password=st.secrets["supabase"]["password"],
    sslmode="require"
)

    query = "SELECT * FROM reporte_gerencial;"
    df = pd.read_sql_query(query, conexion)
    conexion.close()
    return df

try:
    df = cargar_datos()
    
    # 2. Preparación de datos (Crear columna de Mes para filtrar)
    # Convertimos la fecha a formato de tiempo de Pandas
    df['fecha_pago'] = pd.to_datetime(df['fecha_pago'])
    # Creamos una columna bonita con el Año y el Mes (Ej: 2026 - 03)
    df['Mes_Pago'] = df['fecha_pago'].dt.strftime('%Y - %m')
    
    # ==========================================
    # BARRA LATERAL (MENÚ DE FILTROS)
    # ==========================================
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2163/2163350.png", width=100) # Un ícono de casa genérico
    st.sidebar.title("Filtros de Búsqueda")
    
    # Filtro 1: Mes
    lista_meses = ["Todos los meses"] + sorted(list(df['Mes_Pago'].dropna().unique()), reverse=True)
    mes_seleccionado = st.sidebar.selectbox("📅 Seleccionar Mes", lista_meses)
    
    # Filtro 2: Número de Predio
    lista_predios = ["Todos los predios"] + sorted(list(df['Numero de predio'].dropna().unique()))
    predio_seleccionado = st.sidebar.selectbox("🏡 Número de Predio", lista_predios)
    
    # Filtro 3: Nombre del Propietario
    lista_propietarios = ["Todos los propietarios"] + sorted(list(df['Nombre Completo'].dropna().unique()))
    propietario_seleccionado = st.sidebar.selectbox("👤 Propietario", lista_propietarios)
    
    # ==========================================
    # LÓGICA DE FILTRADO (El motor del tablero)
    # ==========================================
    df_filtrado = df.copy()
    
    if mes_seleccionado != "Todos los meses":
        df_filtrado = df_filtrado[df_filtrado['Mes_Pago'] == mes_seleccionado]
        
    if predio_seleccionado != "Todos los predios":
        df_filtrado = df_filtrado[df_filtrado['Numero de predio'] == predio_seleccionado]
        
    if propietario_seleccionado != "Todos los propietarios":
        df_filtrado = df_filtrado[df_filtrado['Nombre Completo'] == propietario_seleccionado]

    # ==========================================
    # INTERFAZ PRINCIPAL (Lo que ve la junta)
    # ==========================================
    st.title("📊 Tablero de Recaudo - Parcelación Venecia")
    st.markdown("---")
    
    # TARJETAS DE TOTALES (Métricas Macro)
    col1, col2, col3 = st.columns(3)
    
    recaudo_total = df_filtrado['valor_pagado'].sum()
    # Contamos cuántos predios distintos hicieron pago en este filtro
    pagos_unicos = df_filtrado['Numero de predio'].nunique() 
    total_transacciones = len(df_filtrado)
    
    col1.metric("💰 Recaudo Total", f"${recaudo_total:,.0f}")
    col2.metric("🏡 Predios que pagaron", pagos_unicos)
    col3.metric("🧾 Total de Transacciones", total_transacciones)
    
    st.markdown("---")
    
    # ESTADO DE CUENTA (Micro)
    st.subheader("📋 Detalle de Pagos Registrados")
    
    if len(df_filtrado) > 0:
        # Organizamos las columnas para que se vean más lógicas
        columnas_mostrar = ['fecha_pago', 'Numero de predio', 'Nombre Completo', 'valor_pagado', 'banco_destino', 'numero_referencia', 'Asociado?']
        
        # Mostramos la tabla interactiva
        st.dataframe(
            df_filtrado[columnas_mostrar].sort_values(by='fecha_pago', ascending=False), 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("No se encontraron pagos con los filtros seleccionados. (El propietario podría tener saldos pendientes en este mes).")

except Exception as e:
    st.error(f"Hubo un error al conectar con la base de datos: {e}")
    st.info("Verifica que las credenciales en Streamlit Secrets estén correctas.")
