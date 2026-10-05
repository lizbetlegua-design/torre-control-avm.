import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Torre de Control AVM", layout="wide")
st.title("🚢 Torre de Control de Embarques — AVM Group")

# 1. Carga de datos desde archivos Excel
st.sidebar.header("Carga de Archivos Operativos")
file_logistics = st.sidebar.file_uploader("Cargar Excel AVM Logistics", type=["xlsx", "xls"])
file_aduanas = st.sidebar.file_uploader("Cargar Excel AVM Aduanera / Facturación", type=["xlsx", "xls"])

if file_logistics and file_aduanas:
    # Leer hojas de datos
    df_logistics = pd.read_excel(file_logistics)
    df_aduanas = pd.read_excel(file_aduanas)

    # Convertir columnas de fechas
    fechas_logistics = ['fecha_bk', 'fecha_envio_docs', 'fecha_zarpe']
    fechas_aduanas = ['fecha_recepcion_docs', 'fecha_dam', 'fecha_reporte_llenado', 'fecha_facturacion']

    for col in fechas_logistics:
        if col in df_logistics.columns:
            df_logistics[col] = pd.to_datetime(df_logistics[col])
            
    for col in fechas_aduanas:
        if col in df_aduanas.columns:
            df_aduanas[col] = pd.to_datetime(df_aduanas[col])

    # 2. Consolidación de datos (JOIN por ID_Booking / ID_File)
    df_master = pd.merge(df_logistics, df_aduanas, on="booking_id", how="outer", suffixes=('_log', '_adu'))

    # 3. Cálculo de KPIs y Control de SLAs
    if 'fecha_dam' in df_master.columns and 'fecha_recepcion_docs' in df_master.columns:
        df_master['horas_dam'] = (df_master['fecha_dam'] - df_master['fecha_recepcion_docs']).dt.total_seconds() / 3600
        df_master['sla_dam_ok'] = df_master['horas_dam'] <= 24

    # --- SECCIÓN DE KPIS SUPERIORES ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Embarques", len(df_master))
    col2.metric("En Proceso Aduanero", len(df_master[df_master['estado'] == 'ADUANA']) if 'estado' in df_master.columns else 0)
    col3.metric("Listos para Facturar", len(df_master[df_master['estado'] == 'PENDIENTE_FACTURACION']) if 'estado' in df_master.columns else 0)
    
    if 'sla_dam_ok' in df_master.columns:
        sla_cumplido = round((df_master['sla_dam_ok'].sum() / len(df_master)) * 100, 1) if len(df_master) > 0 else 0
        col4.metric("Cumplimiento SLA DAM (24h)", f"{sla_cumplido}%")

    st.markdown("---")

    # --- TABLA DETALLADA ---
    st.subheader("📋 Consolidado Maestro de Embarques")
    st.dataframe(df_master, use_container_width=True)

else:
    st.info("Por favor, sube los dos archivos Excel en la barra lateral para generar la Torre de Control.")
