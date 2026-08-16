
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Streamlit + Banco de Dados", layout="wide")

st.markdown('''
    <style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .stMetric {
        background: linear-gradient(135deg, #161b22 0%, #21262d 100%);
        padding: 15px; border-radius: 10px; border: 1px solid #30363d;
    }
    .stButton>button {
        background: linear-gradient(90deg, #238636 0%, #2ea043 100%);
        color: white; border-radius: 8px; border: none;
    }
    </style>
''', unsafe_allow_html=True)

# Inicializa banco SQLite local
def init_db():
    conn = sqlite3.connect('dados.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT,
            categoria TEXT,
            valor REAL,
            quantidade INTEGER,
            total REAL
        )
    ''')
    conn.commit()
    conn.close()

def salvar_registro(cat, val, qtd):
    conn = sqlite3.connect('dados.db')
    c = conn.cursor()
    dh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT INTO registros (data_hora, categoria, valor, quantidade, total) VALUES (?, ?, ?, ?, ?)',
              (dh, cat, val, qtd, val * qtd))
    conn.commit()
    conn.close()

def carregar_dados():
    conn = sqlite3.connect('dados.db')
    df = pd.read_sql_query("SELECT * FROM registros ORDER BY id DESC", conn)
    conn.close()
    return df

init_db()

st.title("⚡ Streamlit Dashboard (SQLite Local)")

col_form, col_dash = st.columns([1, 2])

with col_form:
    st.subheader("📝 Preenchimento de Dados")
    with st.form("form_sqlite"):
        categoria = st.selectbox("Categoria", ["Tech", "Vendas", "Marketing", "Suporte"])
        valor = st.number_input("Valor (R$)", min_value=10.0, max_value=5000.0, value=250.0)
        quantidade = st.slider("Quantidade", 1, 100, 5)
        enviado = st.form_submit_button("Salvar Registro")
        
        if enviado:
            salvar_registro(categoria, valor, quantidade)
            st.success("✅ Registro salvo com sucesso!")
            st.rerun()

with col_dash:
    st.subheader("📊 Métricas & Gráficos")
    df = carregar_dados()
    if not df.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Acumulado", f"R$ {df['total'].sum():,.2f}")
        m2.metric("Registros", len(df))
        m3.metric("Média por Item", f"R$ {df['valor'].mean():,.2f}")
        
        fig = px.bar(df, x="categoria", y="total", color="categoria", title="Total por Categoria")
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum dado salvo ainda. Preencha o formulário ao lado.")
