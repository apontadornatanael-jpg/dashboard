import streamlit as st
import sqlite3
import pandas as pd

from datetime import date, datetime, time, timedelta
from io import BytesIO


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="DDH Campo",
    page_icon="⛏️",
    layout="wide"
)

DB = "ddh.db"


# ============================================================
# BANCO DE DADOS
# ============================================================

def conn():
    return sqlite3.connect(DB, check_same_thread=False)


def query(sql, params=()):
    c = conn()
    df = pd.read_sql_query(sql, c, params=params)
    c.close()
    return df


def execute(sql, params=()):
    c = conn()
    cur = c.cursor()

    cur.execute(sql, params)

    c.commit()

    last = cur.lastrowid

    c.close()

    return last


def init_db():

    c = conn()
    cur = c.cursor()

    # --------------------------------------------------------
    # COLABORADORES
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS colaboradores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            funcao TEXT,
            matricula TEXT,
            status TEXT DEFAULT 'Ativo'
        )
    """)


    # --------------------------------------------------------
    # EQUIPES
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS equipes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            supervisor_id INTEGER,
            sondador_id INTEGER,
            auxiliar1_id INTEGER,
            auxiliar2_id INTEGER,
            status TEXT DEFAULT 'Ativa'
        )
    """)


    # --------------------------------------------------------
    # SONDAS
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sondas(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            modelo TEXT,
            fabricante TEXT,
            patrimonio TEXT,
            equipe_id INTEGER,
            status TEXT DEFAULT 'Operando'
        )
    """)


    # --------------------------------------------------------
    # FUROS
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS furos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identificacao TEXT UNIQUE NOT NULL,
            projeto TEXT,
            cliente TEXT,
            local TEXT,
            coord_e REAL,
            coord_n REAL,
            cota REAL,
            azimute REAL,
            dip REAL,
            status TEXT DEFAULT 'Em andamento'
        )
    """)


    # --------------------------------------------------------
    # ATIVIDADES
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS atividades(
            codigo INTEGER PRIMARY KEY,
            grupo TEXT NOT NULL,
            atividade TEXT NOT NULL,
            classificacao TEXT NOT NULL
        )
    """)


    # --------------------------------------------------------
    # BOLETINS
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS boletins(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            turno TEXT,
            projeto TEXT,
            cliente TEXT,
            sonda_id INTEGER,
            equipe_id INTEGER,
            furo_id INTEGER,
            horimetro_inicial REAL,
            horimetro_final REAL,
            observacoes TEXT,
            criado_em TEXT
        )
    """)


    # --------------------------------------------------------
    # MANOBRAS
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS manobras(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            boletim_id INTEGER NOT NULL,
            numero INTEGER,
            de_m REAL,
            ate_m REAL,
            recuperado_m REAL,
            dip REAL,
            qaqc TEXT,
            perfil TEXT,
            coroa TEXT,
            revestimento TEXT,
            fluido TEXT
        )
    """)


    # --------------------------------------------------------
    # APONTAMENTOS
    # --------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS apontamentos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            boletim_id INTEGER NOT NULL,
            codigo_atividade INTEGER,
            hora_inicio TEXT,
            hora_fim TEXT,
            horas REAL,
            horimetro REAL,
            observacao TEXT
        )
    """)

    c.commit()
    c.close()

    # Corrige e cria os códigos de atividades
    seed_activities()


# ============================================================
# CÓDIGOS DE ATIVIDADES
# ============================================================

def seed_activities():

    rows = [

        (
            1,
            "Segurança e Gestão",
            "DDS / Segurança",
            "SEGURANÇA"
        ),

        (
            2,
            "Administrativo",
            "Reunião / Administrativo",
            "ADMINISTRATIVO"
        ),

        (
            3,
            "Logística",
            "Deslocamento / Logística",
            "APOIO OPERACIONAL"
        ),

        (
            4,
            "Fluidos",
            "Preparação de fluido",
            "APOIO OPERACIONAL"
        ),

        (
            5,
            "Praça e Acesso",
            "Preparação de praça / acesso",
            "APOIO OPERACIONAL"
        ),

        (
            6,
            "Mobilização",
            "Mobilização / desmobilização",
            "APOIO OPERACIONAL"
        ),

        (
            7,
            "Manutenção Preventiva",
            "Manutenção preventiva",
            "MANUTENÇÃO PREVENTIVA"
        ),

        (
            8,
            "Manutenção Corretiva",
            "Manutenção mecânica corretiva",
            "MECÂNICA CORRETIVA"
        ),

        (
            9,
            "Suprimentos",
            "Aguardar / receber suprimentos",
            "PARADA EXTERNA"
        ),

        (
            10,
            "Apoio Externo",
            "Aguardar apoio externo",
            "PARADA EXTERNA"
        ),

        (
            11,
            "Condições Externas",
            "Chuva / condição climática",
            "PARADA EXTERNA"
        ),

        (
            12,
            "Contratante",
            "Aguardar liberação do contratante",
            "PARADA EXTERNA"
        ),

        (
            13,
            "Serviços Especializados",
            "Serviço especializado",
            "APOIO OPERACIONAL"
        ),

        (
            14,
            "Produção",
            "Perfuração",
            "OPERAÇÃO DIRETA"
        ),

        (
            15,
            "Produção",
            "Manobra",
            "OPERAÇÃO DIRETA"
        ),

        (
            16,
            "Produção",
            "Troca de haste / tubo",
            "OPERAÇÃO DIRETA"
        ),

        (
            17,
            "Produção",
            "Condicionamento do furo",
            "OPERAÇÃO DIRETA"
        ),

        (
            18,
            "Produção",
            "Furando e manobrando",
            "OPERAÇÃO DIRETA"
        ),

        (
            19,
            "Operação",
            "Preparação operacional",
            "APOIO OPERACIONAL"
        ),

        (
            20,
            "Operação",
            "Limpeza e organização",
            "APOIO OPERACIONAL"
        ),

        (
            21,
            "Ferramental",
            "Troca de ferramental",
            "APOIO OPERACIONAL"
        ),

        (
            22,
            "Ferramental",
            "Inspeção de ferramental",
            "APOIO OPERACIONAL"
        ),

        (
            23,
            "Revestimento",
            "Instalação / retirada de revestimento",
            "INTERVENÇÃO NO FURO"
        ),

        (
            24,
            "Intervenção",
            "Desvio / intervenção no furo",
            "INTERVENÇÃO NO FURO"
        ),

        (
            25,
            "Intervenção",
            "Obstrução / perda no furo",
            "INTERVENÇÃO NO FURO"
        ),

        (
            26,
            "Segurança e Gestão",
            "Treinamento / gestão",
            "SEGURANÇA"
        ),

        (
            27,
            "Administrativo",
            "Encerramento / relatório",
            "ADMINISTRATIVO"
        )

    ]


    c = conn()
    cur = c.cursor()


    for codigo, grupo, atividade, classificacao in rows:

        cur.execute("""

            INSERT INTO atividades
            (
                codigo,
                grupo,
                atividade,
                classificacao
            )

            VALUES (?, ?, ?, ?)

            ON CONFLICT(codigo)

            DO UPDATE SET

                grupo = CASE

                    WHEN atividades.grupo IS NULL
                    OR TRIM(atividades.grupo) = ''

                    THEN excluded.grupo

                    ELSE atividades.grupo

                END,


                atividade = CASE

                    WHEN atividades.atividade IS NULL
                    OR TRIM(atividades.atividade) = ''

                    THEN excluded.atividade

                    ELSE atividades.atividade

                END,


                classificacao = CASE

                    WHEN atividades.classificacao IS NULL
                    OR TRIM(atividades.classificacao) = ''

                    THEN excluded.classificacao

                    ELSE atividades.classificacao

                END

        """, (

            codigo,
            grupo,
            atividade,
            classificacao

        ))


    c.commit()
    c.close()


# Inicializa banco
init_db()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def horas_intervalo(inicio, fim):

    if not inicio or not fim:
        return 0.0

    a = datetime.combine(
        date.today(),
        inicio
    )

    b = datetime.combine(
        date.today(),
        fim
    )

    # Turno passando da meia noite
    if b < a:
        b += timedelta(days=1)

    return round(
        (b - a).total_seconds() / 3600,
        2
    )


def activity_row(codigo):

    df = query(
        """
        SELECT *
        FROM atividades
        WHERE codigo=?
        """,
        (int(codigo),)
    )

    if df.empty:
        return {}

    return df.iloc[0].to_dict()


def entity_options(table, label_col, where=None):

    sql = f"""
        SELECT *
        FROM {table}
    """

    if where:
        sql += " WHERE " + where

    df = query(sql)

    if df.empty:
        return df, {}

    mapping = {}

    for _, r in df.iterrows():

        mapping[
            int(r["id"])
        ] = str(r[label_col])

    return df, mapping


def safe_name(df, col, idv):

    if pd.isna(idv):
        return ""

    try:

        row = df[
            df["id"] == int(idv)
        ]

        if row.empty:
            return ""

        return str(
            row.iloc[0][col]
        )

    except Exception:
        return ""


def delete(table, idv):

    execute(
        f"""
        DELETE FROM {table}
        WHERE id=?
        """,
        (int(idv),)
    )


# ============================================================
# GERAÇÃO EXCEL
# ============================================================

def excel_boletim(boletim_id):

    from openpyxl import Workbook

    from openpyxl.styles import (
        Font,
        PatternFill,
        Alignment,
        Border,
        Side
    )

    from openpyxl.utils import get_column_letter


    boletim_df = query(
        """
        SELECT *
        FROM boletins
        WHERE id=?
        """,
        (boletim_id,)
    )


    if boletim_df.empty:
        return None


    b = boletim_df.iloc[0].to_dict()


    man = query(
        """
        SELECT *
        FROM manobras
        WHERE boletim_id=?
        ORDER BY numero
        """,
        (boletim_id,)
    )


    ap = query(
        """
        SELECT
            p.*,
            a.grupo,
            a.atividade,
            a.classificacao

        FROM apontamentos p

        LEFT JOIN atividades a
        ON p.codigo_atividade = a.codigo

        WHERE p.boletim_id=?

        ORDER BY p.id
        """,
        (boletim_id,)
    )


    sondas = query(
        """
        SELECT *
        FROM sondas
        """
    )

    equipes = query(
        """
        SELECT *
        FROM equipes
        """
    )

    furos = query(
        """
        SELECT *
        FROM furos
        """
    )


    wb = Workbook()

    ws = wb.active

    ws.title = "BOLETIM_DDH"


    # --------------------------------------------------------
    # ESTILOS
    # --------------------------------------------------------

    dark = PatternFill(
        "solid",
        fgColor="17365D"
    )

    light = PatternFill(
        "solid",
        fgColor="D9EAF7"
    )

    white = Font(
        color="FFFFFF",
        bold=True,
        size=14
    )

    bold = Font(
        bold=True
    )

    thin = Side(
        style="thin",
        color="808080"
    )


    # --------------------------------------------------------
    # TÍTULO
    # --------------------------------------------------------

    ws.merge_cells("A1:J1")

    ws["A1"] = (
        "BOLETIM DE SONDAGEM "
        "ROTATIVA DIAMANTADA - DDH"
    )

    ws["A1"].fill = dark

    ws["A1"].font = white

    ws["A1"].alignment = Alignment(
        horizontal="center"
    )


    # --------------------------------------------------------
    # INFORMAÇÕES
    # --------------------------------------------------------

    sonda = safe_name(
        sondas,
        "codigo",
        b.get("sonda_id")
    )

    equipe = safe_name(
        equipes,
        "codigo",
        b.get("equipe_id")
    )

    furo = safe_name(
        furos,
        "identificacao",
        b.get("furo_id")
    )


    info = [

        ("Data", b.get("data")),

        ("Turno", b.get("turno")),

        ("Projeto", b.get("projeto")),

        ("Cliente", b.get("cliente")),

        ("Sonda", sonda),

        ("Equipe", equipe),

        ("Furo", furo),

        (
            "Horímetro inicial",
            b.get("horimetro_inicial")
        ),

        (
            "Horímetro final",
            b.get("horimetro_final")
        )

    ]


    r = 3


    for label, value in info:

        ws.cell(
            r,
            1,
            label
        ).font = bold

        ws.cell(
            r,
            2,
            value
        )

        r += 1


    # ========================================================
    # MANOBRAS
    # ========================================================

    r += 1


    ws.cell(
        r,
        1,
        "MANOBRAS / PERFURAÇÃO"
    ).fill = dark


    ws.cell(
        r,
        1
    ).font = white


    ws.merge_cells(
        start_row=r,
        start_column=1,
        end_row=r,
        end_column=10
    )


    r += 1


    heads = [

        "Nº",
        "De (m)",
        "Até (m)",
        "Avanço (m)",
        "Recuperado (m)",
        "Rec. %",
        "DIP",
        "QAQC",
        "Perfil",
        "Fluido"

    ]


    for c, h in enumerate(heads, 1):

        ws.cell(
            r,
            c,
            h
        ).fill = light

        ws.cell(
            r,
            c
        ).font = bold


    for _, x in man.iterrows():

        r += 1


        av = (
            float(x["ate_m"] or 0)
            -
            float(x["de_m"] or 0)
        )


        rec = (
            float(x["recuperado_m"] or 0)
            /
            av
            *
            100
        ) if av else 0


        vals = [

            x["numero"],

            x["de_m"],

            x["ate_m"],

            av,

            x["recuperado_m"],

            rec,

            x["dip"],

            x["qaqc"],

            x["perfil"],

            x["fluido"]

        ]


        for c, v in enumerate(vals, 1):

            ws.cell(
                r,
                c,
                v
            )


    # ========================================================
    # ATIVIDADES
    # ========================================================

    r += 2


    ws.cell(
        r,
        1,
        "ATIVIDADES / HORAS"
    ).fill = dark


    ws.cell(
        r,
        1
    ).font = white


    ws.merge_cells(
        start_row=r,
        start_column=1,
        end_row=r,
        end_column=9
    )


    r += 1


    heads = [

        "Código",
        "Grupo",
        "Atividade",
        "Classificação",
        "Início",
        "Fim",
        "Horas",
        "Horímetro",
        "Observação"

    ]


    for c, h in enumerate(heads, 1):

        ws.cell(
            r,
            c,
            h
        ).fill = light


        ws.cell(
            r,
            c
        ).font = bold


    for _, x in ap.iterrows():

        r += 1


        vals = [

            x["codigo_atividade"],

            x["grupo"],

            x["atividade"],

            x["classificacao"],

            x["hora_inicio"],

            x["hora_fim"],

            x["horas"],

            x["horimetro"],

            x["observacao"]

        ]


        for c, v in enumerate(vals, 1):

            ws.cell(
                r,
                c,
                v
            )


    # ========================================================
    # FORMATAÇÃO
    # ========================================================

    for row in ws.iter_rows():

        for cell in row:

            cell.border = Border(

                left=thin,
                right=thin,
                top=thin,
                bottom=thin

            )


            cell.alignment = Alignment(
                vertical="center"
            )


    widths = [

        12,
        20,
        28,
        22,
        18,
        15,
        12,
        20,
        25,
        20

    ]


    for i, w in enumerate(widths, 1):

        ws.column_dimensions[
            get_column_letter(i)
        ].width = w


    out = BytesIO()

    wb.save(out)

    return out.getvalue()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⛏️ DDH CAMPO")


page = st.sidebar.radio(

    "Menu",

    [

        "🏠 Painel DDH",
        "📝 Novo Boletim",
        "📋 Boletins Salvos",
        "👷 Colaboradores",
        "👥 Equipes",
        "🔩 Sondas",
        "⚙️ Cadastros"

    ]

)


# ========================================================
# PRODUÇÃO POR EQUIPE
# ========================================================

st.divider()

st.subheader(
    "👥 Produção por Equipe"
)


# --------------------------------------------------------
# PRODUÇÃO EM METROS POR EQUIPE
# --------------------------------------------------------

producao_metros = query(

    """

    SELECT

        e.id AS equipe_id,

        e.codigo AS equipe,

        e.nome AS nome_equipe,


        COALESCE(

            SUM(

                COALESCE(m.ate_m, 0)

                -

                COALESCE(m.de_m, 0)

            ),

            0

        ) AS metros,


        COALESCE(

            SUM(
                COALESCE(
                    m.recuperado_m,
                    0
                )
            ),

            0

        ) AS recuperado


    FROM equipes e


    LEFT JOIN boletins b

    ON b.equipe_id = e.id


    LEFT JOIN manobras m

    ON m.boletim_id = b.id


    WHERE e.status != 'Inativa'


    GROUP BY

        e.id,
        e.codigo,
        e.nome


    ORDER BY metros DESC

    """

)


# --------------------------------------------------------
# HORAS DE OPERAÇÃO POR EQUIPE
# --------------------------------------------------------

producao_horas = query(

    """

    SELECT

        e.id AS equipe_id,


        COALESCE(

            SUM(

                CASE

                    WHEN a.classificacao =
                    'OPERAÇÃO DIRETA'

                    THEN COALESCE(
                        p.horas,
                        0
                    )

                    ELSE 0

                END

            ),

            0

        ) AS horas_operacao


    FROM equipes e


    LEFT JOIN boletins b

    ON b.equipe_id = e.id


    LEFT JOIN apontamentos p

    ON p.boletim_id = b.id


    LEFT JOIN atividades a

    ON a.codigo =
    p.codigo_atividade


    WHERE e.status != 'Inativa'


    GROUP BY e.id


    """

)


# --------------------------------------------------------
# JUNTA PRODUÇÃO E HORAS
# --------------------------------------------------------

if not producao_metros.empty:


    producao_equipes = (

        producao_metros.merge(

            producao_horas,

            on="equipe_id",

            how="left"

        )

    )


    producao_equipes[
        "horas_operacao"
    ] = (

        producao_equipes[
            "horas_operacao"
        ].fillna(0)

    )


    # ----------------------------------------------------
    # RECUPERAÇÃO
    # ----------------------------------------------------

    producao_equipes[
        "Recuperação %"
    ] = (

        producao_equipes[
            "recuperado"
        ]

        /

        producao_equipes[
            "metros"
        ].replace(
            0,
            pd.NA
        )

        *
        100

    ).fillna(0)


    # ----------------------------------------------------
    # ROP
    # ----------------------------------------------------

    producao_equipes[
        "ROP (m/h)"
    ] = (

        producao_equipes[
            "metros"
        ]

        /

        producao_equipes[
            "horas_operacao"
        ].replace(
            0,
            pd.NA
        )

    ).fillna(0)


    # ----------------------------------------------------
    # TABELA
    # ----------------------------------------------------

    tabela_equipes = (

        producao_equipes[

            [

                "equipe",

                "nome_equipe",

                "metros",

                "recuperado",

                "Recuperação %",

                "horas_operacao",

                "ROP (m/h)"

            ]

        ].copy()

    )


    tabela_equipes.columns = [

        "Equipe",

        "Nome",

        "Metros",

        "Recuperado",

        "Recuperação %",

        "Horas Operação",

        "ROP (m/h)"

    ]


    tabela_equipes = (

        tabela_equipes.sort_values(

            "Metros",

            ascending=False

        )

    )


    # ====================================================
    # CARDS DAS EQUIPES
    # ====================================================

    equipes_com_producao = (

        tabela_equipes[

            tabela_equipes[
                "Metros"
            ] > 0

        ]

    )


    if not equipes_com_producao.empty:


        for _, eq in equipes_com_producao.iterrows():


            st.markdown(

                f"### 👷 {eq['Equipe']} - {eq['Nome']}"

            )


            cc = st.columns(4)


            cc[0].metric(

                "PRODUÇÃO",

                f"{eq['Metros']:.2f} m"

            )


            cc[1].metric(

                "RECUPERAÇÃO",

                f"{eq['Recuperação %']:.1f}%"

            )


            cc[2].metric(

                "HORAS OPERAÇÃO",

                f"{eq['Horas Operação']:.2f} h"

            )


            cc[3].metric(

                "ROP",

                f"{eq['ROP (m/h)']:.2f} m/h"

            )


    else:


        st.info(

            "Ainda não existem lançamentos "
            "de produção para as equipes."

        )


    # ====================================================
    # GRÁFICO
    # ====================================================

    st.subheader(
        "📊 Comparativo de Produção das Equipes"
    )


    grafico_producao = (

        tabela_equipes[

            [

                "Equipe",

                "Metros"

            ]

        ]

        .set_index(
            "Equipe"
        )

    )


    st.bar_chart(
        grafico_producao
    )


    # ====================================================
    # TABELA COMPLETA
    # ====================================================

    st.subheader(
        "📋 Resumo Geral por Equipe"
    )


    tabela_exibicao = (
        tabela_equipes.copy()
    )


    tabela_exibicao[
        "Metros"
    ] = tabela_exibicao[
        "Metros"
    ].round(2)


    tabela_exibicao[
        "Recuperado"
    ] = tabela_exibicao[
        "Recuperado"
    ].round(2)


    tabela_exibicao[
        "Recuperação %"
    ] = tabela_exibicao[
        "Recuperação %"
    ].round(1)


    tabela_exibicao[
        "Horas Operação"
    ] = tabela_exibicao[
        "Horas Operação"
    ].round(2)


    tabela_exibicao[
        "ROP (m/h)"
    ] = tabela_exibicao[
        "ROP (m/h)"
    ].round(2)


    st.dataframe(

        tabela_exibicao,

        use_container_width=True,

        hide_index=True

    )


else:


    st.info(
        "Ainda não existem equipes cadastradas."
    )
# ============================================================
# NOVO BOLETIM
# ============================================================

elif page == "📝 Novo Boletim":

    st.title(
        "📝 NOVO RDO / BOLETIM DDH"
    )


    df_s, map_s = entity_options(

        "sondas",
        "codigo",
        "status != 'Inativa'"

    )


    df_e, map_e = entity_options(

        "equipes",
        "codigo",
        "status != 'Inativa'"

    )


    df_f, map_f = entity_options(

        "furos",
        "identificacao"

    )


    if (

        df_s.empty
        or
        df_e.empty
        or
        df_f.empty

    ):

        st.warning(

            "Cadastre pelo menos uma "
            "Sonda, uma Equipe e um Furo "
            "antes de criar o boletim."

        )

        st.stop()


    if (
        "boletim_edit_id"
        not in
        st.session_state
    ):

        st.session_state.boletim_edit_id = None


    # --------------------------------------------------------
    # CABEÇALHO
    # --------------------------------------------------------

    with st.form("cabecalho"):


        a, b, c, d = st.columns(4)


        data_b = a.date_input(

            "Data",

            value=date.today()

        )


        turno = b.selectbox(

            "Turno",

            [

                "Diurno",
                "Noturno"

            ]

        )


        sonda_id = c.selectbox(

            "Sonda",

            list(
                map_s.keys()
            ),

            format_func=lambda x:
                map_s[x]

        )


        equipe_padrao = None


        row_s = df_s[
            df_s["id"]
            ==
            sonda_id
        ]


        if (
            not row_s.empty
            and
            pd.notna(
                row_s.iloc[0]["equipe_id"]
            )
        ):

            equipe_padrao = int(

                row_s.iloc[0][
                    "equipe_id"
                ]

            )


        idx_e = (

            list(
                map_e.keys()
            ).index(
                equipe_padrao
            )

            if equipe_padrao in map_e

            else 0

        )


        equipe_id = d.selectbox(

            "Equipe",

            list(
                map_e.keys()
            ),

            index=idx_e,

            format_func=lambda x:
                map_e[x]

        )


        a, b, c, d = st.columns(4)


        furo_id = a.selectbox(

            "Furo",

            list(
                map_f.keys()
            ),

            format_func=lambda x:
                map_f[x]

        )


        projeto = b.text_input(
            "Projeto"
        )


        cliente = c.text_input(
            "Cliente"
        )


        h_ini = d.number_input(

            "Horímetro Inicial",

            min_value=0.0,

            step=0.1

        )


        h_fim = st.number_input(

            "Horímetro Final",

            min_value=0.0,

            step=0.1

        )


        observacoes = st.text_area(
            "Observações gerais"
        )


        salvar = st.form_submit_button(

            "💾 Criar Boletim",

            type="primary"

        )


    if salvar:


        if (
            h_fim
            and
            h_fim < h_ini
        ):

            st.error(

                "Horímetro final "
                "não pode ser menor "
                "que o inicial."

            )


        else:


            bid = execute(

                """

                INSERT INTO boletins
                (
                    data,
                    turno,
                    projeto,
                    cliente,
                    sonda_id,
                    equipe_id,
                    furo_id,
                    horimetro_inicial,
                    horimetro_final,
                    observacoes,
                    criado_em
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

                    str(data_b),

                    turno,

                    projeto,

                    cliente,

                    int(sonda_id),

                    int(equipe_id),

                    int(furo_id),

                    h_ini,

                    h_fim,

                    observacoes,

                    datetime.now().isoformat()

                )

            )


            st.session_state.boletim_edit_id = bid


            st.success(

                "Boletim criado. "
                "Agora adicione manobras "
                "e atividades abaixo."

            )


            st.rerun()


    # --------------------------------------------------------
    # LANÇAMENTOS
    # --------------------------------------------------------

    bid = st.session_state.boletim_edit_id


    if bid:


        st.divider()


        # ====================================================
        # MANOBRAS
        # ====================================================

        st.subheader(
            "⛏️ Manobras e Perfuração"
        )


        with st.form(

            "nova_manobra",

            clear_on_submit=True

        ):


            c1, c2, c3, c4 = st.columns(4)


            numero = c1.number_input(

                "Nº",

                min_value=1,

                value=1,

                step=1

            )


            de_m = c2.number_input(

                "De (m)",

                min_value=0.0,

                step=0.1

            )


            ate_m = c3.number_input(

                "Até (m)",

                min_value=0.0,

                step=0.1

            )


            recuperado = c4.number_input(

                "Recuperado (m)",

                min_value=0.0,

                step=0.01

            )


            av = max(
                0.0,
                ate_m - de_m
            )


            rec = (

                recuperado
                /
                av
                *
                100

            ) if av else 0


            st.info(

                f"Avanço automático: "
                f"{av:.2f} m | "

                f"Recuperação automática: "
                f"{rec:.1f}%"

            )


            c1, c2, c3, c4, c5 = st.columns(5)


            dip = c1.number_input(
                "DIP",
                step=0.1
            )


            qaqc = c2.text_input(
                "QAQC"
            )


            perfil = c3.text_input(
                "Perfil / Diâmetro"
            )


            coroa = c4.text_input(
                "Coroa / Série"
            )


            revestimento = c5.text_input(
                "Revestimento"
            )


            fluido = st.text_input(
                "Tipo de Fluido"
            )


            add = st.form_submit_button(
                "➕ Adicionar Manobra"
            )


        if add:


            if ate_m <= de_m:

                st.error(

                    "O valor 'Até' deve "
                    "ser maior que 'De'."

                )


            elif recuperado > (
                ate_m - de_m
            ):

                st.error(

                    "A recuperação não "
                    "pode ser maior "
                    "que o avanço."

                )


            else:


                execute(

                    """

                    INSERT INTO manobras
                    (
                        boletim_id,
                        numero,
                        de_m,
                        ate_m,
                        recuperado_m,
                        dip,
                        qaqc,
                        perfil,
                        coroa,
                        revestimento,
                        fluido
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

                        bid,

                        numero,

                        de_m,

                        ate_m,

                        recuperado,

                        dip,

                        qaqc,

                        perfil,

                        coroa,

                        revestimento,

                        fluido

                    )

                )


                st.success(
                    "Manobra adicionada."
                )


                st.rerun()


        dfm = query(

            """

            SELECT *
            FROM manobras

            WHERE boletim_id=?

            ORDER BY numero

            """,

            (bid,)

        )


        if not dfm.empty:


            view = dfm.copy()


            view["Avanço"] = (

                view["ate_m"]
                -
                view["de_m"]

            )


            view["Recuperação %"] = (

                view[
                    "recuperado_m"
                ]

                /

                view[
                    "Avanço"
                ].replace(
                    0,
                    pd.NA
                )

                *
                100

            ).round(1)


            st.dataframe(

                view,

                use_container_width=True,

                hide_index=True

            )


        st.divider()


        # ====================================================
        # ATIVIDADES
        # ====================================================

        st.subheader(
            "⏱️ Atividades e Horários"
        )


        acts = query(

            """

            SELECT *
            FROM atividades

            ORDER BY codigo

            """

        )


        codes = acts[
            "codigo"
        ].tolist()


        with st.form(

            "nova_atividade",

            clear_on_submit=True

        ):


            codigo = st.selectbox(

                "Código da atividade",

                codes

            )


            ar = activity_row(
                codigo
            )


            c1, c2, c3 = st.columns(3)


            c1.text_input(

                "Grupo",

                value=ar.get(
                    "grupo",
                    ""
                ),

                disabled=True

            )


            c2.text_input(

                "Atividade",

                value=ar.get(
                    "atividade",
                    ""
                ),

                disabled=True

            )


            c3.text_input(

                "Classificação",

                value=ar.get(
                    "classificacao",
                    ""
                ),

                disabled=True

            )


            c1, c2, c3, c4 = st.columns(4)


            inicio = c1.time_input(

                "Hora inicial",

                value=time(
                    7,
                    0
                )

            )


            fim = c2.time_input(

                "Hora final",

                value=time(
                    8,
                    0
                )

            )


            horas = horas_intervalo(
                inicio,
                fim
            )


            c3.metric(

                "Tempo automático",

                f"{horas:.2f} h"

            )


            horimetro = c4.number_input(

                "Horímetro",

                min_value=0.0,

                step=0.1

            )


            obs = st.text_input(
                "Observação"
            )


            add_a = st.form_submit_button(

                "➕ Adicionar Atividade"

            )


        if add_a:


            execute(

                """

                INSERT INTO apontamentos
                (
                    boletim_id,
                    codigo_atividade,
                    hora_inicio,
                    hora_fim,
                    horas,
                    horimetro,
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
                    ?
                )

                """,

                (

                    bid,

                    int(codigo),

                    inicio.strftime(
                        "%H:%M"
                    ),

                    fim.strftime(
                        "%H:%M"
                    ),

                    horas,

                    horimetro,

                    obs

                )

            )


            st.success(
                "Atividade adicionada."
            )


            st.rerun()


        # ----------------------------------------------------
        # TABELA DE ATIVIDADES
        # ----------------------------------------------------

        dfa = query(

            """

            SELECT

                p.id,

                p.codigo_atividade,

                a.grupo,

                a.atividade,

                a.classificacao,

                p.hora_inicio,

                p.hora_fim,

                p.horas,

                p.horimetro,

                p.observacao

            FROM apontamentos p

            LEFT JOIN atividades a

            ON a.codigo =
                p.codigo_atividade

            WHERE p.boletim_id=?

            ORDER BY p.id

            """,

            (bid,)

        )


        if not dfa.empty:


            st.dataframe(

                dfa,

                use_container_width=True,

                hide_index=True

            )


        st.divider()


        # ----------------------------------------------------
        # EXCEL
        # ----------------------------------------------------

        if st.button(

            "📥 Gerar Excel deste Boletim",

            type="primary"

        ):


            st.download_button(

                "⬇️ Baixar Excel",

                excel_boletim(bid),

                file_name=
                    f"BOLETIM_DDH_{bid}.xlsx",

                mime=
                    "application/"
                    "vnd.openxmlformats-"
                    "officedocument."
                    "spreadsheetml.sheet"

            )


# ============================================================
# BOLETINS SALVOS
# ============================================================

elif page == "📋 Boletins Salvos":

    st.title(
        "📋 BOLETINS SALVOS"
    )


    df = query(

        """

        SELECT *
        FROM boletins

        ORDER BY
            data DESC,
            id DESC

        """

    )


    if df.empty:

        st.info(
            "Nenhum boletim salvo."
        )


    else:


        st.dataframe(

            df,

            use_container_width=True,

            hide_index=True

        )


        ids = df[
            "id"
        ].tolist()


        bid = st.selectbox(

            "Selecione um boletim",

            ids

        )


        c1, c2, c3 = st.columns(3)


        if c1.button(
            "✏️ Abrir para lançamento"
        ):

            st.session_state.boletim_edit_id = int(
                bid
            )

            st.info(

                "Abra o menu "
                "'Novo Boletim' "
                "para continuar."

            )


        c2.download_button(

            "📥 Excel",

            excel_boletim(
                int(bid)
            ),

            file_name=
                f"BOLETIM_DDH_{bid}.xlsx"

        )


        if c3.button(
            "🗑️ Excluir boletim"
        ):


            execute(

                """

                DELETE FROM manobras
                WHERE boletim_id=?

                """,

                (int(bid),)

            )


            execute(

                """

                DELETE FROM apontamentos
                WHERE boletim_id=?

                """,

                (int(bid),)

            )


            delete(
                "boletins",
                bid
            )


            st.success(
                "Boletim excluído."
            )


            st.rerun()


# ============================================================
# COLABORADORES
# ============================================================

elif page == "👷 Colaboradores":

    st.title(
        "👷 COLABORADORES"
    )


    t1, t2 = st.tabs(

        [

            "Lista",

            "Novo cadastro"

        ]

    )


    with t1:


        df = query(

            """

            SELECT *
            FROM colaboradores

            ORDER BY nome

            """

        )


        st.dataframe(

            df,

            use_container_width=True,

            hide_index=True

        )


        if not df.empty:


            idx = st.selectbox(

                "Excluir colaborador",

                df["id"].tolist(),

                format_func=lambda x:

                f"{x} - "

                f"{df[df.id == x].iloc[0].nome}"

            )


            if st.button(
                "🗑️ Excluir colaborador"
            ):

                delete(
                    "colaboradores",
                    idx
                )

                st.rerun()


    with t2:


        with st.form(

            "form_colab",

            clear_on_submit=True

        ):


            nome = st.text_input(
                "Nome"
            )


            funcao = st.selectbox(

                "Função",

                [

                    "Supervisor",

                    "Sondador",

                    "Auxiliar de Sondador",

                    "Geólogo",

                    "Mecânico",

                    "Técnico de Segurança",

                    "Outro"

                ]

            )


            matricula = st.text_input(
                "Matrícula"
            )


            status = st.selectbox(

                "Status",

                [

                    "Ativo",

                    "Inativo"

                ]

            )


            if st.form_submit_button(

                "Cadastrar",

                type="primary"

            ):


                if nome.strip():


                    execute(

                        """

                        INSERT INTO colaboradores
                        (
                            nome,
                            funcao,
                            matricula,
                            status
                        )

                        VALUES
                        (
                            ?,
                            ?,
                            ?,
                            ?
                        )

                        """,

                        (

                            nome.strip(),

                            funcao,

                            matricula,

                            status

                        )

                    )


                    st.success(
                        "Colaborador cadastrado."
                    )


                    st.rerun()


# ============================================================
# EQUIPES
# ============================================================

elif page == "👥 Equipes":

    st.title(
        "👥 EQUIPES"
    )


    dfc = query(

        """

        SELECT *
        FROM colaboradores

        WHERE status='Ativo'

        ORDER BY nome

        """

    )


    if dfc.empty:

        st.warning(
            "Cadastre colaboradores primeiro."
        )


    else:


        opts = dfc[
            "id"
        ].tolist()


        fmt = lambda x: (

            dfc[
                dfc.id == x
            ].iloc[0]["nome"]

        )


        with st.form(

            "form_equipe",

            clear_on_submit=True

        ):


            c1, c2 = st.columns(2)


            codigo = c1.text_input(
                "Código da equipe"
            )


            nome = c2.text_input(
                "Nome da equipe"
            )


            supervisor = st.selectbox(

                "Supervisor",

                opts,

                format_func=fmt

            )


            sondador = st.selectbox(

                "Sondador",

                opts,

                format_func=fmt

            )


            a1, a2 = st.columns(2)


            aux1 = a1.selectbox(

                "Auxiliar 1",

                opts,

                format_func=fmt

            )


            aux2 = a2.selectbox(

                "Auxiliar 2",

                opts,

                format_func=fmt

            )


            status = st.selectbox(

                "Status",

                [

                    "Ativa",

                    "Inativa"

                ]

            )


            if st.form_submit_button(

                "Cadastrar equipe",

                type="primary"

            ):


                if codigo and nome:


                    try:


                        execute(

                            """

                            INSERT INTO equipes
                            (
                                codigo,
                                nome,
                                supervisor_id,
                                sondador_id,
                                auxiliar1_id,
                                auxiliar2_id,
                                status
                            )

                            VALUES
                            (
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

                                codigo,

                                nome,

                                supervisor,

                                sondador,

                                aux1,

                                aux2,

                                status

                            )

                        )


                        st.success(
                            "Equipe cadastrada."
                        )


                        st.rerun()


                    except sqlite3.IntegrityError:


                        st.error(
                            "Código de equipe "
                            "já cadastrado."
                        )


        st.divider()


        st.dataframe(

            query(

                """

                SELECT *
                FROM equipes

                ORDER BY codigo

                """

            ),

            use_container_width=True,

            hide_index=True

        )


# ============================================================
# SONDAS
# ============================================================

elif page == "🔩 Sondas":

    st.title(
        "🔩 SONDAS"
    )


    dfe = query(

        """

        SELECT *
        FROM equipes

        WHERE status='Ativa'

        ORDER BY codigo

        """

    )


    if dfe.empty:

        st.warning(

            "Cadastre uma equipe "
            "antes de cadastrar "
            "uma sonda."

        )


    else:


        opts = dfe[
            "id"
        ].tolist()


        fmt = lambda x: (

            dfe[
                dfe.id == x
            ].iloc[0]["codigo"]

        )


        with st.form(

            "form_sonda",

            clear_on_submit=True

        ):


            c1, c2, c3 = st.columns(3)


            codigo = c1.text_input(
                "Código"
            )


            modelo = c2.text_input(
                "Modelo"
            )


            fabricante = c3.text_input(
                "Fabricante"
            )


            c1, c2, c3 = st.columns(3)


            patrimonio = c1.text_input(
                "Patrimônio"
            )


            equipe = c2.selectbox(

                "Equipe vinculada",

                opts,

                format_func=fmt

            )


            status = c3.selectbox(

                "Status",

                [

                    "Operando",

                    "Parada",

                    "Manutenção",

                    "Inativa"

                ]

            )


            if st.form_submit_button(

                "Cadastrar sonda",

                type="primary"

            ):


                if codigo:


                    try:


                        execute(

                            """

                            INSERT INTO sondas
                            (
                                codigo,
                                modelo,
                                fabricante,
                                patrimonio,
                                equipe_id,
                                status
                            )

                            VALUES
                            (
                                ?,
                                ?,
                                ?,
                                ?,
                                ?,
                                ?
                            )

                            """,

                            (

                                codigo,

                                modelo,

                                fabricante,

                                patrimonio,

                                equipe,

                                status

                            )

                        )


                        st.success(
                            "Sonda cadastrada."
                        )


                        st.rerun()


                    except sqlite3.IntegrityError:


                        st.error(
                            "Código de sonda "
                            "já cadastrado."
                        )


        st.divider()


        st.dataframe(

            query(

                """

                SELECT *
                FROM sondas

                ORDER BY codigo

                """

            ),

            use_container_width=True,

            hide_index=True

        )


# ============================================================
# CADASTROS
# ============================================================

else:

    st.title(
        "⚙️ CADASTROS"
    )


    tab_f, tab_a = st.tabs(

        [

            "🎯 Furos",

            "⏱️ Códigos de atividades"

        ]

    )


    # ========================================================
    # FUROS
    # ========================================================

    with tab_f:


        with st.form(

            "form_furo",

            clear_on_submit=True

        ):


            c1, c2, c3 = st.columns(3)


            ident = c1.text_input(
                "Identificação do furo"
            )


            projeto = c2.text_input(
                "Projeto"
            )


            cliente = c3.text_input(
                "Cliente"
            )


            c1, c2, c3 = st.columns(3)


            local = c1.text_input(
                "Local"
            )


            e = c2.number_input(
                "Coordenada E"
            )


            n = c3.number_input(
                "Coordenada N"
            )


            c1, c2, c3 = st.columns(3)


            cota = c1.number_input(
                "Cota"
            )


            az = c2.number_input(
                "Azimute"
            )


            dip = c3.number_input(
                "DIP"
            )


            status = st.selectbox(

                "Status",

                [

                    "Em andamento",

                    "Planejado",

                    "Concluído"

                ]

            )


            if st.form_submit_button(

                "Cadastrar furo",

                type="primary"

            ):


                if ident:


                    try:


                        execute(

                            """

                            INSERT INTO furos
                            (
                                identificacao,
                                projeto,
                                cliente,
                                local,
                                coord_e,
                                coord_n,
                                cota,
                                azimute,
                                dip,
                                status
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
                                ?
                            )

                            """,

                            (

                                ident,

                                projeto,

                                cliente,

                                local,

                                e,

                                n,

                                cota,

                                az,

                                dip,

                                status

                            )

                        )


                        st.success(
                            "Furo cadastrado."
                        )


                        st.rerun()


                    except sqlite3.IntegrityError:


                        st.error(
                            "Identificação "
                            "já cadastrada."
                        )


        st.dataframe(

            query(

                """

                SELECT *
                FROM furos

                ORDER BY identificacao

                """

            ),

            use_container_width=True,

            hide_index=True

        )


    # ========================================================
    # CÓDIGOS DE ATIVIDADES
    # ========================================================

    with tab_a:


        st.caption(

            "Edite ou cadastre os códigos "
            "para deixá-los exatamente "
            "iguais aos códigos da sua planilha."

        )


        df = query(

            """

            SELECT *
            FROM atividades

            ORDER BY codigo

            """

        )


        st.dataframe(

            df,

            use_container_width=True,

            hide_index=True

        )


        with st.form(

            "form_atividade",

            clear_on_submit=True

        ):


            c1, c2, c3, c4 = st.columns(4)


            cod = c1.number_input(

                "Código",

                min_value=1,

                step=1

            )


            grupo = c2.text_input(
                "Grupo"
            )


            atividade = c3.text_input(
                "Atividade"
            )


            classificacao = c4.selectbox(

                "Classificação",

                [

                    "OPERAÇÃO DIRETA",

                    "APOIO OPERACIONAL",

                    "MANUTENÇÃO PREVENTIVA",

                    "MECÂNICA CORRETIVA",

                    "PARADA EXTERNA",

                    "INTERVENÇÃO NO FURO",

                    "ADMINISTRATIVO",

                    "SEGURANÇA"

                ]

            )


            if st.form_submit_button(

                "Salvar código",

                type="primary"

            ):


                execute(

                    """

                    INSERT INTO atividades
                    (
                        codigo,
                        grupo,
                        atividade,
                        classificacao
                    )

                    VALUES
                    (
                        ?,
                        ?,
                        ?,
                        ?
                    )

                    ON CONFLICT(codigo)

                    DO UPDATE SET

                        grupo =
                            excluded.grupo,

                        atividade =
                            excluded.atividade,

                        classificacao =
                            excluded.classificacao

                    """,

                    (

                        int(cod),

                        grupo,

                        atividade,

                        classificacao

                    )

                )


                st.success(
                    "Código salvo."
                )


                st.rerun()
