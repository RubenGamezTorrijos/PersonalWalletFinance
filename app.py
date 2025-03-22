# Importar las bibliotecas necesarias
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3
import psycopg2
import pymysql

# Configuración inicial de la página
st.set_page_config(page_title="Personal Budget", page_icon="💰", layout="wide")

# Título de la aplicación
st.title("💰 Personal Wallet Finance")
st.markdown("Una herramienta para gestionar tus ingresos, gastos y ahorros mensuales.")

# Inicializar el historial de registros (usando Session State)
if "history" not in st.session_state:
    st.session_state.history = []

# Configuración global (moneda y tema)
if "currency" not in st.session_state:
    st.session_state.currency = "$"
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Función para conectar a la base de datos
def connect_to_db(db_type, db_params):
    try:
        if db_type == "SQLite":
            conn = sqlite3.connect(db_params["dbname"])
        elif db_type == "PostgreSQL":
            conn = psycopg2.connect(
                dbname=db_params["dbname"],
                user=db_params["user"],
                password=db_params["password"],
                host=db_params["host"],
                port=db_params["port"],
            )
        elif db_type == "MySQL":
            conn = pymysql.connect(
                host=db_params["host"],
                user=db_params["user"],
                password=db_params["password"],
                database=db_params["dbname"],
                port=int(db_params["port"]),
            )
        return conn
    except Exception as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None

# Función para guardar un registro en el historial
def save_record(date, income_categories, expense_categories):
    record = {
        "Fecha": date,
        "Ingresos": income_categories,
        "Gastos": expense_categories,
        "Ahorro": sum(income_categories.values()) - sum(expense_categories.values()),
    }
    st.session_state.history.append(record)

    # Guardar en la base de datos si está configurada
    if "db_connection" in st.session_state and st.session_state.db_connection:
        conn = st.session_state.db_connection
        cursor = conn.cursor()
        for category, amount in income_categories.items():
            cursor.execute(
                "INSERT INTO records (date, type, category, amount) VALUES (%s, %s, %s, %s)",
                (date, "Ingreso", category, amount),
            )
        for category, amount in expense_categories.items():
            cursor.execute(
                "INSERT INTO records (date, type, category, amount) VALUES (%s, %s, %s, %s)",
                (date, "Gasto", category, amount),
            )
        conn.commit()

# Barra lateral: Formulario para ingresar datos
with st.sidebar:
    st.header("📝 Introduce tus datos")

    # Fecha del registro
    record_date = st.date_input("Fecha del registro", value=datetime.today())

    # Ingresos personalizados
    st.subheader("Ingresos")
    num_income_categories = st.number_input("Número de categorías de ingreso", min_value=1, step=1)
    income_categories = {}
    for i in range(num_income_categories):
        col1, col2 = st.columns(2)
        with col1:
            category_name = st.text_input(f"Categoría de ingreso {i+1}", value=f"Ingreso {i+1}")
        with col2:
            amount = st.number_input(f"Monto para {category_name}", min_value=0.0, step=100.0)
        income_categories[category_name] = amount

    # Gastos personalizados
    st.subheader("Gastos")
    num_expense_categories = st.number_input("Número de categorías de gasto", min_value=1, step=1)
    expense_categories = {}
    for i in range(num_expense_categories):
        col1, col2 = st.columns(2)
        with col1:
            category_name = st.text_input(f"Categoría de gasto {i+1}", value=f"Gasto {i+1}")
        with col2:
            amount = st.number_input(f"Monto para {category_name}", min_value=0.0, step=50.0)
        expense_categories[category_name] = amount

    # Botón para enviar el formulario
    with st.form(key="budget_form"):
        submit_button = st.form_submit_button(label="Guardar Registro")

    if submit_button:
        save_record(record_date, income_categories, expense_categories)
        st.success("Registro guardado correctamente.")

# Página principal con pestañas
tab1, tab2, tab3, tab4 = st.tabs(["📊 Resumen", "📚 Historial", "💡 Consejos Financieros", "⚙️ Ajustes"])

# Pestaña 1: Resumen
with tab1:
    st.header("📊 Resumen de Resultados")
    if st.session_state.history:
        # Obtener el último registro
        last_record = st.session_state.history[-1]
        total_income = sum(last_record["Ingresos"].values())
        total_expenses = sum(last_record["Gastos"].values())
        net_savings = last_record["Ahorro"]

        # Mostrar métricas
        st.metric("Ingresos Totales", f"{st.session_state.currency}{total_income:.2f}")
        st.metric("Gastos Totales", f"{st.session_state.currency}{total_expenses:.2f}")
        st.metric("Ahorro Neto", f"{st.session_state.currency}{net_savings:.2f}", delta=f"{net_savings / total_income * 100:.1f}%" if total_income > 0 else "0%")

        # Gráficos de barras para ingresos y gastos
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Ingresos por Categoría")
            fig_income, ax_income = plt.subplots(figsize=(6, 4))
            categories_income = list(last_record["Ingresos"].keys())
            values_income = list(last_record["Ingresos"].values())
            ax_income.bar(categories_income, values_income, color="green")
            ax_income.set_title("Ingresos por Categoría")
            ax_income.set_ylabel(f"Monto ({st.session_state.currency})")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig_income)

        with col2:
            st.subheader("Gastos por Categoría")
            fig_expenses, ax_expenses = plt.subplots(figsize=(6, 4))
            categories_expenses = list(last_record["Gastos"].keys())
            values_expenses = list(last_record["Gastos"].values())
            ax_expenses.bar(categories_expenses, values_expenses, color="red")
            ax_expenses.set_title("Gastos por Categoría")
            ax_expenses.set_ylabel(f"Monto ({st.session_state.currency})")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig_expenses)
    else:
        st.info("No hay registros disponibles. Agrega un registro en la barra lateral.")

# Pestaña 2: Historial
with tab2:
    st.header("📚 Historial de Registros")
    if st.session_state.history or ("db_connection" in st.session_state and st.session_state.db_connection):
        # Convertir el historial a un DataFrame
        history_data = []
        if "db_connection" in st.session_state and st.session_state.db_connection:
            conn = st.session_state.db_connection
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM records")
            rows = cursor.fetchall()
            for row in rows:
                history_data.append({"ID": row[0], "Fecha": row[1], "Tipo": row[2], "Categoría": row[3], "Monto": row[4]})
        else:
            for record in st.session_state.history:
                for category, amount in record["Ingresos"].items():
                    history_data.append({"Fecha": record["Fecha"], "Tipo": "Ingreso", "Categoría": category, "Monto": amount})
                for category, amount in record["Gastos"].items():
                    history_data.append({"Fecha": record["Fecha"], "Tipo": "Gasto", "Categoría": category, "Monto": amount})
        history_df = pd.DataFrame(history_data)

        # Mostrar tabla editable
        st.subheader("Editar/Eliminar Registros")
        edited_history = st.data_editor(history_df, num_rows="dynamic")

        # Guardar cambios en la base de datos
        if st.button("Guardar Cambios en el Historial"):
            if "db_connection" in st.session_state and st.session_state.db_connection:
                conn = st.session_state.db_connection
                cursor = conn.cursor()
                for index, row in edited_history.iterrows():
                    if "ID" in row:
                        cursor.execute(
                            "UPDATE records SET date=%s, type=%s, category=%s, amount=%s WHERE id=%s",
                            (row["Fecha"], row["Tipo"], row["Categoría"], row["Monto"], row["ID"]),
                        )
                conn.commit()
                st.success("Cambios guardados en la base de datos.")
            else:
                st.warning("No hay conexión a la base de datos. Los cambios no se guardarán.")

        # Gráfico de donut: Distribución total de ingresos, gastos y ahorro
        total_income = history_df[history_df["Tipo"] == "Ingreso"]["Monto"].sum()
        total_expenses = history_df[history_df["Tipo"] == "Gasto"]["Monto"].sum()
        total_savings = total_income - total_expenses

        fig_donut, ax_donut = plt.subplots(figsize=(6, 6))
        labels = ["Ingresos", "Gastos", "Ahorro"]
        sizes = [total_income, total_expenses, total_savings]
        colors_donut = ["lightgreen", "orange", "blue"]
        ax_donut.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors_donut, wedgeprops=dict(width=0.3))
        ax_donut.set_title("Distribución Total de Finanzas")
        st.pyplot(fig_donut)

        # Tabla con el historial completo
        st.dataframe(history_df.style.format({
            "Monto": f"{st.session_state.currency}{{:.2f}}",
        }))
    else:
        st.info("No hay registros en el historial. Agrega un registro en la barra lateral.")

# Pestaña 3: Consejos Financieros
with tab3:
    st.header("💡 Consejos Financieros")
    if st.session_state.history:
        # Obtener el último ahorro neto
        last_savings = st.session_state.history[-1]["Ahorro"]

        if last_savings > 0:
            st.success("¡Estás ahorrando! Considera invertir una parte de tus ahorros para maximizar tu crecimiento financiero.")
        elif last_savings == 0:
            st.warning("No estás ahorrando este mes. Revisa tus gastos para identificar áreas donde puedas reducir.")
        else:
            st.error("Tus gastos superan tus ingresos. Es importante revisar tus hábitos de gasto y ajustar tu presupuesto.")
    else:
        st.info("No hay registros disponibles. Agrega un registro en la barra lateral.")

# Pestaña 4: Ajustes
with tab4:
    st.header("⚙️ Ajustes")

    # Configuración de la base de datos
    st.subheader("Base de Datos")
    db_type = st.selectbox("Tipo de Base de Datos", ["SQLite", "PostgreSQL", "MySQL"])
    db_params = {}
    if db_type == "SQLite":
        db_params["dbname"] = st.text_input("Ruta de la base de datos (SQLite)", value="personal_budget.db")
    else:
        db_params["dbname"] = st.text_input("Nombre de la base de datos", value="personal_budget")
        db_params["user"] = st.text_input("Usuario", value="postgres" if db_type == "PostgreSQL" else "root")
        db_params["password"] = st.text_input("Contraseña", type="password")
        db_params["host"] = st.text_input("Host", value="localhost")
        db_params["port"] = st.text_input("Puerto", value="5432" if db_type == "PostgreSQL" else "3306")

    if st.button("Conectar a la Base de Datos"):
        conn = connect_to_db(db_type, db_params)
        if conn:
            st.session_state.db_connection = conn
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    id SERIAL PRIMARY KEY,
                    date TEXT,
                    type TEXT,
                    category TEXT,
                    amount REAL
                )
            """)
            conn.commit()
            st.success("Conexión exitosa a la base de datos.")

    # Cambiar la moneda
    currency_options = {"Dólar ($)": "$", "Euro (€)": "€", "Libra (£)": "£"}
    selected_currency = st.selectbox("Selecciona tu moneda", list(currency_options.keys()))
    st.session_state.currency = currency_options[selected_currency]

    # Cambiar el tema
    theme_options = {"Claro": "light", "Oscuro": "dark"}
    selected_theme = st.selectbox("Selecciona el tema", list(theme_options.keys()))
    st.session_state.theme = theme_options[selected_theme]
    st.write("El tema se aplicará automáticamente al recargar la página.")

    # Botón para guardar configuración
    if st.button("Guardar Configuración"):
        st.success("Configuración guardada correctamente.")

# Pie de página
st.markdown("---")
st.markdown("Desarrollado por Rubén Gámez Torrijos | Powered by Streamlit")
