import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import date
import qrcode
from io import BytesIO

st.set_page_config(
    page_title="Sistema de Herramientas",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #f5f7fb;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

h1 {
    color: #0f172a;
    font-size: 42px !important;
    font-weight: 800 !important;
}

h2, h3 {
    color: #1e293b;
}

div[data-testid="stMetric"] {
    background: white;
    padding: 24px;
    border-radius: 18px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    border: 1px solid #e5e7eb;
}

div[data-testid="stForm"] {
    background: white;
    padding: 28px;
    border-radius: 20px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    border: 1px solid #e5e7eb;
}

div[data-testid="stDataFrame"] {
    background: white;
    border-radius: 18px;
    padding: 12px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.stButton button,
.stDownloadButton button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 10px 22px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

DB_NAME = "inventario_herramientas.db"

def conectar():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def crear_tablas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS herramientas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        categoria TEXT,
        cantidad_total INTEGER NOT NULL,
        cantidad_disponible INTEGER NOT NULL,
        estado TEXT DEFAULT 'Disponible'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solicitudes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_usuario TEXT NOT NULL,
        carrera TEXT,
        area TEXT,
        herramienta_id INTEGER,
        herramienta_nombre TEXT,
        cantidad INTEGER,
        fecha_solicitud TEXT,
        fecha_devolucion TEXT,
        motivo TEXT,
        estado TEXT DEFAULT 'Pendiente'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS danos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        herramienta_nombre TEXT,
        descripcion TEXT,
        fecha TEXT
    )
    """)

    conn.commit()
    conn.close()

def actualizar_base_datos():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(solicitudes)")
    columnas = [columna[1] for columna in cursor.fetchall()]

    if "carrera" not in columnas:
        cursor.execute("ALTER TABLE solicitudes ADD COLUMN carrera TEXT")

    conn.commit()
    conn.close()

crear_tablas()
actualizar_base_datos()

def obtener_herramientas():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM herramientas", conn)
    conn.close()
    return df

def obtener_herramientas_disponibles():
    conn = conectar()
    df = pd.read_sql_query("""
        SELECT * FROM herramientas
        WHERE cantidad_disponible > 0
        AND estado = 'Disponible'
    """, conn)
    conn.close()
    return df

def obtener_solicitudes():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM solicitudes ORDER BY id DESC", conn)
    conn.close()
    return df

def obtener_danos():
    conn = conectar()
    df = pd.read_sql_query("SELECT * FROM danos ORDER BY id DESC", conn)
    conn.close()
    return df

def tabla_solicitudes_visible(df):
    if df.empty:
        return df

    columnas = [
        "id",
        "nombre_usuario",
        "carrera",
        "area",
        "herramienta_nombre",
        "cantidad",
        "fecha_solicitud",
        "fecha_devolucion",
        "motivo"
    ]

    columnas_existentes = [col for col in columnas if col in df.columns]
    return df[columnas_existentes]

def generar_qr(link):
    img = qrcode.make(link)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

params = st.query_params
modo = params.get("modo", "admin")
herramienta_qr = params.get("herramienta", None)

if modo == "usuario":

    st.markdown("# Solicitud de herramienta")
    st.caption("Llena el formulario para solicitar una herramienta disponible.")

    herramientas = obtener_herramientas_disponibles()

    if herramientas.empty:
        st.warning("No hay herramientas disponibles por el momento.")
    else:
        nombres_herramientas = herramientas["nombre"].tolist()

        if herramienta_qr in nombres_herramientas:
            index_herramienta = nombres_herramientas.index(herramienta_qr)
        else:
            index_herramienta = 0

        with st.form("formulario_usuario"):
            herramienta_nombre = st.selectbox(
                "Herramienta disponible",
                nombres_herramientas,
                index=index_herramienta
            )

            herramienta_info = herramientas[herramientas["nombre"] == herramienta_nombre].iloc[0]

            st.info(f"Disponibles actualmente: {herramienta_info['cantidad_disponible']}")

            nombre_usuario = st.text_input("Nombre completo")

            carrera = st.selectbox(
                "Carrera",
                [
                    "Ingeniería en Datos e Inteligencia Artificial",
                    "Ingeniería en Sistemas",
                    "Ingeniería Mecatrónica",
                    "Ingeniería Industrial",
                    "Otra"
                ]
            )

            area = st.text_input("Área o laboratorio")

            cantidad = st.number_input(
                "Cantidad a solicitar",
                min_value=1,
                max_value=int(herramienta_info["cantidad_disponible"]),
                step=1
            )

            fecha_devolucion = st.date_input("Fecha de devolución")
            motivo = st.text_area("Motivo del préstamo")

            enviar = st.form_submit_button("Solicitar herramienta")

            if enviar:
                if nombre_usuario.strip() == "":
                    st.error("Debes escribir tu nombre.")
                elif area.strip() == "":
                    st.error("Debes escribir tu área o laboratorio.")
                elif motivo.strip() == "":
                    st.error("Debes escribir el motivo.")
                else:
                    conn = conectar()
                    cursor = conn.cursor()

                    cursor.execute("""
                    INSERT INTO solicitudes (
                        nombre_usuario,
                        carrera,
                        area,
                        herramienta_id,
                        herramienta_nombre,
                        cantidad,
                        fecha_solicitud,
                        fecha_devolucion,
                        motivo,
                        estado
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nombre_usuario,
                        carrera,
                        area,
                        int(herramienta_info["id"]),
                        herramienta_nombre,
                        int(cantidad),
                        str(date.today()),
                        str(fecha_devolucion),
                        motivo,
                        "Pendiente"
                    ))

                    conn.commit()
                    conn.close()

                    st.success("Solicitud enviada correctamente.")
                    st.info("Espera a que el administrador apruebe tu solicitud.")

else:

    st.sidebar.markdown("# 🔧 Sistema")
    st.sidebar.markdown("### Inventario de herramientas")

    menu = st.sidebar.radio(
        "Menú",
        [
            "Dashboard",
            "Inventario",
            "Solicitudes",
            "Devoluciones",
            "Herramientas dañadas",
            "Reportes",
            "QR"
        ]
    )

    if menu == "Dashboard":

        st.markdown("# Dashboard general")
        st.caption("Resumen operativo del inventario, préstamos y solicitudes.")

        herramientas = obtener_herramientas()
        solicitudes = obtener_solicitudes()
        danos = obtener_danos()

        total_herramientas = herramientas["cantidad_total"].sum() if not herramientas.empty else 0
        disponibles = herramientas["cantidad_disponible"].sum() if not herramientas.empty else 0
        pendientes = solicitudes[solicitudes["estado"] == "Pendiente"].shape[0] if not solicitudes.empty else 0
        aprobadas = solicitudes[solicitudes["estado"] == "Aprobada"].shape[0] if not solicitudes.empty else 0
        danadas = danos.shape[0] if not danos.empty else 0

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Herramientas", total_herramientas)
        col2.metric("Disponibles", disponibles)
        col3.metric("Pendientes", pendientes)
        col4.metric("Préstamos activos", aprobadas)
        col5.metric("Daños", danadas)

        st.divider()

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            if not solicitudes.empty:
                conteo = solicitudes["herramienta_nombre"].value_counts().reset_index()
                conteo.columns = ["Herramienta", "Solicitudes"]

                fig = px.bar(
                    conteo,
                    x="Herramienta",
                    y="Solicitudes",
                    title="Herramientas más solicitadas"
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aún no hay solicitudes para graficar.")

        with col_g2:
            if not herramientas.empty:
                estado_df = herramientas.groupby("estado")["cantidad_total"].sum().reset_index()

                fig2 = px.pie(
                    estado_df,
                    names="estado",
                    values="cantidad_total",
                    title="Estado de herramientas",
                    hole=0.45
                )

                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Aún no hay herramientas registradas.")

        st.subheader("Últimas solicitudes")
        st.dataframe(tabla_solicitudes_visible(solicitudes), use_container_width=True)

    elif menu == "Inventario":

        st.markdown("# Inventario")
        st.caption("Registro de herramientas y control de stock.")

        with st.form("form_herramienta"):
            nombre = st.text_input("Nombre de la herramienta")
            categoria = st.text_input("Categoría")
            cantidad = st.number_input("Cantidad total", min_value=1, step=1)
            estado = st.selectbox("Estado", ["Disponible", "Mantenimiento", "Dañada"])

            guardar = st.form_submit_button("Guardar herramienta")

            if guardar:
                if nombre.strip() == "":
                    st.error("Escribe el nombre de la herramienta.")
                else:
                    conn = conectar()
                    cursor = conn.cursor()

                    cursor.execute("""
                    INSERT INTO herramientas (
                        nombre,
                        categoria,
                        cantidad_total,
                        cantidad_disponible,
                        estado
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        nombre,
                        categoria,
                        int(cantidad),
                        int(cantidad),
                        estado
                    ))

                    conn.commit()
                    conn.close()

                    st.success("Herramienta registrada correctamente.")

        st.subheader("Herramientas registradas")
        st.dataframe(obtener_herramientas(), use_container_width=True)

    elif menu == "Solicitudes":

        st.markdown("# Solicitudes")
        st.caption("Aprueba o rechaza las solicitudes enviadas por los usuarios.")

        solicitudes = obtener_solicitudes()

        if solicitudes.empty:
            st.info("No hay solicitudes registradas.")
        else:
            st.dataframe(tabla_solicitudes_visible(solicitudes), use_container_width=True)

            pendientes = solicitudes[solicitudes["estado"] == "Pendiente"]

            if pendientes.empty:
                st.success("No hay solicitudes pendientes.")
            else:
                st.subheader("Gestionar solicitud")

                solicitud_id = st.selectbox(
                    "Selecciona una solicitud pendiente",
                    pendientes["id"]
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Aprobar solicitud"):
                        solicitud = pendientes[pendientes["id"] == solicitud_id].iloc[0]

                        conn = conectar()
                        cursor = conn.cursor()

                        cursor.execute("""
                        SELECT cantidad_disponible 
                        FROM herramientas 
                        WHERE id = ?
                        """, (int(solicitud["herramienta_id"]),))

                        disponible = cursor.fetchone()[0]

                        if int(solicitud["cantidad"]) <= disponible:
                            nueva_cantidad = disponible - int(solicitud["cantidad"])

                            cursor.execute("""
                            UPDATE herramientas
                            SET cantidad_disponible = ?
                            WHERE id = ?
                            """, (
                                nueva_cantidad,
                                int(solicitud["herramienta_id"])
                            ))

                            cursor.execute("""
                            UPDATE solicitudes
                            SET estado = 'Aprobada'
                            WHERE id = ?
                            """, (int(solicitud_id),))

                            conn.commit()
                            st.success("Solicitud aprobada y stock actualizado.")
                        else:
                            st.error("No hay suficiente stock disponible.")

                        conn.close()

                with col2:
                    if st.button("Rechazar solicitud"):
                        conn = conectar()
                        cursor = conn.cursor()

                        cursor.execute("""
                        UPDATE solicitudes
                        SET estado = 'Rechazada'
                        WHERE id = ?
                        """, (int(solicitud_id),))

                        conn.commit()
                        conn.close()

                        st.warning("Solicitud rechazada.")

    elif menu == "Devoluciones":

        st.markdown("# Devoluciones")
        st.caption("Registra herramientas devueltas y actualiza el stock.")

        solicitudes = obtener_solicitudes()
        activos = solicitudes[solicitudes["estado"] == "Aprobada"]

        if activos.empty:
            st.info("No hay préstamos activos.")
        else:
            prestamo_id = st.selectbox(
                "Selecciona préstamo a devolver",
                activos["id"]
            )

            if st.button("Registrar devolución"):
                prestamo = activos[activos["id"] == prestamo_id].iloc[0]

                conn = conectar()
                cursor = conn.cursor()

                cursor.execute("""
                UPDATE herramientas
                SET cantidad_disponible = cantidad_disponible + ?
                WHERE id = ?
                """, (
                    int(prestamo["cantidad"]),
                    int(prestamo["herramienta_id"])
                ))

                cursor.execute("""
                UPDATE solicitudes
                SET estado = 'Devuelta'
                WHERE id = ?
                """, (int(prestamo_id),))

                conn.commit()
                conn.close()

                st.success("Devolución registrada correctamente.")

        st.subheader("Préstamos activos")
        st.dataframe(tabla_solicitudes_visible(activos), use_container_width=True)

    elif menu == "Herramientas dañadas":

        st.markdown("# Herramientas dañadas")
        st.caption("Registro de herramientas dañadas o en mal estado.")

        herramientas = obtener_herramientas()

        if herramientas.empty:
            st.warning("Primero registra herramientas.")
        else:
            with st.form("form_dano"):
                herramienta = st.selectbox("Herramienta dañada", herramientas["nombre"])
                descripcion = st.text_area("Descripción del daño")
                fecha_dano = st.date_input("Fecha del daño", date.today())

                registrar = st.form_submit_button("Registrar daño")

                if registrar:
                    conn = conectar()
                    cursor = conn.cursor()

                    cursor.execute("""
                    INSERT INTO danos (
                        herramienta_nombre,
                        descripcion,
                        fecha
                    )
                    VALUES (?, ?, ?)
                    """, (
                        herramienta,
                        descripcion,
                        str(fecha_dano)
                    ))

                    cursor.execute("""
                    UPDATE herramientas
                    SET estado = 'Dañada'
                    WHERE nombre = ?
                    """, (herramienta,))

                    conn.commit()
                    conn.close()

                    st.success("Daño registrado correctamente.")

        st.subheader("Historial de daños")
        st.dataframe(obtener_danos(), use_container_width=True)

    elif menu == "Reportes":

        st.markdown("# Reportes")
        st.caption("Análisis de uso de herramientas y daños registrados.")

        solicitudes = obtener_solicitudes()
        danos = obtener_danos()

        if not solicitudes.empty:
            conteo = solicitudes["herramienta_nombre"].value_counts().reset_index()
            conteo.columns = ["Herramienta", "Solicitudes"]

            fig = px.bar(
                conteo,
                x="Herramienta",
                y="Solicitudes",
                title="Herramientas más solicitadas"
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aún no hay solicitudes.")

        if not danos.empty:
            conteo_danos = danos["herramienta_nombre"].value_counts().reset_index()
            conteo_danos.columns = ["Herramienta", "Daños"]

            fig2 = px.pie(
                conteo_danos,
                names="Herramienta",
                values="Daños",
                title="Herramientas con más daños",
                hole=0.45
            )

            st.plotly_chart(fig2, use_container_width=True)

    elif menu == "QR":

        st.markdown("# Generador de QR")
        st.caption("Crea códigos QR para que los usuarios soliciten herramientas.")

        url_app = st.text_input(
            "Link público de la app",
            value="https://sistema-herramientas-upq.streamlit.app"
        )

        if url_app:
            link_usuario = f"{url_app}/?modo=usuario"

            st.subheader("QR general para usuarios")
            st.code(link_usuario)

            qr_general = generar_qr(link_usuario)
            st.image(qr_general, width=260)

            st.download_button(
                "Descargar QR general",
                data=qr_general,
                file_name="qr_general_usuario.png",
                mime="image/png"
            )

            st.divider()

            st.subheader("QR por herramienta")

            herramientas = obtener_herramientas()

            if herramientas.empty:
                st.warning("Primero registra herramientas.")
            else:
                herramienta_nombre = st.selectbox(
                    "Selecciona herramienta",
                    herramientas["nombre"]
                )

                link_herramienta = f"{url_app}/?modo=usuario&herramienta={herramienta_nombre}"

                st.code(link_herramienta)

                qr_herramienta = generar_qr(link_herramienta)
                st.image(qr_herramienta, width=260)

                st.download_button(
                    "Descargar QR de herramienta",
                    data=qr_herramienta,
                    file_name=f"qr_{herramienta_nombre}.png",
                    mime="image/png"
                )