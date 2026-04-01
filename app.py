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
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2163/2163350.png", width=100)
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
        # Organizamos las columnas para que se vean más lógicas (incluyendo url_archivo)
        columnas_mostrar = ['fecha_pago', 'Numero de predio', 'Nombre Completo', 'valor_pagado', 'url_archivo', 'Asociado?']
        
        # Mostramos la tabla interactiva
        st.dataframe(
            df_filtrado[columnas_mostrar].sort_values(by='fecha_pago', ascending=False), 
            use_container_width=True,
            hide_index=True,
            column_config={
                "url_archivo": st.column_config.LinkColumn(
                    "📄 Comprobante",
                    help="Click para abrir el recibo original",
                    validate="^https://.*",
                    display_text="Ver Recibo"
                ),
                "valor_pagado": st.column_config.NumberColumn("Valor", format="$ %d")
            }
        )

        # ==========================================
        # 🔍 VISTA DE DETALLE (Visualización de Imagen)
        # ==========================================
        st.markdown("---")
        st.subheader("🔍 Inspección Visual de Recibos")
        
        # Creamos un selector para elegir un pago específico y ver su foto
        opciones_detalles = df_filtrado.apply(
            lambda x: f"{x['fecha_pago'].date()} - Predio {x['Numero de predio']} - {x['Nombre Completo']}", axis=1
        ).tolist()
        
        seleccion = st.selectbox("Selecciona un registro para visualizar el comprobante:", opciones_detalles)
        
        if seleccion:
            # Buscamos la URL del registro seleccionado
            indice_sel = opciones_detalles.index(seleccion)
            url_img = df_filtrado.iloc[indice_sel]['url_archivo']
            
            if pd.notna(url_img) and url_img:
                col_img, col_info = st.columns([2, 1])
                
                with col_img:
                    # Determinamos si es PDF o Imagen por la extensión
                    if str(url_img).lower().endswith(".pdf"):
                        st.info("Este comprobante es un PDF.")
                        st.markdown(f'<iframe src="{url_img}" width="100%" height="600px"></iframe>', unsafe_allow_html=True)
                    else:
                        st.image(url_img, caption=f"Comprobante: {seleccion}", use_container_width=True)
                
                with col_info:
                    st.write("### Acciones")
                    st.markdown(f'''
                        <a href="{url_img}" target="_blank">
                            <button style="
                                width: 100%;
                                background-color: #4CAF50;
                                color: white;
                                padding: 10px;
                                border: none;
                                border-radius: 5px;
                                cursor: pointer;">
                                📥 Descargar Comprobante
                            </button>
                        </a>
                    ''', unsafe_allow_html=True)
            else:
                st.warning("Este registro no tiene una imagen asociada en la base de datos.")

    else:
        st.warning("No se encontraron pagos con los filtros seleccionados. (El propietario podría tener saldos pendientes en este mes).")

except Exception as e:
    st.error(f"Hubo un error al conectar con la base de datos: {e}")
    st.info("Verifica que las credenciales en Streamlit Secrets estén correctas.")
