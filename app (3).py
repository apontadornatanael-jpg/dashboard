import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Streamlit + Banco de Dados", layout="wide", initial_sidebar_state="expanded")

# --- ESTILIZAÇÃO CSS (Design Iluminado / Glassmorphism) ---
st.markdown('''
    <style>
    /* Fundo Geral */
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
''', unsafe_allow_html=True)

# --- CADASTRO DE USUÁRIOS E SENHAS ---
USUARIOS = {
    "admin": "1234",
    "natanael": "senha123"
}

# --- GERENCIAMENTO DE SESSÃO DO LOGIN ---
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

# --- DASHBOARD PRINCIPAL ---
else:
    # Sidebar com informações do usuário logado
    with st.sidebar:
        st.markdown(f"### 👤 Conectado como:\n**{st.session_state['usuario_atual']}**")
        if st.button("🚪 Sair / Logout", use_container_width=True):
            st.session_state["logado"] = False
            st.session_state["usuario_atual"] = ""
            st.rerun()
        st.divider()

    # Funções do Banco de Dados SQLite
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
