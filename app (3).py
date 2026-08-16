import io
import sqlite3
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestor de Boletins de Sondagem Rotativa",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ESTILIZAÇÃO CSS ---
st.markdown(
    """
    <style>
    .stApp { 
        background: radial-gradient(circle at top left, #1a2035, #0d1117, #05070a); 
        color: #e6edf3; 
    }
    .login-box, .stCard {
        background: rgba(22, 27, 34, 0.85);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(88, 166, 255, 0.3);
        border-radius: 16px;
        padding: 25px;
        box-shadow: 0 0 25px rgba(56, 139, 253, 0.2);
    }
    .stMetric {
        background: rgba(22, 27, 34, 0.85) !important;
        border: 1px solid rgba(88, 166, 255, 0.25) !important;
        border-radius: 14px !important;
        padding: 18px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), 0 0 12px rgba(56, 139, 253, 0.15);
    }
    div[data-testid="stDataEditor"] {
        background: rgba(13, 17, 23, 0.9) !important;
        border: 1px solid rgba(88, 166, 255, 0.3) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 15px rgba(56, 139, 253, 0.15) !important;
    }
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
            "<p style='text-align: center; color: #8b949e;'>Gestão de Boletins de Sondagem Rotativa</p>",
            unsafe_allow_html=True,
        )

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

        c.execute("SELECT COUNT(*) FROM avancos")
        if c.fetchone()[0] == 0:
            dados_iniciais = [
                ("14/04/2023", "DHAB 109", 44.10, 47.20, 3.10, 3.10, 100.0),
                ("14/04/2023", "DHAB 109", 47.20, 50.20, 3.00, 3.00, 100.0),
                ("14/04/2023", "DHAB 109", 50.20, 53.30, 3.10, 3.10, 100.0),
                ("15/04/2023", "DHAB 110", 0.00, 3.00, 3.00, 2.80, 93.33),
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

    def obter_furos():
        conn = sqlite3.connect("sondagem.db")
        df = pd.read_sql_query("SELECT DISTINCT furo FROM avancos ORDER BY furo ASC", conn)
        conn.close()
        return df["furo"].tolist() if not df.empty else []

    def carregar_dados_furo(furo_selecionado):
        conn = sqlite3.connect("sondagem.db")
        df = pd.read_sql_query(
            "SELECT * FROM avancos WHERE furo = ? ORDER BY id ASC",
            conn,
            params=(furo_selecionado,),
        )
        conn.close()
        return df

    def salvar_dados_furo(df_novo, furo_atual):
        conn = sqlite3.connect("sondagem.db")
        c = conn.cursor()
        c.execute("DELETE FROM avancos WHERE furo = ?", (furo_atual,))
        conn.commit()

        df_novo["furo"] = furo_atual
        df_novo.to_sql("avancos", conn, if_exists="append", index=False)
        conn.close()

    def excluir_furo(furo_para_excluir):
        conn = sqlite3.connect("sondagem.db")
        c = conn.cursor()
        c.execute("DELETE FROM avancos WHERE furo = ?", (furo_para_excluir,))
        conn.commit()
        conn.close()

    init_db()

    # --- INICIALIZAÇÃO E RECÁLCULO AUTOMÁTICO ---
    if "sb_de" not in st.session_state:
        st.session_state["sb_de"] = 0.0
    if "sb_ate" not in st.session_state:
        st.session_state["sb_ate"] = 0.0
    if "sb_recuperado" not in st.session_state:
        st.session_state["sb_recuperado"] = 0.0
    if "confirmar_exclusao" not in st.session_state:
        st.session_state["confirmar_exclusao"] = False

    def recalcular_sidebar():
        avanco = max(0.0, st.session_state["sb_ate"] - st.session_state["sb_de"])
        st.session_state["sb_avanco"] = round(avanco, 2)
        
        # Preenche o Recuperado igual ao Avanço automaticamente (100% padrão)
        st.session_state["sb_recuperado"] = round(avanco, 2)
        
        if avanco > 0:
            pct = (st.session_state["sb_recuperado"] / avanco) * 100
            st.session_state["sb_pct"] = round(min(100.0, pct), 2)
        else:
            st.session_state["sb_pct"] = 0.0

    if "sb_avanco" not in st.session_state or "sb_pct" not in st.session_state:
        recalcular_sidebar()

    # --- BARRA LATERAL ---
    with st.sidebar:
        st.title("📌 Seleção de Boletim")
        st.write(f"Usuário: **{st.session_state['usuario_atual']}**")

        if st.button("🚪 Sair / Logout", use_container_width=True):
            st.session_state["logado"] = False
            st.session_state["usuario_atual"] = ""
            st.rerun()

        st.markdown("---")

        # Seleção de Documento
        lista_furos = obter_furos()

        if lista_furos:
            furo_selecionado = st.selectbox("📂 Selecione o Documento / Furo:", lista_furos)

            # Opção para Excluir o Furo Selecionado
            if not st.session_state["confirmar_exclusao"]:
                if st.button("🗑️ Excluir Furo Selecionado", use_container_width=True):
                    st.session_state["confirmar_exclusao"] = True
                    st.rerun()
            else:
                st.warning(f"⚠️ Tem certeza que deseja excluir o furo **{furo_selecionado}**?")
                col_sim, col_nao = st.columns(2)
                if col_sim.button("✔️ Sim", use_container_width=True):
                    excluir_furo(furo_selecionado)
                    st.session_state["confirmar_exclusao"] = False
                    st.success(f"Furo '{furo_selecionado}' excluído com sucesso!")
                    st.rerun()
                if col_nao.button("❌ Não", use_container_width=True):
                    st.session_state["confirmar_exclusao"] = False
                    st.rerun()

        else:
            furo_selecionado = None
            st.info("Nenhum furo cadastrado no momento.")

        st.markdown("---")
        st.subheader("🆕 Criar Novo Documento / Furo")
        novo_furo_nome = st.text_input("Identificação do Novo Furo (ex: DHAB 111)")
        if st.button("➕ Criar Novo Furo", use_container_width=True):
            if novo_furo_nome and novo_furo_nome not in lista_furos:
                conn = sqlite3.connect("sondagem.db")
                c = conn.cursor()
                c.execute(
                    "INSERT INTO avancos (data, furo, de_m, ate_m, avanco_m, recuperado_m, porcentagem) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (datetime.today().strftime("%d/%m/%Y"), novo_furo_nome, 0.0, 0.0, 0.0, 0.0, 0.0),
                )
                conn.commit()
                conn.close()
                st.success(f"Furo '{novo_furo_nome}' criado com sucesso!")
                st.rerun()
            elif novo_furo_nome in lista_furos:
                st.warning("Este furo já existe.")

        if furo_selecionado:
            st.markdown("---")
            st.subheader("➕ Adicionar Novo Avanço")

            st.number_input(
                "De (m)",
                min_value=0.0,
                step=0.1,
                key="sb_de",
                on_change=recalcular_sidebar,
            )
            st.number_input(
                "Até (m)",
                min_value=0.0,
                step=0.1,
                key="sb_ate",
                on_change=recalcular_sidebar,
            )
            st.number_input(
                "Recuperado (m)",
                min_value=0.0,
                step=0.1,
                key="sb_recuperado",
                on_change=recalcular_sidebar,
            )

            st.markdown("---")
            # Exibição dos Cálculos na Sidebar
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("⚡ Avanço (m)", f"{st.session_state['sb_avanco']:.2f} m")
            col_m2.metric("⚡ Recuperação", f"{st.session_state['sb_pct']:.1f}%")

            if st.button("💾 Inserir Registro", use_container_width=True):
                if st.session_state["sb_ate"] < st.session_state["sb_de"]:
                    st.error("❌ O valor 'Até' não pode ser menor que 'De'.")
                else:
                    conn = sqlite3.connect("sondagem.db")
                    c = conn.cursor()
                    c.execute(
                        """
                        INSERT INTO avancos (data, furo, de_m, ate_m, avanco_m, recuperado_m, porcentagem)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            datetime.today().strftime("%d/%m/%Y"),
                            furo_selecionado,
                            st.session_state["sb_de"],
                            st.session_state["sb_ate"],
                            st.session_state["sb_avanco"],
                            st.session_state["sb_recuperado"],
                            st.session_state["sb_pct"],
                        ),
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Avanço registrado em {furo_selecionado}!")
                    st.rerun()

    # --- CARREGAMENTO DOS DADOS DO FURO SELECIONADO ---
    if furo_selecionado:
        df_furo = carregar_dados_furo(furo_selecionado)

        st.title(f"📄 Boletim de Sondagem Rotativa - {furo_selecionado}")

        # Métricas Principais do Documento
        total_avanco = df_furo["avanco_m"].sum() if not df_furo.empty else 0.0
        total_recuperado = df_furo["recuperado_m"].sum() if not df_furo.empty else 0.0
        pct_media = (total_recuperado / total_avanco * 100) if total_avanco > 0 else 0.0

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Avanço Total do Furo", f"{total_avanco:.2f} m")
        col_m2.metric("Recuperado Total", f"{total_recuperado:.2f} m")
        col_m3.metric("Recuperação Média", f"{pct_media:.2f} %")

        st.markdown("---")

        # --- EDIÇÃO DIRETA DA TABELA COM CÁLCULOS AUTOMÁTICOS ---
        st.subheader(f"📋 Tabela do Documento: {furo_selecionado}")

        if not df_furo.empty:
            df_furo["avanco_m"] = df_furo["ate_m"] - df_furo["de_m"]
            df_furo["porcentagem"] = df_furo.apply(
                lambda r: (r["recuperado_m"] / r["avanco_m"] * 100) if r["avanco_m"] > 0 else 0.0,
                axis=1,
            ).round(2)

        df_editado = st.data_editor(
            df_furo,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{furo_selecionado}",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "data": st.column_config.TextColumn("Data"),
                "furo": st.column_config.TextColumn("Furo", disabled=True),
                "de_m": st.column_config.NumberColumn("De (m)", format="%.2f", min_value=0.0),
                "ate_m": st.column_config.NumberColumn("Até (m)", format="%.2f", min_value=0.0),
                "avanco_m": st.column_config.NumberColumn("Avanço (m) ⚡", format="%.2f", disabled=True),
                "recuperado_m": st.column_config.NumberColumn("Recuperado (m)", format="%.2f", min_value=0.0),
                "porcentagem": st.column_config.NumberColumn("Recuperação (%) ⚡", format="%.2f %%", disabled=True),
            },
        )

        if st.button("💾 Salvar Alterações deste Documento", use_container_width=True):
            df_editado["avanco_m"] = df_editado["ate_m"] - df_editado["de_m"]
            df_editado["porcentagem"] = df_editado.apply(
                lambda row: (row["recuperado_m"] / row["avanco_m"] * 100) if row["avanco_m"] > 0 else 0.0,
                axis=1,
            ).round(2)

            salvar_dados_furo(df_editado, furo_selecionado)
            st.success(f"Documento '{furo_selecionado}' salvo com os cálculos atualizados!")
            st.rerun()

        # --- GRÁFICO DO FURO ---
        if not df_furo.empty:
            st.markdown("---")
            st.subheader("📈 Perfil de Avanço e Recuperação")
            fig = px.bar(
                df_furo,
                x="id",
                y=["avanco_m", "recuperado_m"],
                barmode="group",
                labels={"value": "Metros (m)", "id": "Manobra / Trecho", "variable": "Métrica"},
                title=f"Avanço vs Recuperação - Furo {furo_selecionado}",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Crie um novo furo na barra lateral para começar.")
