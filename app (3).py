import io
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st
import openpyxl

from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Boletim Digital de Sondagem Rotativa",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ESTILIZAÇÃO CSS
# ============================================================

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
        border: 1px solid rgba(88, 166, 255, 0.30);
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

    .stButton > button {
        background: linear-gradient(135deg, #238636 0%, #2ea043 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# BANCO DE DADOS
# ============================================================

def get_db():
    return sqlite3.connect("sondagem.db")


def adicionar_coluna_se_nao_existir(cursor, tabela, coluna, tipo):
    try:
        cursor.execute(
            f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}"
        )
    except sqlite3.OperationalError:
        pass


def init_db():

    conn = get_db()
    c = conn.cursor()

    # --------------------------------------------------------
    # BOLETINS
    # --------------------------------------------------------

    c.execute(
        """
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
        """
    )

    # --------------------------------------------------------
    # AVANÇOS
    # --------------------------------------------------------

    c.execute(
        """
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
        """
    )

    adicionar_coluna_se_nao_existir(
        c,
        "avancos",
        "acumulado_m",
        "REAL"
    )

    adicionar_coluna_se_nao_existir(
        c,
        "avancos",
        "material",
        "TEXT"
    )

    # --------------------------------------------------------
    # HORÁRIOS / ATIVIDADES
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            furo TEXT,
            descricao TEXT,
            hora_inicio TEXT,
            hora_fim TEXT,
            tempo_horas REAL,
            horimetro TEXT
        )
        """
    )

    # Novas colunas adicionadas sem apagar dados antigos

    adicionar_coluna_se_nao_existir(
        c,
        "horarios",
        "codigo",
        "TEXT"
    )

    adicionar_coluna_se_nao_existir(
        c,
        "horarios",
        "grupo",
        "TEXT"
    )

    adicionar_coluna_se_nao_existir(
        c,
        "horarios",
        "atividade",
        "TEXT"
    )

    adicionar_coluna_se_nao_existir(
        c,
        "horarios",
        "classificacao",
        "TEXT"
    )

    adicionar_coluna_se_nao_existir(
        c,
        "horarios",
        "observacao",
        "TEXT"
    )

    # --------------------------------------------------------
    # INSUMOS
    # --------------------------------------------------------

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS insumos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            furo TEXT,
            item TEXT,
            quantidade REAL
        )
        """
    )

    conn.commit()
    conn.close()


init_db()


# ============================================================
# CADASTRO DE ATIVIDADES
# ============================================================

ATIVIDADES_PADRAO = {

    "01": {
        "grupo": "Produção",
        "atividade": "Furando",
        "classificacao": "Operação Direta",
    },

    "02": {
        "grupo": "Produção",
        "atividade": "Manobra",
        "classificacao": "Operação Direta",
    },

    "03": {
        "grupo": "Produção",
        "atividade": "Furando e Manobrando",
        "classificacao": "Operação Direta",
    },

    "04": {
        "grupo": "Apoio",
        "atividade": "Abastecimento",
        "classificacao": "Apoio Operacional",
    },

    "05": {
        "grupo": "Apoio",
        "atividade": "Preparação / Organização",
        "classificacao": "Apoio Operacional",
    },

    "06": {
        "grupo": "Manutenção",
        "atividade": "Manutenção Preventiva",
        "classificacao": "Manutenção Preventiva",
    },

    "07": {
        "grupo": "Manutenção",
        "atividade": "Manutenção Mecânica",
        "classificacao": "Mecânica Corretiva",
    },

    "08": {
        "grupo": "Externo",
        "atividade": "Intempéries",
        "classificacao": "Parada Externa",
    },

    "09": {
        "grupo": "Externo",
        "atividade": "Falta de Água",
        "classificacao": "Parada Externa",
    },

    "10": {
        "grupo": "Furo",
        "atividade": "Troca de Coroa",
        "classificacao": "Intervenção no Furo",
    },

    "11": {
        "grupo": "Furo",
        "atividade": "Revestimento",
        "classificacao": "Intervenção no Furo",
    },

    "12": {
        "grupo": "Furo",
        "atividade": "Limpeza do Furo",
        "classificacao": "Intervenção no Furo",
    },

    "13": {
        "grupo": "Administrativo",
        "atividade": "Atividade Administrativa",
        "classificacao": "Administrativo",
    },

    "14": {
        "grupo": "Segurança",
        "atividade": "DDS / APR",
        "classificacao": "Segurança",
    },

    "15": {
        "grupo": "Segurança",
        "atividade": "Inspeção de Segurança",
        "classificacao": "Segurança",
    },

}


# ============================================================
# FUNÇÕES DE CÁLCULO
# ============================================================

def calcular_diferenca_horas(inicio, fim):

    try:

        if not inicio or not fim:
            return 0.0

        fmt = "%H:%M"

        t1 = datetime.strptime(
            str(inicio).strip(),
            fmt
        )

        t2 = datetime.strptime(
            str(fim).strip(),
            fmt
        )

        diff = (
            t2 - t1
        ).total_seconds() / 3600.0

        # Caso atravesse meia-noite

        if diff < 0:
            diff += 24.0

        return round(
            diff,
            2
        )

    except Exception:
        return 0.0


def obter_total_recuperado_existente(furo):

    if not furo:
        return 0.0

    conn = get_db()

    c = conn.cursor()

    c.execute(
        """
        SELECT SUM(recuperado_m)
        FROM avancos
        WHERE furo = ?
        """,
        (furo,)
    )

    resultado = c.fetchone()[0]

    conn.close()

    if resultado is None:
        return 0.0

    return float(resultado)


def calcular_resumo_operacional(df_horarios):

    classificacoes = [
        "Operação Direta",
        "Apoio Operacional",
        "Manutenção Preventiva",
        "Mecânica Corretiva",
        "Parada Externa",
        "Intervenção no Furo",
        "Administrativo",
        "Segurança",
    ]

    resumo = {}

    for classificacao in classificacoes:

        if (
            df_horarios.empty
            or "classificacao" not in df_horarios.columns
        ):
            resumo[classificacao] = 0.0

        else:

            filtro = (
                df_horarios["classificacao"]
                .fillna("")
                .astype(str)
                .str.strip()
                == classificacao
            )

            resumo[classificacao] = round(
                df_horarios.loc[
                    filtro,
                    "tempo_horas"
                ].sum(),
                2
            )

    return resumo


# ============================================================
# EXCEL FORMATADO
# ============================================================

def gerar_excel_boletim(
    cabecalho,
    df_avancos,
    df_horarios,
    df_insumos,
    resumo_operacional,
):

    wb = openpyxl.Workbook()

    ws = wb.active

    ws.title = "Boletim de Sondagem"

    ws.views.sheetView[0].showGridLines = True


    # --------------------------------------------------------
    # ESTILOS
    # --------------------------------------------------------

    fill_header = PatternFill(
        start_color="1F497D",
        end_color="1F497D",
        fill_type="solid"
    )

    fill_sub = PatternFill(
        start_color="DCE6F1",
        end_color="DCE6F1",
        fill_type="solid"
    )

    fill_total = PatternFill(
        start_color="E2F0D9",
        end_color="E2F0D9",
        fill_type="solid"
    )

    font_header = Font(
        name="Calibri",
        size=11,
        bold=True,
        color="FFFFFF"
    )

    font_bold = Font(
        name="Calibri",
        size=11,
        bold=True
    )

    font_normal = Font(
        name="Calibri",
        size=10
    )

    thin_border = Border(

        left=Side(
            style="thin",
            color="D9D9D9"
        ),

        right=Side(
            style="thin",
            color="D9D9D9"
        ),

        top=Side(
            style="thin",
            color="D9D9D9"
        ),

        bottom=Side(
            style="thin",
            color="D9D9D9"
        ),

    )


    # --------------------------------------------------------
    # TÍTULO
    # --------------------------------------------------------

    ws.merge_cells(
        "A1:I1"
    )

    ws["A1"] = (
        f"BOLETIM DE SONDAGEM ROTATIVA - {cabecalho[0]}"
    )

    ws["A1"].font = Font(
        name="Calibri",
        size=14,
        bold=True,
        color="FFFFFF"
    )

    ws["A1"].fill = PatternFill(
        start_color="0F243E",
        end_color="0F243E",
        fill_type="solid"
    )

    ws["A1"].alignment = Alignment(
        horizontal="center",
        vertical="center"
    )


    # --------------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------------

    info_data = [

        [
            "Data:",
            cabecalho[1] or "",

            "Cliente:",
            cabecalho[5] or "",

            "Área:",
            cabecalho[6] or "",

            "Turno:",
            cabecalho[4] or "",
        ],

        [
            "Modelo Sonda:",
            cabecalho[2] or "",

            "Nº Sonda:",
            cabecalho[3] or "",

            "Azimute:",
            cabecalho[7] or 0,

            "Ângulo:",
            cabecalho[8] or 0,
        ],

        [
            "Diâm. Peça:",
            cabecalho[9] or "",

            "Nº Coroa:",
            cabecalho[10] or "",

            "Nº Calibrador:",
            cabecalho[11] or "",

            "Última Caixa:",
            cabecalho[15] or 0,
        ],

    ]

    row_idx = 3

    for row in info_data:

        for col_idx, val in enumerate(
            row,
            start=1
        ):

            cell = ws.cell(
                row=row_idx,
                column=col_idx,
                value=val
            )

            cell.font = (
                font_bold
                if col_idx % 2 != 0
                else font_normal
            )

            if col_idx % 2 != 0:
                cell.fill = fill_sub

            cell.border = thin_border

        row_idx += 1


    # --------------------------------------------------------
    # PERFURAÇÃO
    # --------------------------------------------------------

    row_idx += 1

    ws.cell(
        row=row_idx,
        column=1,
        value="PERFURAÇÃO E RECUPERAÇÃO"
    ).font = font_bold

    row_idx += 1

    cols_av = [

        "De (m)",
        "Até (m)",
        "Avanço (m)",
        "Recuperado (m)",
        "Acumulado (m)",
        "Recuperação (%)",
        "Material Perfurado",

    ]

    for c_idx, col_name in enumerate(
        cols_av,
        start=1
    ):

        cell = ws.cell(
            row=row_idx,
            column=c_idx,
            value=col_name
        )

        cell.fill = fill_header

        cell.font = font_header

        cell.alignment = Alignment(
            horizontal="center"
        )

        cell.border = thin_border


    row_idx += 1

    for _, r in df_avancos.iterrows():

        ws.cell(
            row=row_idx,
            column=1,
            value=r["de_m"]
        ).border = thin_border

        ws.cell(
            row=row_idx,
            column=2,
            value=r["ate_m"]
        ).border = thin_border

        ws.cell(
            row=row_idx,
            column=3,
            value=r["avanco_m"]
        ).border = thin_border

        ws.cell(
            row=row_idx,
            column=4,
            value=r["recuperado_m"]
        ).border = thin_border

        ws.cell(
            row=row_idx,
            column=5,
            value=r["acumulado_m"]
        ).border = thin_border


        c_pct = ws.cell(
            row=row_idx,
            column=6,
            value=f"{r['porcentagem']:.1f}%"
        )

        c_pct.border = thin_border

        if r["porcentagem"] < 80.0:

            c_pct.fill = PatternFill(
                start_color="FCE4D6",
                end_color="FCE4D6",
                fill_type="solid"
            )


        ws.cell(
            row=row_idx,
            column=7,
            value=r["material"]
        ).border = thin_border

        row_idx += 1


    # --------------------------------------------------------
    # ATIVIDADES
    # --------------------------------------------------------

    row_idx += 2

    ws.cell(
        row=row_idx,
        column=1,
        value="ATIVIDADES E TEMPOS"
    ).font = font_bold

    row_idx += 1


    cols_hor = [

        "Código",
        "Grupo",
        "Atividade",
        "Classificação",
        "Inicial",
        "Final",
        "Tempo (h)",
        "Horímetro",
        "Observação",

    ]


    for c_idx, col_name in enumerate(
        cols_hor,
        start=1
    ):

        cell = ws.cell(
            row=row_idx,
            column=c_idx,
            value=col_name
        )

        cell.fill = fill_header

        cell.font = font_header

        cell.border = thin_border


    row_idx += 1


    for _, r in df_horarios.iterrows():

        valores = [

            r.get("codigo", ""),
            r.get("grupo", ""),
            r.get("atividade", ""),
            r.get("classificacao", ""),
            r.get("hora_inicio", ""),
            r.get("hora_fim", ""),
            r.get("tempo_horas", 0),
            r.get("horimetro", ""),
            r.get("observacao", ""),

        ]


        for col_idx, valor in enumerate(
            valores,
            start=1
        ):

            cell = ws.cell(
                row=row_idx,
                column=col_idx,
                value=valor
            )

            cell.border = thin_border


        row_idx += 1


    # --------------------------------------------------------
    # RESUMO OPERACIONAL
    # --------------------------------------------------------

    row_idx += 2

    ws.cell(
        row=row_idx,
        column=1,
        value="RESUMO OPERACIONAL"
    ).font = font_bold

    row_idx += 1


    ws.cell(
        row=row_idx,
        column=1,
        value="Classificação"
    )

    ws.cell(
        row=row_idx,
        column=2,
        value="Horas"
    )


    ws.cell(
        row=row_idx,
        column=1
    ).fill = fill_header

    ws.cell(
        row=row_idx,
        column=2
    ).fill = fill_header

    ws.cell(
        row=row_idx,
        column=1
    ).font = font_header

    ws.cell(
        row=row_idx,
        column=2
    ).font = font_header


    row_idx += 1


    for classificacao, horas in resumo_operacional.items():

        ws.cell(
            row=row_idx,
            column=1,
            value=classificacao
        )

        ws.cell(
            row=row_idx,
            column=2,
            value=horas
        )

        ws.cell(
            row=row_idx,
            column=1
        ).border = thin_border

        ws.cell(
            row=row_idx,
            column=2
        ).border = thin_border

        row_idx += 1


    # --------------------------------------------------------
    # INSUMOS
    # --------------------------------------------------------

    row_idx += 2

    ws.cell(
        row=row_idx,
        column=1,
        value="INSUMOS UTILIZADOS"
    ).font = font_bold

    row_idx += 1


    ws.cell(
        row=row_idx,
        column=1,
        value="Item / Descrição"
    )

    ws.cell(
        row=row_idx,
        column=2,
        value="Quantidade"
    )


    for coluna in [1, 2]:

        ws.cell(
            row=row_idx,
            column=coluna
        ).fill = fill_header

        ws.cell(
            row=row_idx,
            column=coluna
        ).font = font_header

        ws.cell(
            row=row_idx,
            column=coluna
        ).border = thin_border


    row_idx += 1


    for _, r in df_insumos.iterrows():

        ws.cell(
            row=row_idx,
            column=1,
            value=r["item"]
        ).border = thin_border

        ws.cell(
            row=row_idx,
            column=2,
            value=r["quantidade"]
        ).border = thin_border

        row_idx += 1


    # --------------------------------------------------------
    # AJUSTE DE COLUNAS
    # --------------------------------------------------------

    for col in ws.columns:

        try:

            max_len = max(
                len(
                    str(
                        cell.value or ""
                    )
                )
                for cell in col
            )

            col_letter = get_column_letter(
                col[0].column
            )

            ws.column_dimensions[
                col_letter
            ].width = max(
                max_len + 3,
                12
            )

        except Exception:
            pass


    output = io.BytesIO()

    wb.save(output)

    output.seek(0)

    return output


# ============================================================
# FUNÇÕES DE CARREGAMENTO
# ============================================================

def obter_furos():

    conn = get_db()

    df = pd.read_sql_query(
        """
        SELECT furo
        FROM boletins
        ORDER BY furo ASC
        """,
        conn
    )

    conn.close()

    if df.empty:
        return []

    return df["furo"].tolist()


def carregar_boletim(furo):

    conn = get_db()

    c = conn.cursor()

    c.execute(
        """
        SELECT *
        FROM boletins
        WHERE furo = ?
        """,
        (furo,)
    )

    cabecalho = c.fetchone()


    df_avancos = pd.read_sql_query(
        """
        SELECT *
        FROM avancos
        WHERE furo = ?
        ORDER BY id ASC
        """,
        conn,
        params=(furo,)
    )


    df_horarios = pd.read_sql_query(
        """
        SELECT *
        FROM horarios
        WHERE furo = ?
        ORDER BY id ASC
        """,
        conn,
        params=(furo,)
    )


    df_insumos = pd.read_sql_query(
        """
        SELECT *
        FROM insumos
        WHERE furo = ?
        ORDER BY id ASC
        """,
        conn,
        params=(furo,)
    )


    conn.close()

    return (
        cabecalho,
        df_avancos,
        df_horarios,
        df_insumos
    )


# ============================================================
# SESSION STATE
# ============================================================

if "sb_de" not in st.session_state:
    st.session_state["sb_de"] = 0.0

if "sb_ate" not in st.session_state:
    st.session_state["sb_ate"] = 0.0

if "sb_recuperado" not in st.session_state:
    st.session_state["sb_recuperado"] = 0.0


# ============================================================
# BARRA LATERAL
# ============================================================

with st.sidebar:

    st.title(
        "📋 Gestão de Boletins"
    )


    lista_furos = obter_furos()


    furo_selecionado = (
        st.selectbox(
            "📂 Selecionar Boletim Existente:",
            lista_furos
        )
        if lista_furos
        else None
    )


    st.markdown("---")

    st.subheader(
        "🆕 Novo Boletim"
    )


    novo_furo_id = st.text_input(
        "Identificação do Furo",
        placeholder="Ex: DHAB 109"
    )


    if st.button(
        "➕ Criar Boletim",
        use_container_width=True
    ):

        if novo_furo_id:

            if novo_furo_id not in lista_furos:

                conn = get_db()

                c = conn.cursor()

                c.execute(
                    """
                    INSERT INTO boletins
                    (
                        furo,
                        data,
                        modelo_sonda,
                        num_sonda,
                        turno,
                        cliente,
                        area,
                        azimute,
                        angulo
                    )
                    VALUES
                    (
                        ?,
                        ?,
                        '',
                        '',
                        '',
                        '',
                        '',
                        0,
                        0
                    )
                    """,
                    (
                        novo_furo_id,
                        datetime.today().strftime(
                            "%d/%m/%Y"
                        ),
                    )
                )


                conn.commit()

                conn.close()


                st.success(
                    f"Boletim '{novo_furo_id}' criado!"
                )

                st.rerun()

            else:

                st.warning(
                    "Este furo já existe."
                )


    # --------------------------------------------------------
    # ADICIONAR MANOBRA
    # --------------------------------------------------------

    if furo_selecionado:

        st.markdown("---")

        st.subheader(
            "⛏️ Adicionar Avanço / Manobra"
        )


        def on_change_de_ate():

            novo_avanco = max(
                0.0,
                st.session_state["sb_ate"]
                - st.session_state["sb_de"]
            )

            st.session_state[
                "sb_recuperado"
            ] = round(
                novo_avanco,
                2
            )


        st.number_input(
            "De (m)",
            min_value=0.0,
            step=0.1,
            key="sb_de",
            on_change=on_change_de_ate
        )


        st.number_input(
            "Até (m)",
            min_value=0.0,
            step=0.1,
            key="sb_ate",
            on_change=on_change_de_ate
        )


        st.number_input(
            "Recuperado (m)",
            min_value=0.0,
            step=0.1,
            key="sb_recuperado"
        )


        sb_mat = st.text_input(
            "Material Perfurado",
            value=""
        )


        sb_avanco = max(
            0.0,
            round(
                st.session_state["sb_ate"]
                - st.session_state["sb_de"],
                2
            )
        )


        recuperado_val = round(
            st.session_state["sb_recuperado"],
            2
        )


        rec_anterior = (
            obter_total_recuperado_existente(
                furo_selecionado
            )
        )


        sb_acumulado = round(
            rec_anterior
            + recuperado_val,
            2
        )


        sb_pct = (
            round(
                recuperado_val
                / sb_avanco
                * 100,
                2
            )
            if sb_avanco > 0
            else 0.0
        )


        col_m1, col_m2 = st.columns(2)


        col_m1.metric(
            "Avanço Manobra",
            f"{sb_avanco:.2f} m"
        )


        col_m2.metric(
            "Recuperação Total",
            f"{sb_acumulado:.2f} m"
        )


        st.caption(
            f"📊 Recuperação da Manobra: {sb_pct:.1f}%"
        )


        if st.button(
            "💾 Inserir Manobra",
            use_container_width=True
        ):

            if (
                st.session_state["sb_ate"]
                >= st.session_state["sb_de"]
            ):

                conn = get_db()

                c = conn.cursor()


                c.execute(
                    """
                    INSERT INTO avancos
                    (
                        furo,
                        de_m,
                        ate_m,
                        avanco_m,
                        recuperado_m,
                        acumulado_m,
                        porcentagem,
                        material
                    )
                    VALUES
                    (
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?,
                        ?
                    )
                    """,
                    (
                        furo_selecionado,
                        st.session_state["sb_de"],
                        st.session_state["sb_ate"],
                        sb_avanco,
                        recuperado_val,
                        sb_acumulado,
                        sb_pct,
                        sb_mat,
                    )
                )


                conn.commit()

                conn.close()


                st.success(
                    "Manobra registrada com sucesso!"
                )

                st.rerun()

            else:

                st.error(
                    "O valor 'Até' não pode ser menor que 'De'."
                )


# ============================================================
# ÁREA PRINCIPAL
# ============================================================

if furo_selecionado:


    (
        cabecalho,
        df_avancos,
        df_horarios,
        df_insumos
    ) = carregar_boletim(
        furo_selecionado
    )


    st.title(
        f"📄 Boletim de Sondagem Rotativa: {furo_selecionado}"
    )


    # --------------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------------

    with st.expander(
        "📌 Informações Gerais do Furo e Equipamento",
        expanded=True
    ):


        col1, col2, col3, col4 = st.columns(4)


        data = col1.text_input(
            "Data",
            value=cabecalho[1] or ""
        )


        cliente = col2.text_input(
            "Cliente",
            value=cabecalho[5] or ""
        )


        area = col3.text_input(
            "Área",
            value=cabecalho[6] or ""
        )


        turno = col4.text_input(
            "Turno",
            value=cabecalho[4] or ""
        )


        col5, col6, col7, col8 = st.columns(4)


        sonda = col5.text_input(
            "Modelo Sonda",
            value=cabecalho[2] or ""
        )


        num_sonda = col6.text_input(
            "Nº Sonda",
            value=cabecalho[3] or ""
        )


        azimute = col7.number_input(
            "Azimute (°)",
            value=float(
                cabecalho[7] or 0.0
            )
        )


        angulo = col8.number_input(
            "Ângulo / Dip (°)",
            value=float(
                cabecalho[8] or 0.0
            )
        )


        st.markdown(
            "**Peça de Corte e Revestimento**"
        )


        (
            col9,
            col10,
            col11,
            col12,
            col13
        ) = st.columns(5)


        diam_peca = col9.text_input(
            "Diâm. Peça",
            value=cabecalho[9] or "NQ"
        )


        coroa = col10.text_input(
            "Nº Coroa",
            value=cabecalho[10] or ""
        )


        calib = col11.text_input(
            "Nº Calibrador",
            value=cabecalho[11] or ""
        )


        rev_diam = col12.text_input(
            "Diâm. Revestimento",
            value=cabecalho[12] or ""
        )


        caixas = col13.number_input(
            "Última Caixa Nº",
            value=int(
                cabecalho[15] or 0
            )
        )


        if st.button(
            "💾 Salvar Cabeçalho",
            use_container_width=True
        ):

            conn = get_db()

            c = conn.cursor()


            c.execute(
                """
                UPDATE boletins SET

                    data=?,
                    cliente=?,
                    area=?,
                    turno=?,
                    modelo_sonda=?,
                    num_sonda=?,
                    azimute=?,
                    angulo=?,
                    diam_peca=?,
                    coroa_num=?,
                    calib_num=?,
                    revest_diam=?,
                    num_caixa=?

                WHERE furo=?
                """,
                (
                    data,
                    cliente,
                    area,
                    turno,
                    sonda,
                    num_sonda,
                    azimute,
                    angulo,
                    diam_peca,
                    coroa,
                    calib,
                    rev_diam,
                    caixas,
                    furo_selecionado,
                )
            )


            conn.commit()

            conn.close()


            st.success(
                "Cabeçalho atualizado!"
            )

            st.rerun()


    # ========================================================
    # PERFURAÇÃO
    # ========================================================

    st.subheader(
        "📊 Perfuração e Recuperação"
    )


    if not df_avancos.empty:

        df_avancos["avanco_m"] = (
            df_avancos["ate_m"]
            - df_avancos["de_m"]
        )


        df_avancos["acumulado_m"] = (
            df_avancos[
                "recuperado_m"
            ].cumsum()
        )


        df_avancos["porcentagem"] = (
            df_avancos.apply(
                lambda r:
                round(
                    r["recuperado_m"]
                    / r["avanco_m"]
                    * 100,
                    2
                )
                if r["avanco_m"] > 0
                else 0.0,
                axis=1
            )
        )


    df_editado_avancos = st.data_editor(

        df_avancos,

        num_rows="dynamic",

        use_container_width=True,

        key=f"editor_av_{furo_selecionado}",

        column_config={

            "id":
                st.column_config.NumberColumn(
                    "ID",
                    disabled=True
                ),

            "furo":
                st.column_config.TextColumn(
                    "Furo",
                    disabled=True
                ),

            "de_m":
                st.column_config.NumberColumn(
                    "De (m)",
                    format="%.2f"
                ),

            "ate_m":
                st.column_config.NumberColumn(
                    "Até (m)",
                    format="%.2f"
                ),

            "avanco_m":
                st.column_config.NumberColumn(
                    "Avanço (m) ⚡",
                    format="%.2f",
                    disabled=True
                ),

            "recuperado_m":
                st.column_config.NumberColumn(
                    "Recuperado (m)",
                    format="%.2f"
                ),

            "acumulado_m":
                st.column_config.NumberColumn(
                    "Recuperação Total (m) ⚡",
                    format="%.2f",
                    disabled=True
                ),

            "porcentagem":
                st.column_config.NumberColumn(
                    "Recuperação (%) ⚡",
                    format="%.2f %%",
                    disabled=True
                ),

            "material":
                st.column_config.TextColumn(
                    "Material Perfurado"
                ),

        }
    )


    if not df_editado_avancos.empty:

        df_editado_avancos["avanco_m"] = (
            df_editado_avancos["ate_m"]
            - df_editado_avancos["de_m"]
        )


        df_editado_avancos["acumulado_m"] = (
            df_editado_avancos[
                "recuperado_m"
            ].cumsum()
        )


        df_editado_avancos["porcentagem"] = (
            df_editado_avancos.apply(
                lambda r:
                (
                    r["recuperado_m"]
                    / r["avanco_m"]
                    * 100
                )
                if r["avanco_m"] > 0
                else 0.0,
                axis=1
            )
        )


    total_av = (
        df_editado_avancos[
            "avanco_m"
        ].sum()
        if not df_editado_avancos.empty
        else 0.0
    )


    total_rec = (
        df_editado_avancos[
            "recuperado_m"
        ].sum()
        if not df_editado_avancos.empty
        else 0.0
    )


    rec_med = (
        total_rec
        / total_av
        * 100
        if total_av > 0
        else 0.0
    )


    m1, m2, m3 = st.columns(3)


    m1.metric(
        "Avanço Total",
        f"{total_av:.2f} m"
    )


    m2.metric(
        "Recuperação Total",
        f"{total_rec:.2f} m"
    )


    m3.metric(
        "Recuperação Média",
        f"{rec_med:.2f} %"
    )


    # ========================================================
    # ATIVIDADES E HORAS
    # ========================================================

    st.markdown("---")

    st.subheader(
        "⏱️ Atividades, Serviços e Horas"
    )


    # Garante que todas as colunas existam

    colunas_horarios = {

        "codigo": "",
        "grupo": "",
        "atividade": "",
        "classificacao": "",
        "descricao": "",
        "hora_inicio": "",
        "hora_fim": "",
        "tempo_horas": 0.0,
        "horimetro": "",
        "observacao": "",

    }


    for coluna, valor_padrao in colunas_horarios.items():

        if coluna not in df_horarios.columns:

            df_horarios[
                coluna
            ] = valor_padrao


    if not df_horarios.empty:

        df_horarios["tempo_horas"] = (
            df_horarios.apply(
                lambda r:
                calcular_diferenca_horas(
                    r["hora_inicio"],
                    r["hora_fim"]
                ),
                axis=1
            )
        )


    st.info(
        "💡 Informe o código, a atividade e os horários. "
        "A duração e os indicadores serão calculados automaticamente."
    )


    df_editado_horarios = st.data_editor(

        df_horarios,

        num_rows="dynamic",

        use_container_width=True,

        key=f"editor_hor_{furo_selecionado}",

        column_config={

            "id":
                st.column_config.NumberColumn(
                    "ID",
                    disabled=True
                ),

            "furo":
                st.column_config.TextColumn(
                    "Furo",
                    disabled=True
                ),

            "codigo":
                st.column_config.SelectboxColumn(
                    "Código",
                    options=list(
                        ATIVIDADES_PADRAO.keys()
                    )
                ),

            "grupo":
                st.column_config.TextColumn(
                    "Grupo"
                ),

            "atividade":
                st.column_config.TextColumn(
                    "Atividade"
                ),

            "classificacao":
                st.column_config.SelectboxColumn(
                    "Classificação",
                    options=[
                        "Operação Direta",
                        "Apoio Operacional",
                        "Manutenção Preventiva",
                        "Mecânica Corretiva",
                        "Parada Externa",
                        "Intervenção no Furo",
                        "Administrativo",
                        "Segurança",
                    ]
                ),

            "descricao":
                st.column_config.TextColumn(
                    "Descrição"
                ),

            "hora_inicio":
                st.column_config.TextColumn(
                    "Inicial (HH:MM)"
                ),

            "hora_fim":
                st.column_config.TextColumn(
                    "Final (HH:MM)"
                ),

            "tempo_horas":
                st.column_config.NumberColumn(
                    "Tempo (h) ⚡",
                    format="%.2f",
                    disabled=True
                ),

            "horimetro":
                st.column_config.TextColumn(
                    "Horímetro"
                ),

            "observacao":
                st.column_config.TextColumn(
                    "Observação"
                ),

        }
    )


    # Atualiza automaticamente os dados pelo código

    if not df_editado_horarios.empty:

        for index, row in df_editado_horarios.iterrows():

            codigo = str(
                row.get(
                    "codigo",
                    ""
                )
            ).strip()


            if codigo in ATIVIDADES_PADRAO:

                info = (
                    ATIVIDADES_PADRAO[
                        codigo
                    ]
                )


                # Só preenche automaticamente
                # caso os campos estejam vazios

                if not str(
                    row.get(
                        "grupo",
                        ""
                    )
                ).strip():

                    df_editado_horarios.at[
                        index,
                        "grupo"
                    ] = info["grupo"]


                if not str(
                    row.get(
                        "atividade",
                        ""
                    )
                ).strip():

                    df_editado_horarios.at[
                        index,
                        "atividade"
                    ] = info["atividade"]


                if not str(
                    row.get(
                        "classificacao",
                        ""
                    )
                ).strip():

                    df_editado_horarios.at[
                        index,
                        "classificacao"
                    ] = info["classificacao"]


            df_editado_horarios.at[
                index,
                "tempo_horas"
            ] = calcular_diferenca_horas(

                row.get(
                    "hora_inicio",
                    ""
                ),

                row.get(
                    "hora_fim",
                    ""
                )

            )


    # ========================================================
    # RESUMO AUTOMÁTICO
    # ========================================================

    resumo_operacional = (
        calcular_resumo_operacional(
            df_editado_horarios
        )
    )


    st.markdown("---")

    st.subheader(
        "📈 Resumo Automático do RDO"
    )


    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "🟢 Operação Direta",
        f"{resumo_operacional['Operação Direta']:.2f} h"
    )


    c2.metric(
        "🔵 Apoio Operacional",
        f"{resumo_operacional['Apoio Operacional']:.2f} h"
    )


    c3.metric(
        "🟡 Manutenção Preventiva",
        f"{resumo_operacional['Manutenção Preventiva']:.2f} h"
    )


    c4.metric(
        "🔴 Mecânica Corretiva",
        f"{resumo_operacional['Mecânica Corretiva']:.2f} h"
    )


    c5, c6, c7, c8 = st.columns(4)


    c5.metric(
        "🟠 Parada Externa",
        f"{resumo_operacional['Parada Externa']:.2f} h"
    )


    c6.metric(
        "🟣 Intervenção no Furo",
        f"{resumo_operacional['Intervenção no Furo']:.2f} h"
    )


    c7.metric(
        "⚪ Administrativo",
        f"{resumo_operacional['Administrativo']:.2f} h"
    )


    c8.metric(
        "🦺 Segurança",
        f"{resumo_operacional['Segurança']:.2f} h"
    )


    # ========================================================
    # INDICADORES OPERACIONAIS
    # ========================================================

    horas_operacao = (
        resumo_operacional[
            "Operação Direta"
        ]
    )


    horas_apoio = (
        resumo_operacional[
            "Apoio Operacional"
        ]
    )


    horas_manut_preventiva = (
        resumo_operacional[
            "Manutenção Preventiva"
        ]
    )


    horas_manut_corretiva = (
        resumo_operacional[
            "Mecânica Corretiva"
        ]
    )


    horas_parada = (

        resumo_operacional[
            "Apoio Operacional"
        ]

        +

        resumo_operacional[
            "Manutenção Preventiva"
        ]

        +

        resumo_operacional[
            "Mecânica Corretiva"
        ]

        +

        resumo_operacional[
            "Parada Externa"
        ]

        +

        resumo_operacional[
            "Intervenção no Furo"
        ]

        +

        resumo_operacional[
            "Administrativo"
        ]

        +

        resumo_operacional[
            "Segurança"
        ]

    )


    horas_programadas = (
        horas_operacao
        + horas_parada
    )


    disponibilidade_fisica = (

        (
            horas_programadas
            - horas_manut_corretiva
        )

        /

        horas_programadas

        * 100

        if horas_programadas > 0

        else 0.0

    )


    base_utilizacao = (
        horas_programadas
        - horas_manut_corretiva
    )


    utilizacao = (

        horas_operacao
        / base_utilizacao
        * 100

        if base_utilizacao > 0

        else 0.0

    )


    rop = (

        total_av
        / horas_operacao

        if horas_operacao > 0

        else 0.0

    )


    st.subheader(
        "⚙️ Indicadores Operacionais"
    )


    i1, i2, i3, i4, i5 = st.columns(5)


    i1.metric(
        "Horas Programadas",
        f"{horas_programadas:.2f} h"
    )


    i2.metric(
        "Horas de Operação",
        f"{horas_operacao:.2f} h"
    )


    i3.metric(
        "Horas de Parada",
        f"{horas_parada:.2f} h"
    )


    i4.metric(
        "Disponibilidade Física",
        f"{disponibilidade_fisica:.2f} %"
    )


    i5.metric(
        "Utilização",
        f"{utilizacao:.2f} %"
    )


    st.metric(
        "⚡ ROP",
        f"{rop:.2f} m/h"
    )


    # ========================================================
    # INSUMOS
    # ========================================================

    st.markdown("---")

    st.subheader(
        "⛽ Insumos Utilizados"
    )


    df_editado_insumos = st.data_editor(

        df_insumos,

        num_rows="dynamic",

        use_container_width=True,

        key=f"editor_ins_{furo_selecionado}",

        column_config={

            "id":
                st.column_config.NumberColumn(
                    "ID",
                    disabled=True
                ),

            "furo":
                st.column_config.TextColumn(
                    "Furo",
                    disabled=True
                ),

            "item":
                st.column_config.TextColumn(
                    "Descrição"
                ),

            "quantidade":
                st.column_config.NumberColumn(
                    "Quantidade",
                    format="%.2f"
                ),

        }
    )


    # ========================================================
    # BOTÕES
    # ========================================================

    st.markdown("---")


    col_btn1, col_btn2 = st.columns(2)


    # --------------------------------------------------------
    # SALVAR
    # --------------------------------------------------------

    with col_btn1:

        if st.button(
            "💾 Salvar Todas as Alterações",
            use_container_width=True
        ):


            conn = get_db()

            c = conn.cursor()


            # ------------------------------------------------
            # AVANÇOS
            # ------------------------------------------------

            c.execute(
                """
                DELETE FROM avancos
                WHERE furo = ?
                """,
                (furo_selecionado,)
            )


            acum_corr = 0.0


            if not df_editado_avancos.empty:

                for _, row in (
                    df_editado_avancos.iterrows()
                ):

                    av_m = (
                        float(
                            row["ate_m"]
                        )
                        -
                        float(
                            row["de_m"]
                        )
                    )


                    rec_m = float(
                        row["recuperado_m"]
                    )


                    acum_corr += rec_m


                    pct = (

                        rec_m
                        / av_m
                        * 100

                        if av_m > 0

                        else 0.0

                    )


                    c.execute(
                        """
                        INSERT INTO avancos
                        (
                            furo,
                            de_m,
                            ate_m,
                            avanco_m,
                            recuperado_m,
                            acumulado_m,
                            porcentagem,
                            material
                        )
                        VALUES
                        (
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?
                        )
                        """,
                        (
                            furo_selecionado,
                            row["de_m"],
                            row["ate_m"],
                            av_m,
                            rec_m,
                            acum_corr,
                            pct,
                            row.get(
                                "material",
                                ""
                            ),
                        )
                    )


            # ------------------------------------------------
            # HORÁRIOS
            # ------------------------------------------------

            c.execute(
                """
                DELETE FROM horarios
                WHERE furo = ?
                """,
                (furo_selecionado,)
            )


            if not df_editado_horarios.empty:

                for _, row in (
                    df_editado_horarios.iterrows()
                ):


                    codigo = str(
                        row.get(
                            "codigo",
                            ""
                        )
                    ).strip()


                    grupo = row.get(
                        "grupo",
                        ""
                    )


                    atividade = row.get(
                        "atividade",
                        ""
                    )


                    classificacao = row.get(
                        "classificacao",
                        ""
                    )


                    # Preenchimento automático
                    # pelo código

                    if codigo in ATIVIDADES_PADRAO:

                        info = (
                            ATIVIDADES_PADRAO[
                                codigo
                            ]
                        )


                        if not str(
                            grupo
                        ).strip():

                            grupo = info["grupo"]


                        if not str(
                            atividade
                        ).strip():

                            atividade = info["atividade"]


                        if not str(
                            classificacao
                        ).strip():

                            classificacao = (
                                info[
                                    "classificacao"
                                ]
                            )


                    tempo_calc = (
                        calcular_diferenca_horas(
                            row.get(
                                "hora_inicio",
                                ""
                            ),

                            row.get(
                                "hora_fim",
                                ""
                            )
                        )
                    )


                    c.execute(
                        """
                        INSERT INTO horarios
                        (
                            furo,
                            descricao,
                            hora_inicio,
                            hora_fim,
                            tempo_horas,
                            horimetro,
                            codigo,
                            grupo,
                            atividade,
                            classificacao,
                            observacao
                        )
                        VALUES
                        (
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?,
                            ?
                        )
                        """,
                        (
                            furo_selecionado,

                            row.get(
                                "descricao",
                                ""
                            ),

                            row.get(
                                "hora_inicio",
                                ""
                            ),

                            row.get(
                                "hora_fim",
                                ""
                            ),

                            tempo_calc,

                            row.get(
                                "horimetro",
                                ""
                            ),

                            codigo,

                            grupo,

                            atividade,

                            classificacao,

                            row.get(
                                "observacao",
                                ""
                            ),

                        )
                    )


            # ------------------------------------------------
            # INSUMOS
            # ------------------------------------------------

            c.execute(
                """
                DELETE FROM insumos
                WHERE furo = ?
                """,
                (furo_selecionado,)
            )


            if not df_editado_insumos.empty:

                for _, row in (
                    df_editado_insumos.iterrows()
                ):

                    c.execute(
                        """
                        INSERT INTO insumos
                        (
                            furo,
                            item,
                            quantidade
                        )
                        VALUES
                        (
                            ?,
                            ?,
                            ?
                        )
                        """,
                        (
                            furo_selecionado,
                            row.get(
                                "item",
                                ""
                            ),
                            row.get(
                                "quantidade",
                                0
                            ),
                        )
                    )


            conn.commit()

            conn.close()


            st.success(
                "✅ Dados salvos e atualizados com sucesso!"
            )

            st.rerun()


    # --------------------------------------------------------
    # EXCEL
    # --------------------------------------------------------

    with col_btn2:


        excel_data = gerar_excel_boletim(

            cabecalho,

            df_editado_avancos,

            df_editado_horarios,

            df_editado_insumos,

            resumo_operacional,

        )


        st.download_button(

            label=(
                "📥 Baixar Boletim em Excel Formatado"
            ),

            data=excel_data,

            file_name=(
                f"Boletim_Sondagem_"
                f"{furo_selecionado}.xlsx"
            ),

            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),

            use_container_width=True

        )


else:

    st.info(
        "👈 Selecione ou crie um novo boletim "
        "na barra lateral para iniciar a digitação."
    )
```
