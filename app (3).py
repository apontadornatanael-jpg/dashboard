import io
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

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

    colunas_novas = [
        ("acumulado_m", "REAL"),
        ("material", "TEXT")
    ]
    for nome_col, tipo_col in colunas_novas:
        try:
            c.execute(f"ALTER TABLE avancos ADD COLUMN {nome_col} {tipo_col}")
        except sqlite3.OperationalError:
            pass

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

# --- FUNÇÕES DE CÁLCULO ---
def calcular_diferenca_horas(inicio, fim):
    try:
        fmt = "%H:%M"
        t1 = datetime.strptime(str(inicio).strip(), fmt)
        t2 = datetime.strptime(str(fim).strip(), fmt)
        diff = (t2 - t1).total_seconds() / 3600.0
        if diff < 0:
            diff += 24.0
        return round(diff, 2)
    except Exception:
        return 0.0

# --- GERADOR DE EXCEL FORMATADO ---
def gerar_excel_boletim(cabecalho, df_avancos, df_horarios, df_insumos):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Boletim de Sondagem"
    ws.views.sheetView[0].showGridLines = True

    # Estilos
    fill_header = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    fill_sub = PatternFill(start_color="DCE6F1", end_color="DCE6F1", fill_type="solid")
    fill_highlight = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=11, bold=True)
    font_normal = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    # Título Principal
    ws.merge_cells('A1:I1')
    ws['A1'] = f"BOLETIM DE SONDAGEM ROTATIVA - {cabecalho[0]}"
    ws['A1'].font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    ws['A1'].fill = PatternFill(start_color="0F243E", end_color="0F243E", fill_type="solid")
    ws['A1'].alignment = Alignment(horizontal="center", vertical="center")

    # Cabeçalho de Informações Gerais
    info_data = [
        ["Data:", cabecalho[1] or "", "Cliente:", cabecalho[5] or "", "Área:", cabecalho[6] or "", "Turno:", cabecalho[4] or ""],
        ["Modelo Sonda:", cabecalho[2] or "", "Nº Sonda:", cabecalho[3] or "", "Azimute:", cabecalho[7] or 0, "Ângulo:", cabecalho[8] or 0],
        ["Diâm. Peça:", cabecalho[9] or "", "Nº Coroa:", cabecalho[10] or "", "Nº Calibrador:", cabecalho[11] or "", "Última Caixa:", cabecalho[15] or 0]
    ]
    
    row_idx = 3
    for row in info_data:
        for col_idx, val in enumerate(row, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_bold if col_idx % 2 != 0 else font_normal
            if col_idx % 2 != 0:
                cell.fill = fill_sub
            cell.border = thin_border
        row_idx += 1

    row_idx += 1

    # Tabela de Avanços
    ws.cell(row=row_idx, column=1, value="PERFURAÇÃO E RECUPERAÇÃO").font = font_bold
    row_idx += 1
    
    cols_av = ["De (m)", "Até (m)", "Avanço (m)", "Recuperado (m)", "Acumulado (m)", "Recuperação (%)", "Material Perfurado"]
    for c_idx, col_name in enumerate(cols_av, start=1):
        cell = ws.cell(row=row_idx, column=c_idx, value=col_name)
        cell.fill = fill_header
        cell.font = font_header
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    row_idx += 1
    for _, r in df_avancos.iterrows():
        ws.cell(row=row_idx, column=1, value=r["de_m"]).border = thin_border
        ws.cell(row=row_idx, column=2, value=r["ate_m"]).border = thin_border
        ws.cell(row=row_idx, column=3, value=r["avanco_m"]).border = thin_border
        ws.cell(row=row_idx, column=4, value=r["recuperado_m"]).border = thin_border
        ws.cell(row=row_idx, column=5, value=r["acumulado_m"]).border = thin_border
        
        c_pct = ws.cell(row=row_idx, column=6, value=f"{r['porcentagem']:.1f}%")
        c_pct.border = thin_border
        if r["porcentagem"] < 80.0:
            c_pct.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
            
        ws.cell(row=row_idx, column=7, value=r["material"]).border = thin_border
        row_idx += 1

    row_idx += 2

    # Horários e Insumos lado a lado
    ws.cell(row=row_idx, column=1, value="DESCRIÇÃO DOS SERVIÇOS").font = font_bold
    ws.cell(row=row_idx, column=6, value="INSUMOS UTILIZADOS").font = font_bold
    row_idx += 1

    cols_hor = ["Descrição", "Inicial", "Final", "Tempo (h)", "Horímetro"]
    for c_idx, col_name in enumerate(cols_hor, start=1):
        cell = ws.cell(row=row_idx, column=c_idx, value=col_name)
        cell.fill = fill_header
        cell.font = font_header
        cell.border = thin_border

    cols_ins = ["Item / Descrição", "Qtde"]
    for c_idx, col_name in enumerate(cols_ins, start=6):
        cell = ws.cell(row=row_idx, column=c_idx, value=col_name)
        cell.fill = fill_header
        cell.font = font_header
        cell.border = thin_border

    start_h_row = row_idx + 1
    for _, r in df_horarios.iterrows():
        ws.cell(row=start_h_row, column=1, value=r["descricao"]).border = thin_border
        ws.cell(row=start_h_row, column=2, value=r["hora_inicio"]).border = thin_border
        ws.cell(row=start_h_row, column=3, value=r["hora_fim"]).border = thin_border
        ws.cell(row=start_h_row, column=4, value=r["tempo_horas"]).border = thin_border
        ws.cell(row=start_h_row, column=5, value=r["horimetro"]).border = thin_border
        start_h_row += 1

    start_i_row = row_idx + 1
    for _, r in df_insumos.iterrows():
        ws.cell(row=start_i_row, column=6, value=r["item"]).border = thin_border
        ws.cell(row=start_i_row, column=7, value=r["quantidade"]).border = thin_border
        start_i_row += 1

    # Autoajuste de colunas
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

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

    # 2. TABELA DE AVANÇOS
    st.subheader("📊 Perfuração e Recuperação")
    
    if not df_avancos.empty:
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
        if not df_horarios.empty:
            df_horarios["tempo_horas"] = df_horarios.apply(
                lambda r: calcular_diferenca_horas(r["hora_inicio"], r["hora_fim"]), axis=1
            )

        df_editado_horarios = st.data_editor(
            df_horarios,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_hor_{furo_selecionado}",
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "furo": st.column_config.TextColumn("Furo", disabled=True),
                "descricao": st.column_config.TextColumn("Descrição dos Serviços"),
                "hora_inicio": st.column_config.TextColumn("Inicial (HH:MM)"),
                "hora_fim": st.column_config.TextColumn("Final (HH:MM)"),
                "tempo_horas": st.column_config.NumberColumn("Tempo (h) ⚡", format="%.2f", disabled=True),
                "horimetro": st.column_config.TextColumn("Horímetro"),
            }
        )

        total_horas_servico = df_editado_horarios["tempo_horas"].sum() if not df_editado_horarios.empty else 0.0
        st.caption(f"⏱️ **Total de Horas Registradas:** {total_horas_servico:.2f} h")

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

    # BOTÕES DE AÇÃO (SALVAR E EXPORTAR EXCEL)
    col_btn1, col_btn2 = st.columns(2)

    with col_btn1:
        if st.button("💾 Salvar Alterações", use_container_width=True):
            conn = get_db()
            c = conn.cursor()
            
            c.execute("DELETE FROM avancos WHERE furo = ?", (furo_selecionado,))
            for _, row in df_editado_avancos.iterrows():
                c.execute("""
                    INSERT INTO avancos (furo, de_m, ate_m, avanco_m, recuperado_m, acumulado_m, porcentagem, material)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (furo_selecionado, row["de_m"], row["ate_m"], row["ate_m"] - row["de_m"], row["recuperado_m"], row["acumulado_m"], row["porcentagem"], row["material"]))

            c.execute("DELETE FROM horarios WHERE furo = ?", (furo_selecionado,))
            for _, row in df_editado_horarios.iterrows():
                tempo_calc = calcular_diferenca_horas(row["hora_inicio"], row["hora_fim"])
                c.execute("""
                    INSERT INTO horarios (furo, descricao, hora_inicio, hora_fim, tempo_horas, horimetro)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (furo_selecionado, row["descricao"], row["hora_inicio"], row["hora_fim"], tempo_calc, row["horimetro"]))

            c.execute("DELETE FROM insumos WHERE furo = ?", (furo_selecionado,))
            for _, row in df_editado_insumos.iterrows():
                c.execute("""
                    INSERT INTO insumos (furo, item, quantidade)
                    VALUES (?, ?, ?)
                """, (furo_selecionado, row["item"], row["quantidade"]))

            conn.commit()
            conn.close()
            st.success("Dados salvos!")
            st.rerun()

    with col_btn2:
        excel_data = gerar_excel_boletim(cabecalho, df_editado_avancos, df_editado_horarios, df_editado_insumos)
        st.download_button(
            label="📥 Baixar Boletim em Excel Formatado",
            data=excel_data,
            file_name=f"Boletim_Sondagem_{furo_selecionado}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    st.info("Selecione ou crie um novo boletim na barra lateral para iniciar a digitação.")
