import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Sistema de Herramientas",
    layout="wide"
)

# SIDEBAR
st.sidebar.title("🔧 Sistema")
st.sidebar.markdown("### Inventario de Herramientas")

menu = st.sidebar.radio(
    "Menú",
    [
        "Dashboard",
        "Inventario",
        "Préstamos",
        "Alertas",
        "Reportes"
    ]
)

# DATOS DEMO
herramientas = pd.DataFrame({
    "Herramienta": [
        "Taladro",
        "Esmeril",
        "Martillo",
        "Juego de llaves",
        "Flexómetro"
    ],
    "Solicitudes": [23, 18, 12, 15, 9]
})

estado = pd.DataFrame({
    "Estado": [
        "Disponibles",
        "Prestadas",
        "Mantenimiento",
        "Dañadas"
    ],
    "Cantidad": [45, 27, 9, 5]
})

prestamos = pd.DataFrame({
    "Herramienta": [
        "Taladro",
        "Esmeril",
        "Juego de llaves"
    ],
    "Solicitante": [
        "Juan Pérez",
        "María López",
        "Carlos Ramírez"
    ],
    "Fecha devolución": [
        "20/05/2026",
        "21/05/2026",
        "22/05/2026"
    ]
})

# DASHBOARD
if menu == "Dashboard":

    st.title("📊 Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Herramientas", "128")
    col2.metric("Disponibles", "45")
    col3.metric("Prestadas", "27")
    col4.metric("Retrasadas", "5")

    st.divider()

    col5, col6 = st.columns(2)

    with col5:
        fig = px.bar(
            herramientas,
            x="Herramienta",
            y="Solicitudes",
            title="Herramientas más solicitadas"
        )

        st.plotly_chart(fig, use_container_width=True)

    with col6:
        fig2 = px.pie(
            estado,
            names="Estado",
            values="Cantidad",
            title="Estado de herramientas"
        )

        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("📋 Préstamos activos")
    st.dataframe(prestamos, use_container_width=True)

# INVENTARIO
elif menu == "Inventario":

    st.title("📦 Inventario")

    st.dataframe(herramientas, use_container_width=True)

# PRÉSTAMOS
elif menu == "Préstamos":

    st.title("📤 Solicitar herramienta")

    herramientas_disponibles = [
        "Taladro",
        "Esmeril",
        "Juego de llaves",
        "Flexómetro"
    ]

    with st.form("solicitud"):

        nombre = st.text_input("Nombre del solicitante")

        area = st.text_input("Área o departamento")

        herramienta = st.selectbox(
            "Herramienta",
            herramientas_disponibles
        )

        cantidad = st.number_input(
            "Cantidad",
            min_value=1,
            step=1
        )

        fecha = st.date_input("Fecha de devolución")

        motivo = st.text_area("Motivo del préstamo")

        enviar = st.form_submit_button("Solicitar herramienta")

        if enviar:

            st.success("✅ Solicitud enviada correctamente")

            st.write("### Resumen")

            st.write("👤 Usuario:", nombre)
            st.write("🏢 Área:", area)
            st.write("🔧 Herramienta:", herramienta)
            st.write("📦 Cantidad:", cantidad)
            st.write("📅 Fecha devolución:", fecha)
            st.write("📝 Motivo:", motivo)

# ALERTAS
elif menu == "Alertas":

    st.title("🚨 Alertas")

    st.error("Taladro retrasado")
    st.warning("Esmeril próximo a vencer")

# REPORTES
elif menu == "Reportes":

    st.title("📈 Reportes")

    st.dataframe(herramientas)