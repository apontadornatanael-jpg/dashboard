import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import os
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Portal & Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- ESTILIZAÇÃO CSS (Design Iluminado / Glassmorphism) ---
st.markdown("""
    <style>
    /* Fundo Principal */
    .stApp {
        background: radial-gradient(circle at top left, #1a2035, #0d1117, #05070a);
        color: #e6edf3;
    }
    
    /* Card de Login Iluminado */
    .login-box {
        background: rgba(22, 27, 34, 0.75);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(88, 166, 255, 0.3);
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 0 25px rgba(56, 139, 253, 0.25);
        margin-top: 50px;
    }
    
    /* Métricas Iluminadas (Cards) */
    .stMetric {
        background: rgba(22, 27, 34, 0.8) !important;
        border: 1px solid rgba(88, 166, 255, 0.2) !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 10px rgba(56, 139, 253, 0.15);
    }
    
    /* Botões em Gradiente Neon */
    .stButton>button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 0 12px rgba(46, 160, 67, 0.5) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(46, 160, 67, 0.8) !important;
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# --- USUÁRIOS E SENHAS CADASTRADOS ---
USUARIOS = {
    "admin": "1234",
    "natanael": "senha123"
}

# --- CONTROLE DE SESSÃO DO LOGIN ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False
if "usuario_atual" not in st.session_state:
    st.session_state["usuario_atual"] = ""

# --- TELA DE LOGIN ---
if not st.session_state["logado"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #58a6ff;'>✨ Acesso ao Sistema</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8b949e;'>Insira suas credenciais para acessar o Dashboard</p>", unsafe_allow_html=True)
        
        with st.form("form_login"):
            usuario = st.text_input("👤 Usuário")
            senha = st.text_input("🔑 Senha", type="password")
            btn_entrar = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            
            if btn_entrar:
                if usuario in USUARIOS and USUARIOS[usuario] == senha:
                    st.session_state["logado"] = True
                    st.session_state["usuario_atual"] = usuario
                    st.success(f"Bem-vindo, {usuario}!")
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos.")
                    
        st.markdown("</div>", unsafe_allow_html=True)

# --- APLICAÇÃO PRINCIPAL (DASHBOARD) ---
else:
    # Barra Lateral (Sidebar)
    with st.sidebar:
        st.markdown(f"### 👤 Conectado como: **{st.session_state['usuario_atual']}**")
        if st.button("🚪 Sair / Logout", use_container_width=True):
            st.session_state["logado"] = False
            st.session_state["usuario_atual"] = ""
            st.rerun()
        st.divider()

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    NOME_PLANILHA = "Dados_Streamlit"

    @st.cache_resource
    def conectar_gsheets():
        caminho_credenciais = "credentials.json"
        if not os.path.exists(caminho_credenciais):
            st.error("⚠️ Arquivo 'credentials.json' não foi encontrado no servidor!")
            st.stop()
            
        creds = Credentials.from_service_account_file(caminho_credenciais, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        try:
            sheet = client.open(NOME_PLANILHA).sheet1
            if len(sheet.get_all_values()) == 0:
                sheet.append_row(["Data/Hora", "Categoria", "Valor", "Quantidade", "Total", "RegistradoPor"])
            return sheet
        except Exception as e:
            st.error(f"Erro ao conectar com Google Sheets: {e}")
            st.stop()

    sheet = conectar_gsheets()

    st.title("⚡ Dashboard de Controle")

    col_form, col_dash = st.columns([1, 2])

    with col_form:
        st.subheader("📝 Novo Registro")
        with st.form("form_registro"):
            categoria = st.selectbox("Categoria", ["Tech", "Vendas", "Marketing", "Suporte"])
            valor = st.number_input("Valor (R$)", min_value=10.0, max_value=5000.0, value=250.0)
            quantidade = st.slider("Quantidade", 1, 100, 5)
            enviado = st.form_submit_button("Salvar Registro")
            
            if enviado:
                data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                total = valor * quantidade
                sheet.append_row([data_hora, categoria, valor, quantidade, total, st.session_state['usuario_atual']])
                st.success("✅ Salvo com sucesso no Google Sheets!")
                st.rerun()

    with col_dash:
        st.subheader("📊 Métricas em Tempo Real")
        registros = sheet.get_all_records()
        
        if registros:
            df = pd.DataFrame(registros)
            df["Valor"] = pd.to_numeric(df["Valor"])
            df["Quantidade"] = pd.to_numeric(df["Quantidade"])
            df["Total"] = pd.to_numeric(df["Total"])
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Acumulado", f"R$ {df['Total'].sum():,.2f}")
            m2.metric("Registros", len(df))
            m3.metric("Ticket Médio", f"R$ {df['Total'].mean():,.2f}")
            
            fig = px.bar(df, x="Categoria", y="Total", color="Categoria", title="Total por Categoria")
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Tabela de Dados")
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)
        else:
            st.info("Nenhum registro encontrado ainda.")
