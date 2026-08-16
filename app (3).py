import io
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Boletim Digital de Sondagem Rotativa",
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
    .stCard, .block-container {
        background: rgba(22, 27, 34, 0.85);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(88, 166, 255, 0.3);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .stMetric {
        background: rgba(22, 27, 34, 0.85) !important;
        border: 1px solid rgba(88, 166, 255, 0.25) !important;
        border-radius: 14px !important;
        padding: 14px !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- BANCO DE DADOS COM CORREÇÃO AUTOMÁTICA DE ESQUEMA ---
def get_db():
    return sqlite3.connect("sondagem.db")

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Tabela principal do boletim / cabeçalho
    c.execute("""
        CREATE TABLE IF NOT EXISTS boletins (
            furo TEXT PRIMARY KEY,
            data TEXT,
            modelo_sonda TEXT,
            num_sonda TEXT,
            turno TEXT,
            cliente TEXT,
            area TEXT,
            azimute REAL,
            angulo REAL,
            diam_peca TEXT,
            coroa_num TEXT,
            calib_num TEXT,
            revest_diam TEXT,
            revest_de REAL,
            revest_ate REAL,
            num_caixa INTEGER,
            observacoes TEXT
        )
    """)

    # Tabela de Avanços
    c.execute("""
        CREATE TABLE IF NOT EXISTS avancos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            furo TEXT,
            de_m REAL,
            ate_m REAL,
            avanco_m REAL,
            recuperado_m REAL,
            acumulado_m REAL,
            porcentagem REAL,
            material TEXT
        )
    """)

    # Garante que colunas novas existam caso o banco antigo já estivesse criado no servidor
    colunas_novas = [
        ("acumulado_m", "REAL"),
        ("material", "TEXT")
    ]
    for nome_col, tipo_col in colunas_novas:
        try:
            c.execute(f"ALTER TABLE avancos ADD COLUMN {nome_col} {tipo_col}")
        except sqlite3.OperationalError:
            pass # Coluna já existe no banco

    # Tabela de Horários / Serviços
    c.execute("""
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            furo TEXT,
            descricao TEXT,
            hora_inicio TEXT,
            hora_fim TEXT,
            tempo_horas REAL,
            horimetro TEXT
        )
    """)

    # Tabela de Insumos
    c.execute("""
        CREATE TABLE IF NOT EXISTS insumos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            furo TEXT,
            item TEXT,
            quantidade REAL
        )
    """)

    conn.commit()
    conn.close()

init_db()

# --- FUNÇÕES DE CARREGAMENTO E SALVAMENTO ---
def obter_furos():
    conn = get_db()
    df = pd.read_sql_query("SELECT furo FROM boletins ORDER BY furo ASC", conn)
    conn.close()
    return df["furo"].tolist() if not df.empty else []

def carregar_boletim(furo):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM boletins WHERE furo = ?", (furo,))
    cabecalho = c.fetchone()
    
    df_avancos = pd.read_sql_query("SELECT * FROM avancos WHERE furo = ? ORDER BY id ASC", conn, params=(furo,))
    df_horarios = pd.read_sql_query("SELECT * FROM horarios WHERE furo = ? ORDER BY id ASC", conn, params=(furo,))
    df_insumos = pd.read_sql_query("SELECT * FROM insumos WHERE furo = ? ORDER BY id ASC", conn, params=(furo,))
    
    conn.close()
    return cabecalho, df_avancos, df_horarios, df_insumos

# --- INICIALIZAÇÃO DE ESTADOS ---
if "sb_de" not in st.session_state: st.session_state["sb_de"] = 0.0
if "sb_ate" not in st.session_state: st.session_state["sb_ate"] = 0.0
if "sb_recuperado" not in st.session_state: st.session_state["sb_recuperado"] = 0.0

def recalcular_sidebar():
    avanco = max(0.0, st.session_state["sb_ate"] - st.session_state["sb_de"])
    st.session_state["sb_avanco"] = round(avanco, 2)
    st.session_state["sb_recuperado"] = round(avanco, 2)
    st.session_state["sb_pct"] = 100.0 if avanco > 0 else 0.0

if "sb_avanco" not in st.session_state:
    recalcular_sidebar()

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("📋 Gestão de Boletins")
    
    lista_furos = obter_furos()
    furo_selecionado = st.selectbox("📂 Selecionar Boletim Existente:", lista_furos) if lista_furos else None
    
    st.markdown("---")
    st.subheader("🆕 Novo Boletim")
    novo_furo_id = st.text_input("Identificação do Furo (ex: DHAB 109)")
    
    if st.button("➕ Criar Boletim", use_container_width=True):
        if novo_furo_id:
            if novo_furo_id not in lista_furos:
                conn = get_db()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO boletins (furo, data, modelo_sonda, num_sonda, turno, cliente, area, azimute, angulo)
                    VALUES (?, ?, 'LM 75', '04', '1º', 'ATLAS LITHIUM', 'ABELHAS', 290.0, 60.0)
                """, (novo_furo_id, datetime.today().strftime("%d/%m/%Y")))
                conn.commit()
                conn.close()
                st.success(f"Boletim '{novo_furo_id}' criado!")
                st.rerun()
            else:
                st.warning("Este furo já existe.")

    if furo_selecionado:
        st.markdown("---")
        st.subheader("⛏️ Adicionar Avanço")
        st.number_input("De (m)", min_value=0.0, step=0.1, key="sb_de", on_change=recalcular_sidebar)
        st.number_input("Até (m)", min_value=0.0, step=0.1, key="sb_ate", on_change=recalcular_sidebar)
        st.number_input("Recuperado (m)", min_value=0.0, step=0.1, key="sb_recuperado")
        sb_mat = st.text_input("Material Perfurado", value="")

        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Avanço", f"{st.session_state['sb_avanco']:.2f} m")
        col_m2.metric("Recuperação", f"{st.session_state['sb_pct']:.1f}%")

        if st.button("💾 Inserir Avanço", use_container_width=True):
            if st.session_state["sb_ate"] >= st.session_state["sb_de"]:
                conn = get_db()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO avancos (furo, de_m, ate_m, avanco_m, recuperado_m, porcentagem, material)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    furo_selecionado,
                    st.session_state["sb_de"],
                    st.session_state["sb_ate"],
                    st.session_state["sb_avanco"],
                    st.session_state["sb_recuperado"],
                    st.session_state["sb_pct"],
                    sb_mat
                ))
                conn.commit()
                conn.close()
                st.success("Avanço registrado!")
                st.rerun()

# --- ÁREA PRINCIPAL DO BOLETIM ---
if furo_selecionado:
    cabecalho, df_avancos, df_horarios, df_insumos = carregar_boletim(furo_selecionado)
    
    st.title(f"📄 Boletim de Sondagem Rotativa: {furo_selecionado}")
    
    # 1. CABEÇALHO TÉCNICO
    with st.expander("📌 Informações Gerais do Furo e Equipamento", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        data = col1.text_input("Data", value=cabecalho[1] or "")
        cliente = col2.text_input("Cliente", value=cabecalho[5] or "")
        area = col3.text_input("Área", value=cabecalho[6] or "")
        turno = col4.text_input("Turno", value=cabecalho[4] or "")

        col5, col6, col7, col8 = st.columns(4)
        sonda = col5.text_input("Modelo Sonda", value=cabecalho[2] or "")
        num_sonda = col6.text_input("Nº Sonda", value=cabecalho[3] or "")
        azimute = col7.number_input("Azimute (°)", value=float(cabecalho[7] or 0.0))
        angulo = col8.number_input("Ângulo (°)", value=float(cabecalho[8] or 0.0))

        st.markdown("**Peça de Corte e Revestimento**")
        col9, col10, col11, col12, col13 = st.columns(5)
        diam_peca = col9.text_input("Diâm. Peça", value=cabecalho[9] or "NQ")
        coroa = col10.text_input("Nº Coroa", value=cabecalho[10] or "")
        calib = col11.text_input("Nº Calibrador", value=cabecalho[11] or "")
        rev_diam = col12.text_input("Diâm. Revestimento", value=cabecalho[12] or "")
        caixas = col13.number_input("Última Caixa Nº", value=int(cabecalho[15] or 0))

        if st.button("💾 Salvar Cabeçalho", use_container_width=True):
            conn = get_db()
            c = conn.cursor()
            c.execute("""
                UPDATE boletins SET
                data=?, cliente=?, area=?, turno=?, modelo_sonda=?, num_sonda=?,
                azimute=?, angulo=?, diam_peca=?, coroa_num=?, calib_num=?,
                revest_diam=?, num_caixa=? WHERE furo=?
            """, (data, cliente, area, turno, sonda, num_sonda, azimute, angulo, diam_peca, coroa, calib, rev_diam, caixas, furo_selecionado))
            conn.commit()
            conn.close()
            st.success("Cabeçalho atualizado!")

    # 2. TABELA DE AVANÇOS (PERFURADO E RECUPERAÇÃO)
    st.subheader("📊 Perfuração e Recuperação")
    
    if not df_avancos.empty:
        # Recálculo automático de acumulado e percentual
        df_avancos["avanco_m"] = df_avancos["ate_m"] - df_avancos["de_m"]
        df_avancos["acumulado_m"] = df_avancos["recuperado_m"].cumsum()
        df_avancos["porcentagem"] = df_avancos.apply(
            lambda r: round((r["recuperado_m"] / r["avanco_m"] * 100), 2) if r["avanco_m"] > 0 else 0.0, axis=1
        )

    df_editado_avancos = st.data_editor(
        df_avancos,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_av_{furo_selecionado}",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "furo": st.column_config.TextColumn("Furo", disabled=True),
            "de_m": st.column_config.NumberColumn("De (m)", format="%.2f"),
            "ate_m": st.column_config.NumberColumn("Até (m)", format="%.2f"),
            "avanco_m": st.column_config.NumberColumn("Avanço (m) ⚡", format="%.2f", disabled=True),
            "recuperado_m": st.column_config.NumberColumn("Recuperado (m)", format="%.2f"),
            "acumulado_m": st.column_config.NumberColumn("Total Acum. (m) ⚡", format="%.2f", disabled=True),
            "porcentagem": st.column_config.NumberColumn("Recuperação (%) ⚡", format="%.2f %%", disabled=True),
            "material": st.column_config.TextColumn("Material Perfurado"),
        }
    )

    # Resumo das Métricas no Topo da Tabela
    total_av = df_avancos["avanco_m"].sum() if not df_avancos.empty else 0.0
    total_rec = df_avancos["recuperado_m"].sum() if not df_avancos.empty else 0.0
    rec_med = (total_rec / total_av * 100) if total_av > 0 else 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("Avanço Total do Furo", f"{total_av:.2f} m")
    m2.metric("Recuperado Total", f"{total_rec:.2f} m")
    m3.metric("Recuperação Média", f"{rec_med:.2f} %")

    # 3. HORÁRIOS E INSUMOS
    col_e1, col_e2 = st.columns([2, 1])
    
    with col_e1:
        st.subheader("⏱️ Descrição dos Serviços e Horas")
        df_editado_horarios = st.data_editor(
            df_horarios,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_hor_{furo_selecionado}",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "furo": st.column_config.TextColumn("Furo", disabled=True),
                "descricao": st.column_config.TextColumn("Descrição dos Serviços"),
                "hora_inicio": st.column_config.TextColumn("Inicial"),
                "hora_fim": st.column_config.TextColumn("Final"),
                "tempo_horas": st.column_config.NumberColumn("Tempo (h)", format="%.2f"),
                "horimetro": st.column_config.TextColumn("Horímetro"),
            }
        )

    with col_e2:
        st.subheader("⛽ Insumos Utilizados")
        df_editado_insumos = st.data_editor(
            df_insumos,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_ins_{furo_selecionado}",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "furo": st.column_config.TextColumn("Furo", disabled=True),
                "item": st.column_config.TextColumn("Descrição"),
                "quantidade": st.column_config.NumberColumn("Qtde", format="%.1f"),
            }
        )

    # BOTÃO SALVAR GERAL
    if st.button("💾 Salvar Todas as Alterações da Tabela", use_container_width=True):
        conn = get_db()
        c = conn.cursor()
        
        # Salva avanços
        c.execute("DELETE FROM avancos WHERE furo = ?", (furo_selecionado,))
        for _, row in df_editado_avancos.iterrows():
            c.execute("""
                INSERT INTO avancos (furo, de_m, ate_m, avanco_m, recuperado_m, acumulado_m, porcentagem, material)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (furo_selecionado, row["de_m"], row["ate_m"], row["ate_m"] - row["de_m"], row["recuperado_m"], row["acumulado_m"], row["porcentagem"], row["material"]))

        # Salva horários
        c.execute("DELETE FROM horarios WHERE furo = ?", (furo_selecionado,))
        for _, row in df_editado_horarios.iterrows():
            c.execute("""
                INSERT INTO horarios (furo, descricao, hora_inicio, hora_fim, tempo_horas, horimetro)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (furo_selecionado, row["descricao"], row["hora_inicio"], row["hora_fim"], row["tempo_horas"], row["horimetro"]))

        # Salva insumos
        c.execute("DELETE FROM insumos WHERE furo = ?", (furo_selecionado,))
        for _, row in df_editado_insumos.iterrows():
            c.execute("""
                INSERT INTO insumos (furo, item, quantidade)
                VALUES (?, ?, ?)
            """, (furo_selecionado, row["item"], row["quantidade"]))

        conn.commit()
        conn.close()
        st.success("Todos os dados do boletim foram atualizados!")
        st.rerun()

else:
    st.info("Selecione ou crie um novo boletim na barra lateral para iniciar a digitação.")
