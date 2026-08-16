import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import io

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Boletim de Sondagem Rotativa Interativo",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS (Design Neon / Glassmorphism Iluminado) ---
st.markdown('''
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
''', unsafe_allow_html=True)

# --- USUÁRIOS E AUTENTICAÇÃO ---
USUARIOS = {
    "admin": "1234",
    "natanael": "senha123"
}

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
        st.markdown("<p style='text-align: center; color: #8b949e;'>Insira suas credenciais para gerenciar a Sondagem Rotativa</p>", unsafe_allow_html=True)
        
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
    # --- FUNÇÕES DE BANCO DE DADOS (SQLite) ---
    def init_db():
        conn = sqlite3.connect('sondagem.db')
        c = conn.cursor()
        c.execute('''
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
        ''')
        conn.commit()
        
        # População Inicial baseada na imagem se o banco estiver vazio
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
                ("14/04/2023", "DHAB 109", 98.50, 101.50, 3.00, 3.00, 100.0)
            ]
            c.executemany('''
                INSERT INTO avancos (data, furo, de_m, ate_m, avanco_m, recuperado_m, porcentagem)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', dados_iniciais)
            conn.commit()
        conn.close()

    def carregar_dados():
        conn = sqlite3.connect('sondagem.db')
        df = pd.read_sql_query("SELECT * FROM avancos ORDER BY id ASC", conn)
        conn.close()
        return df

    def atualizar_banco_completo(df_novo):
        conn = sqlite3.connect('sondagem.db')
        # Limpa e reescreve com os dados editados
        c = conn.cursor()
        c.execute("DELETE FROM avancos")
        conn.commit()
        
        df_novo.to_sql('avancos', conn, if_exists='append', index=False)
        conn.close()

    # --- GERADOR DE EXCEL PROFISSIONAL ---
    def gerar_excel_estilizado(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Boletim_Sondagem', index=False, startrow=4)
            workbook = writer.book
            worksheet = writer.sheets['Boletim_Sondagem']

            # Formatos Visuais
            fmt_titulo = workbook.add_format({
                'bold': True, 'font_size': 16, 'font_color': '#1f2937', 'align': 'left'
            })
            fmt_sub = workbook.add_format({
                'italic': True, 'font_size': 10, 'font_color': '#4b5563', 'align': 'left'
            })
            fmt_cabecalho = workbook.add_format({
                'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
                'fg_color': '#1e293b', 'font_color': '#ffffff', 'border': 1
            })
            fmt_dados = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1, 'num_format': '0.00'
            })

            # Escrevendo Cabeçalho Personalizado
            worksheet.write(0, 0, "BOLETIM DE SONDAGEM ROTATIVA - RELATÓRIO TÉCNICO", fmt_titulo)
            worksheet.write(1, 0, f"Cliente: ATLAS LITHIUM | Área: ABELHAS | Furo: DHAB 109 | Data Exportação: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fmt_sub)

            # Estilizando Cabeçalhos e Colunas
            for col_idx, col_name in enumerate(df.columns):
                worksheet.write(4, col_idx, col_name.upper(), fmt_cabecalho)
                worksheet.set_column(col_idx, col_idx, 16, fmt_dados)

        return output.getvalue()

    init_db()

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👤 Usuário:\n**{st.session_state['usuario_atual']}**")
        if st.button("🚪 Sair / Logout", use_container_width=True):
            st.session_state["logado"] = False
            st.session_state["usuario_atual"] = ""
            st.rerun()
        st.divider()
        
        st.markdown("### 🛠️ Parâmetros Fixos da Sondagem")
        st.text("Cliente: ATLAS LITHIUM")
        st.text("Área: ABELHAS")
        st.text("Furo Nº: DHAB 109")
        st.text("Modelo: LM 75 (Nº 04)")
        st.text("Sondadores: FABIO, Wellington, ANDRE")
        st.divider()

    st.title("⚡ Planilha Interativa & Boletim de Sondagem")

    # Carregar Dados Atuais
    df_atual = carregar_dados()

    # --- MÉTRICAS DE RESUMO AUTOMÁTICAS ---
    if not df_atual.empty:
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        prof_inicial = df_atual['de_m'].min() if not df_atual.empty else 0
        prof_final = df_atual['ate_m'].max() if not df_atual.empty else 0
        total_perfurado = df_atual['avanco_m'].sum()
        recup_media = df_atual['porcentagem'].mean()

        col_m1.metric("Prof. Inicial (m)", f"{prof_inicial:.2f} m")
        col_m2.metric("Prof. Final (m)", f"{prof_final:.2f} m")
        col_m3.metric("Total Perfurado", f"{total_perfurado:.2f} m")
        col_m4.metric("Recuperação Média", f"{recup_media:.1f}%")

    st.markdown("---")

    # --- PLANILHA EDITÁVEL EM TEMPO REAL ---
    st.subheader("📝 Edição Direta estilo Excel (Com cálculo automático)")
    st.caption("💡 Dica: Clique em qualquer célula para alterar, pressione '+' para adicionar linhas ou selecione para excluir.")

    # Data Editor Interativo
    df_editado = st.data_editor(
        df_atual,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "data": st.column_config.TextColumn("Data", default=datetime.now().strftime("%d/%m/%Y")),
            "furo": st.column_config.TextColumn("Furo Nº", default="DHAB 109"),
            "de_m": st.column_config.NumberColumn("De (m)", format="%.2f", min_value=0.0),
            "ate_m": st.column_config.NumberColumn("Até (m)", format="%.2f", min_value=0.0),
            "avanco_m": st.column_config.NumberColumn("Avanço (m) [Auto]", format="%.2f", disabled=True),
            "recuperado_m": st.column_config.NumberColumn("Recuperado (m)", format="%.2f", min_value=0.0),
            "porcentagem": st.column_config.NumberColumn("Recuperação (%) [Auto]", format="%.1f %%", disabled=True)
        },
        key="editor_sondagem"
    )

    # Re-calcula colunas derivadas automaticamente
    df_editado["de_m"] = pd.to_numeric(df_editado["de_m"], errors='coerce').fillna(0.0)
    df_editado["ate_m"] = pd.to_numeric(df_editado["ate_m"], errors='coerce').fillna(0.0)
    df_editado["recuperado_m"] = pd.to_numeric(df_editado["recuperado_m"], errors='coerce').fillna(0.0)

    # Fórmulas de Avanço e Porcentagem
    df_editado["avanco_m"] = (df_editado["ate_m"] - df_editado["de_m"]).round(2)
    df_editado["porcentagem"] = (
        (df_editado["recuperado_m"] / df_editado["avanco_m"].replace(0, 1)) * 100
    ).round(2)

    # Botões de Ação
    btn_col1, btn_col2 = st.columns([1, 1])

    with btn_col1:
        if st.button("💾 Salvar Alterações na Base de Dados", use_container_width=True):
            atualizar_banco_completo(df_editado)
            st.success("✅ Banco de dados atualizado com sucesso!")
            st.rerun()

    with btn_col2:
        excel_bytes = gerar_excel_estilizado(df_editado)
        st.download_button(
            label="📥 Baixar Planilha Excel Formatada (.xlsx)",
            data=excel_bytes,
            file_name=f"boletim_sondagem_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    # --- GRÁFICO TÉCNICO ---
    st.markdown("---")
    st.subheader("📊 Perfil de Avanço da Perfuração")
    
    if not df_editado.empty:
        fig = px.bar(
            df_editado,
            x="id",
            y="avanco_m",
            color="porcentagem",
            color_continuous_scale="Blues",
            hover_data=["de_m", "ate_m", "recuperado_m", "porcentagem"],
            labels={"id": "Manobra / Avanço", "avanco_m": "Avanço (m)", "porcentagem": "Recuperação %"},
            title="Avanço de Perfuração por Manobra"
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
```eof

O código foi atualizado com as seguintes melhorias:

1. **Edição Estilo Excel (`st.data_editor`)**: Você pode alterar os valores de **De**, **Até** e **Recuperado** diretamente na tabela na tela.
2. **Cálculos Automáticos**: O avanço (`ate_m - de_m`) e a recuperação (`(recuperado / avanco) * 100`) são calculados automaticamente conforme você digita.
3. **Exportação Profissional para Excel**: O botão **"Baixar Planilha Excel Formatada (.xlsx)"** gera um arquivo Excel estilizado com cabeçalho escuro, bordas e formatação numérica pronta para envio.
4. **Sincronização com o SQLite**: Ao clicar em **"Salvar Alterações"**, toda a tabela é re-gravada no banco de dados.
