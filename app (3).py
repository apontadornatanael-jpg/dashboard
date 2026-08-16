import io
import sqlite3
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Boletim de Sondagem Rotativa Interativo",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ESTILIZAÇÃO CSS (Design Neon / Glassmorphism Iluminado) ---
st.markdown(
    """
    <style>
    /* Fundo Geral */
    .stApp { 
        background: radial-gradient(circle at top left, #1a2035, #0d1117, #05070a); 
        color: #e6edf3; 
    }
    
    /* Card de Login e Containers */
    .login-box, .stCard {
        background: rgba(22, 27, 34, 0.85);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(88, 166, 255, 0.3);
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 0 25px rgba(56, 139, 253, 0.2);
    }
    
    /* Cards de Métricas */
    .stMetric {
        background: rgba(22, 27, 34, 0.85) !important;
        border: 1px solid rgba(88, 166, 255, 0.25) !important;
        border-radius: 14px !important;
        padding: 18px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), 0 0 12px rgba(56, 139, 253, 0.15);
    }
    
    /* Estilização da Planilha (Data Editor) */
    div[data-testid="stDataEditor"] {
        background: rgba(13, 17, 23, 0.9) !important;
        border: 1px solid rgba(88, 166, 255, 0.3) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 15px rgba(56, 139, 253, 0.15) !important;
    }
    
    /* Botões em Gradiente Neon */
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 0 12px rgba(46, 160, 67, 0.5) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        box-shadow: 0 0 22px rgba(46, 160, 67, 0.8) !important;
        transform: translateY(-2px);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- USUÁRIOS E AUTENTICAÇÃO ---
USUARIOS = {"admin": "1234", "natanael": "senha123"}

if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "usuario_atual" not in st.session_state:
    st.session_state["usuario_atual"] = ""

# --- TELA DE LOGIN ---
if not st.session_state["logado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown(
            "<h2 style='text-align: center; color: #58a6ff;'>✨ Acesso ao Sistema</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: #8b949e;'>Insira suas credenciais para gerenciar a Sondagem Rotativa</p>",
            unsafe_allow_html=True,
        )

        with st.form("form_login"):
            usuario = st.text_input("👤 Usuário")
            senha = st.text_input("🔑 Senha", type="password")
            btn_entrar = st.form_submit_button(
                "Entrar no Sistema", use_container_width=True
            )

            if btn_entrar:
                if usuario in USUARIOS and USUARIOS[usuario] == senha:
                    st.session_state["logado"] = True
                    st.session_state["usuario_atual"] = usuario
                    st.success(f"Bem-vindo, {usuario}!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- DASHBOARD PRINCIPAL ---
else:

    def init_db():
        conn = sqlite3.connect("sondagem.db")
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS avancos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                furo TEXT,
                de_m REAL,
                ate_m REAL,
                avanco_m REAL,
                recuperado_m REAL,
                porcentagem REAL
            )
        """)
        conn.commit()

        # População Inicial se o banco estiver vazio
        c.execute("SELECT COUNT(*) FROM avancos")
        if c.fetchone()[0] == 0:
            dados_iniciais = [
                ("14/04/2023", "DHAB 109", 44.10, 47.20, 3.10, 3.10, 100.0),
                ("14/04/2023", "DHAB 109", 47.20, 50.20, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 50.20, 53.30, 3.10, 3.10, 100.0),
                ("14/04/2023", "DHAB 109", 53.30, 56.45, 3.15, 3.15, 100.0),
                ("14/04/2023", "DHAB 109", 56.45, 59.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 59.45, 62.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 62.45, 65.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 65.45, 68.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 68.45, 71.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 71.45, 74.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 74.45, 77.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 77.45, 80.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 80.45, 83.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 83.45, 86.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 86.45, 89.45, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 89.45, 92.50, 3.05, 3.05, 100.0),
                ("14/04/2023", "DHAB 109", 92.50, 95.50, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 95.50, 98.50, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 98.50, 101.50, 3.00, 3.00, 100.0),
            ]
            c.executemany(
                """
                INSERT INTO avancos (data, furo, de_m, ate_m, avanco_m, recuperado_m, porcentagem)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                dados_iniciais,
            )
            conn.commit()
        conn.close()

    def carregar_dados():
        conn = sqlite3.connect("sondagem.db")
        df = pd.read_sql_query("SELECT * FROM avancos ORDER BY id ASC", conn)
        conn.close()
        return df

    def atualizar_banco_completo(df_novo):
        conn = sqlite3.connect("sondagem.db")
        df_novo.to_sql("avancos", conn, if_exists="replace", index=False)
        conn.close()

    # Inicialização do banco e dados
    init_db()
    df_dados = carregar_dados()

    # --- BARRA LATERAL (Sidebar) ---
    with st.sidebar:
        st.title("📌 Menu de Operações")
        st.write(f"Usuário ativo: **{st.session_state['usuario_atual']}**")

        if st.button("🚪 Sair / Logout", use_container_width=True):
            st.session_state["logado"] = False
            st.session_state["usuario_atual"] = ""
            st.rerun()

        st.markdown("---")
        st.subheader("➕ Adicionar Novo Avanço")

        with st.form("form_novo_avanco"):
            data_input = st.date_input("Data", datetime.today())
            furo_input = st.text_input("Furo", value="DHAB 109")
            de_input = st.number_input("De (m)", min_value=0.0, value=0.0, step=0.1)
            ate_input = st.number_input("Até (m)", min_value=0.0, value=0.0, step=0.1)
            recuperado_input = st.number_input(
                "Recuperado (m)", min_value=0.0, value=0.0, step=0.1
            )
            btn_salvar = st.form_submit_button("
