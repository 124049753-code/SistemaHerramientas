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

DB_NAME = "inventario_herramientas.db"

# ---------------- BASE DE DATOS ----------------

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
        area TEXT,
        herramienta_id INTEGER,
        herramienta_nombre TEXT,
        cantidad INTEGER,
        fecha_solicitud TEXT,
        fecha_devolucion TEXT,
        motivo TEXT,
        estado TEXT DEFAULT 'Pendiente',
        FOREIGN KEY(herramienta_id) REFERENCES herramientas(id)
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

crear_tablas()

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

def generar_qr(link):
    img = qrcode.make(link)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

# ---------------- PARÁMETROS QR ----------------

params = st.query_params
modo = params.get("modo", "admin")
herramienta_qr = params.get("herramienta", None)

# ---------------- MODO USUARIO ----------------

if modo == "usuario":

    st.title("🔧 Solicitud de herramienta")
    st.write("Llena el formulario para solicitar una herramienta.")

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

            st.info(f"Disponibles: {herramienta_info['cantidad_disponible']}")

            nombre_usuario = st.text_input("Nombre completo")
            area = st.text_input("Área o departamento")

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
                    st.error("Debes escribir tu área.")
                elif motivo.strip() == "":
                    st.error("Debes escribir el motivo.")
                else:
                    conn = conectar()
                    cursor = conn.cursor()

                    cursor.execute("""
                    INSERT INTO solicitudes (
                        nombre_usuario,
                        area,
                        herramienta_id,
                        herramienta_nombre,
                        cantidad,
                        fecha_solicitud,
                        fecha_devolucion,
                        motivo,
                        estado
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        nombre_usuario,
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

                    st.success("✅ Solicitud enviada correctamente.")
                    st.write("Espera a que el administrador apruebe tu solicitud.")

# ---------------- MODO ADMIN ----------------

else:

    st.sidebar.title("🔐 Panel administrador")

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

    # ---------------- DASHBOARD ----------------

    if menu == "Dashboard":

        st.title("📊 Dashboard general")

        herramientas = obtener_herramientas()
        solicitudes = obtener_solicitudes()
        danos = obtener_danos()

        total_herramientas = herramientas["cantidad_total"].sum() if not herramientas.empty else 0
        disponibles = herramientas["cantidad_disponible"].sum() if not herramientas.empty else 0
        pendientes = solicitudes[solicitudes["estado"] == "Pendiente"].shape[0] if not solicitudes.empty else 0
        aprobadas = solicitudes[solicitudes["estado"] == "Aprobada"].shape[0] if not solicitudes.empty else 0
        danadas = danos.shape[0] if not danos.empty else 0

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Total herramientas", total_herramientas)
        col2.metric("Disponibles", disponibles)
        col3.metric("Solicitudes pendientes", pendientes)
        col4.metric("Préstamos activos", aprobadas)
        col5.metric("Daños registrados", danadas)

        st.divider()

        st.subheader("Últimas solicitudes")
        st.dataframe(solicitudes, use_container_width=True)

    # ---------------- INVENTARIO ----------------

    elif menu == "Inventario":

        st.title("📦 Inventario de herramientas")

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

    # ---------------- SOLICITUDES ----------------

    elif menu == "Solicitudes":

        st.title("📩 Solicitudes de herramientas")

        solicitudes = obtener_solicitudes()

        if solicitudes.empty:
            st.info("No hay solicitudes registradas.")
        else:
            st.dataframe(solicitudes, use_container_width=True)

            solicitudes_pendientes = solicitudes[solicitudes["estado"] == "Pendiente"]

            if solicitudes_pendientes.empty:
                st.success("No hay solicitudes pendientes.")
            else:
                st.subheader("Aprobar o rechazar solicitud")

                solicitud_id = st.selectbox(
                    "Selecciona una solicitud pendiente",
                    solicitudes_pendientes["id"]
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Aprobar solicitud"):
                        solicitud = solicitudes_pendientes[solicitudes_pendientes["id"] == solicitud_id].iloc[0]

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
                            """, (nueva_cantidad, int(solicitud["herramienta_id"])))

                            cursor.execute("""
                            UPDATE solicitudes
                            SET estado = 'Aprobada'
                            WHERE id = ?
                            """, (int(solicitud_id),))

                            conn.commit()
                            st.success("Solicitud aprobada y stock actualizado.")
                        else:
                            st.error("No hay suficiente cantidad disponible.")

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

    # ---------------- DEVOLUCIONES ----------------

    elif menu == "Devoluciones":

        st.title("↩️ Registrar devolución")

        solicitudes = obtener_solicitudes()
        prestamos_activos = solicitudes[solicitudes["estado"] == "Aprobada"]

        if prestamos_activos.empty:
            st.info("No hay préstamos activos.")
        else:
            prestamo_id = st.selectbox(
                "Selecciona préstamo a devolver",
                prestamos_activos["id"]
            )

            if st.button("Registrar devolución"):
                prestamo = prestamos_activos[prestamos_activos["id"] == prestamo_id].iloc[0]

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

                st.success("Devolución registrada y stock actualizado.")

        st.subheader("Préstamos activos")
        st.dataframe(prestamos_activos, use_container_width=True)

    # ---------------- DAÑOS ----------------

    elif menu == "Herramientas dañadas":

        st.title("🛠️ Herramientas dañadas")

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

    # ---------------- REPORTES ----------------

    elif menu == "Reportes":

        st.title("📈 Reportes")

        solicitudes = obtener_solicitudes()
        danos = obtener_danos()

        if solicitudes.empty:
            st.info("Aún no hay solicitudes para generar reportes.")
        else:
            st.subheader("Herramientas más solicitadas")

            conteo = solicitudes["herramienta_nombre"].value_counts().reset_index()
            conteo.columns = ["Herramienta", "Solicitudes"]

            fig = px.bar(
                conteo,
                x="Herramienta",
                y="Solicitudes",
                title="Herramientas más solicitadas"
            )

            st.plotly_chart(fig, use_container_width=True)

        if not danos.empty:
            st.subheader("Herramientas con más daños")

            conteo_danos = danos["herramienta_nombre"].value_counts().reset_index()
            conteo_danos.columns = ["Herramienta", "Daños"]

            fig2 = px.pie(
                conteo_danos,
                names="Herramienta",
                values="Daños",
                title="Herramientas dañadas"
            )

            st.plotly_chart(fig2, use_container_width=True)

    # ---------------- QR ----------------

    elif menu == "QR":

        st.title("🔳 Generar QR para usuarios")

        st.write("Este QR abre solo el formulario para solicitar herramientas.")

        url_app = st.text_input(
            "Pega aquí el link público de tu app",
            placeholder="https://tu-app.streamlit.app"
        )

        if url_app:
            link_usuario = f"{url_app}/?modo=usuario"

            st.subheader("QR general")
            st.write(link_usuario)

            qr_general = generar_qr(link_usuario)
            st.image(qr_general, width=250)

            st.download_button(
                "Descargar QR general",
                data=qr_general,
                file_name="qr_general.png",
                mime="image/png"
            )

            st.divider()

            st.subheader("QR por herramienta")

            herramientas = obtener_herramientas()

            if herramientas.empty:
                st.warning("Primero registra herramientas.")
            else:
                herramienta_qr_nombre = st.selectbox(
                    "Selecciona herramienta",
                    herramientas["nombre"]
                )

                link_herramienta = f"{url_app}/?modo=usuario&herramienta={herramienta_qr_nombre}"

                st.write(link_herramienta)

                qr_herramienta = generar_qr(link_herramienta)
                st.image(qr_herramienta, width=250)

                st.download_button(
                    "Descargar QR de herramienta",
                    data=qr_herramienta,
                    file_name=f"qr_{herramienta_qr_nombre}.png",
                    mime="image/png"
                )