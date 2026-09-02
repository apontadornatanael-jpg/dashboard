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
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "🏠 Painel DDH"

if "boletim_edit_id" not in st.session_state:
    st.session_state.boletim_edit_id = None


# ============================================================
# BANCO DE DADOS
# ============================================================

def conn():

    conexao = sqlite3.connect(
        DB,
        check_same_thread=False,
        timeout=30
    )

    conexao.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conexao


def query(sql, params=()):

    c = conn()

    try:

        df = pd.read_sql_query(
            sql,
            c,
            params=params
        )

    finally:

        c.close()

    return df


def execute(sql, params=()):

    c = conn()

    try:

        cur = c.cursor()

        cur.execute(
            sql,
            params
        )

        c.commit()

        return cur.lastrowid

    finally:

        c.close()


def delete(table, idv):

    execute(
        f"""
        DELETE FROM {table}
        WHERE id=?
        """,
        (int(idv),)
    )


# ============================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================

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

    seed_activities()


# ============================================================
# ATIVIDADES PADRÃO
# ============================================================

def seed_activities():

    rows = [

        (1, "Segurança e Gestão", "DDS / Segurança", "SEGURANÇA"),
        (2, "Administrativo", "Reunião / Administrativo", "ADMINISTRATIVO"),
        (3, "Logística", "Deslocamento / Logística", "APOIO OPERACIONAL"),
        (4, "Fluidos", "Preparação de fluido", "APOIO OPERACIONAL"),
        (5, "Praça e Acesso", "Preparação de praça / acesso", "APOIO OPERACIONAL"),
        (6, "Mobilização", "Mobilização / desmobilização", "APOIO OPERACIONAL"),
        (7, "Manutenção Preventiva", "Manutenção preventiva", "MANUTENÇÃO PREVENTIVA"),
        (8, "Manutenção Corretiva", "Manutenção mecânica corretiva", "MECÂNICA CORRETIVA"),
        (9, "Suprimentos", "Aguardar / receber suprimentos", "PARADA EXTERNA"),
        (10, "Apoio Externo", "Aguardar apoio externo", "PARADA EXTERNA"),
        (11, "Condições Externas", "Chuva / condição climática", "PARADA EXTERNA"),
        (12, "Contratante", "Aguardar liberação do contratante", "PARADA EXTERNA"),
        (13, "Serviços Especializados", "Serviço especializado", "APOIO OPERACIONAL"),
        (14, "Produção", "Perfuração", "OPERAÇÃO DIRETA"),
        (15, "Produção", "Manobra", "OPERAÇÃO DIRETA"),
        (16, "Produção", "Troca de haste / tubo", "OPERAÇÃO DIRETA"),
        (17, "Produção", "Condicionamento do furo", "OPERAÇÃO DIRETA"),
        (18, "Produção", "Furando e manobrando", "OPERAÇÃO DIRETA"),
        (19, "Operação", "Preparação operacional", "APOIO OPERACIONAL"),
        (20, "Operação", "Limpeza e organização", "APOIO OPERACIONAL"),
        (21, "Ferramental", "Troca de ferramental", "APOIO OPERACIONAL"),
        (22, "Ferramental", "Inspeção de ferramental", "APOIO OPERACIONAL"),
        (23, "Revestimento", "Instalação / retirada de revestimento", "INTERVENÇÃO NO FURO"),
        (24, "Intervenção", "Desvio / intervenção no furo", "INTERVENÇÃO NO FURO"),
        (25, "Intervenção", "Obstrução / perda no furo", "INTERVENÇÃO NO FURO"),
        (26, "Segurança e Gestão", "Treinamento / gestão", "SEGURANÇA"),
        (27, "Administrativo", "Encerramento / relatório", "ADMINISTRATIVO")

    ]

    c = conn()
    cur = c.cursor()

    for codigo, grupo, atividade, classificacao in rows:

        cur.execute(
            """
            INSERT INTO atividades
            (
                codigo,
                grupo,
                atividade,
                classificacao
            )
            VALUES (?, ?, ?, ?)

            ON CONFLICT(codigo)
            DO NOTHING
            """,
            (
                codigo,
                grupo,
                atividade,
                classificacao
            )
        )

    c.commit()
    c.close()


# ============================================================
# INICIALIZA BANCO
# ============================================================

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


def entity_options(
    table,
    label_col,
    where=None
):

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


# ============================================================
# GERAÇÃO DO EXCEL
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


    sondas = query("SELECT * FROM sondas")
    equipes = query("SELECT * FROM equipes")
    furos = query("SELECT * FROM furos")


    wb = Workbook()

    ws = wb.active

    ws.title = "BOLETIM_DDH"


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


    # ========================================================
    # TÍTULO
    # ========================================================

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


    # ========================================================
    # INFORMAÇÕES
    # ========================================================

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
        ("Horímetro Inicial", b.get("horimetro_inicial")),
        ("Horímetro Final", b.get("horimetro_final"))

    ]

    r = 3

    for label, value in info:

        ws.cell(r, 1, label).font = bold
        ws.cell(r, 2, value)

        r += 1


    # ========================================================
    # MANOBRAS
    # ========================================================

    r += 1

    ws.merge_cells(
        start_row=r,
        start_column=1,
        end_row=r,
        end_column=10
    )

    ws.cell(
        r,
        1,
        "MANOBRAS / PERFURAÇÃO"
    ).fill = dark

    ws.cell(r, 1).font = white

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

        ws.cell(r, c, h).fill = light
        ws.cell(r, c).font = bold


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
            ws.cell(r, c, v)


    # ========================================================
    # ATIVIDADES
    # ========================================================

    r += 2

    ws.merge_cells(
        start_row=r,
        start_column=1,
        end_row=r,
        end_column=9
    )

    ws.cell(
        r,
        1,
        "ATIVIDADES / HORAS"
    ).fill = dark

    ws.cell(r, 1).font = white

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

        ws.cell(r, c, h).fill = light
        ws.cell(r, c).font = bold


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
            ws.cell(r, c, v)


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

    ],

    key="page"

)


# ============================================================
# PAINEL DDH
# ============================================================

if page == "🏠 Painel DDH":

    st.title("🏠 PAINEL DDH")


    # ========================================================
    # PRODUÇÃO GERAL
    # ========================================================

    resumo_geral = query(
        """
        SELECT

            COALESCE(
                SUM(
                    COALESCE(ate_m, 0)
                    -
                    COALESCE(de_m, 0)
                ),
                0
            ) AS metros,

            COALESCE(
                SUM(
                    COALESCE(recuperado_m, 0)
                ),
                0
            ) AS recuperado

        FROM manobras
        """
    )


    horas_geral = query(
        """
        SELECT

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

        FROM apontamentos p

        LEFT JOIN atividades a
            ON a.codigo =
            p.codigo_atividade
        """
    )


    metros_total = float(
        resumo_geral.iloc[0]["metros"]
        or 0
    )

    recuperado_total = float(
        resumo_geral.iloc[0]["recuperado"]
        or 0
    )

    horas_total = float(
        horas_geral.iloc[0][
            "horas_operacao"
        ]
        or 0
    )


    recuperacao_total = (
        recuperado_total
        /
        metros_total
        *
        100
    ) if metros_total > 0 else 0


    rop_total = (
        metros_total
        /
        horas_total
    ) if horas_total > 0 else 0


    boletins_total = query(
        """
        SELECT COUNT(*) AS total
        FROM boletins
        """
    )


    # ========================================================
    # CARDS
    # ========================================================

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "⛏️ PRODUÇÃO TOTAL",
        f"{metros_total:.2f} m"
    )

    c2.metric(
        "🧪 RECUPERAÇÃO",
        f"{recuperacao_total:.1f}%"
    )

    c3.metric(
        "⏱️ HORAS OPERAÇÃO",
        f"{horas_total:.2f} h"
    )

    c4.metric(
        "⚡ ROP MÉDIO",
        f"{rop_total:.2f} m/h"
    )

    c5.metric(
        "📋 BOLETINS",
        int(
            boletins_total.iloc[0]["total"]
        )
    )


    st.divider()


    # ========================================================
    # PRODUÇÃO POR EQUIPE
    # ========================================================

    st.subheader(
        "👥 Produção por Equipe"
    )


    producao_equipes = query(
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
            ) AS recuperado,

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

        LEFT JOIN manobras m
            ON m.boletim_id = b.id

        LEFT JOIN apontamentos p
            ON p.boletim_id = b.id

        LEFT JOIN atividades a
            ON a.codigo =
            p.codigo_atividade

        WHERE e.status != 'Inativa'

        GROUP BY
            e.id,
            e.codigo,
            e.nome

        ORDER BY metros DESC
        """
    )


    if not producao_equipes.empty:


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
            ]
            .copy()
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


        tabela_equipes = tabela_equipes.sort_values(
            "Metros",
            ascending=False
        )


        st.dataframe(
            tabela_equipes.round(2),
            use_container_width=True,
            hide_index=True
        )


    st.divider()


    # ========================================================
    # PRODUÇÃO POR SONDA
    # ========================================================

    st.subheader(
        "🔩 Produção por Sonda"
    )


    producao_sondas = query(
        """
        SELECT

            s.id AS sonda_id,
            s.codigo AS sonda,
            s.modelo,
            s.status,
            s.equipe_id,

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

        FROM sondas s

        LEFT JOIN equipes e
            ON e.id = s.equipe_id

        LEFT JOIN boletins b
            ON b.sonda_id = s.id

        LEFT JOIN manobras m
            ON m.boletim_id = b.id

        WHERE s.status != 'Inativa'

        GROUP BY

            s.id,
            s.codigo,
            s.modelo,
            s.status,
            s.equipe_id,
            e.codigo,
            e.nome

        ORDER BY metros DESC
        """
    )


    horas_sondas = query(
        """
        SELECT

            s.id AS sonda_id,

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

        FROM sondas s

        LEFT JOIN boletins b
            ON b.sonda_id = s.id

        LEFT JOIN apontamentos p
            ON p.boletim_id = b.id

        LEFT JOIN atividades a
            ON a.codigo =
            p.codigo_atividade

        WHERE s.status != 'Inativa'

        GROUP BY s.id
        """
    )


    if not producao_sondas.empty:


        tabela_sondas = producao_sondas.merge(
            horas_sondas,
            on="sonda_id",
            how="left"
        )


        tabela_sondas[
            "horas_operacao"
        ] = tabela_sondas[
            "horas_operacao"
        ].fillna(0)


        tabela_sondas[
            "Recuperação %"
        ] = (

            tabela_sondas[
                "recuperado"
            ]

            /

            tabela_sondas[
                "metros"
            ].replace(
                0,
                pd.NA
            )

            *
            100

        ).fillna(0)


        tabela_sondas[
            "ROP (m/h)"
        ] = (

            tabela_sondas[
                "metros"
            ]

            /

            tabela_sondas[
                "horas_operacao"
            ].replace(
                0,
                pd.NA
            )

        ).fillna(0)


        tabela_final = tabela_sondas[
            [
                "sonda",
                "modelo",
                "equipe",
                "nome_equipe",
                "metros",
                "recuperado",
                "Recuperação %",
                "horas_operacao",
                "ROP (m/h)"
            ]
        ].copy()


        tabela_final.columns = [

            "Sonda",
            "Modelo",
            "Equipe",
            "Nome da Equipe",
            "Metros",
            "Recuperado",
            "Recuperação %",
            "Horas Operação",
            "ROP (m/h)"

        ]


        tabela_final = tabela_final.sort_values(
            "Metros",
            ascending=False
        )


        # ----------------------------------------------------
        # CARDS
        # ----------------------------------------------------

        sondas_com_producao = tabela_final[
            tabela_final[
                "Metros"
            ] > 0
        ]


        for _, sonda in sondas_com_producao.iterrows():

            st.markdown(
                f"### 🔩 {sonda['Sonda']}"
            )

            st.caption(
                f"👷 Equipe: "
                f"{sonda['Equipe']} - "
                f"{sonda['Nome da Equipe']}"
            )

            cs = st.columns(4)

            cs[0].metric(
                "PRODUÇÃO",
                f"{sonda['Metros']:.2f} m"
            )

            cs[1].metric(
                "RECUPERAÇÃO",
                f"{sonda['Recuperação %']:.1f}%"
            )

            cs[2].metric(
                "HORAS OPERAÇÃO",
                f"{sonda['Horas Operação']:.2f} h"
            )

            cs[3].metric(
                "ROP",
                f"{sonda['ROP (m/h)']:.2f} m/h"
            )


        st.divider()


        # ----------------------------------------------------
        # GRÁFICO PRODUÇÃO
        # ----------------------------------------------------

        st.subheader(
            "📊 Produção das Sondas"
        )

        grafico = tabela_final[
            [
                "Sonda",
                "Metros"
            ]
        ].set_index(
            "Sonda"
        )

        st.bar_chart(
            grafico
        )


        # ----------------------------------------------------
        # GRÁFICO ROP
        # ----------------------------------------------------

        st.subheader(
            "⚡ ROP por Sonda"
        )

        grafico_rop = tabela_final[
            [
                "Sonda",
                "ROP (m/h)"
            ]
        ].set_index(
            "Sonda"
        )

        st.bar_chart(
            grafico_rop
        )


        # ----------------------------------------------------
        # RANKING
        # ----------------------------------------------------

        st.subheader(
            "🏆 Ranking de Produção"
        )

        ranking = tabela_final.copy()

        ranking.insert(
            0,
            "Posição",
            range(
                1,
                len(ranking) + 1
            )
        )

        st.dataframe(
            ranking.round(2),
            use_container_width=True,
            hide_index=True
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
        or df_e.empty
        or df_f.empty
    ):

        st.warning(
            "Cadastre pelo menos uma "
            "Sonda, uma Equipe e um Furo."
        )

        st.stop()


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
            list(map_s.keys()),
            format_func=lambda x: map_s[x]
        )


        row_s = df_s[
            df_s["id"] == sonda_id
        ]

        equipe_padrao = None

        if not row_s.empty:

            if pd.notna(
                row_s.iloc[0]["equipe_id"]
            ):

                equipe_padrao = int(
                    row_s.iloc[0]["equipe_id"]
                )


        ids_equipes = list(map_e.keys())

        idx_e = (
            ids_equipes.index(equipe_padrao)
            if equipe_padrao in ids_equipes
            else 0
        )


        equipe_id = d.selectbox(
            "Equipe",
            ids_equipes,
            index=idx_e,
            format_func=lambda x: map_e[x]
        )


        a, b, c, d = st.columns(4)

        furo_id = a.selectbox(
            "Furo",
            list(map_f.keys()),
            format_func=lambda x: map_f[x]
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

        if h_fim < h_ini:

            st.error(
                "Horímetro final não pode "
                "ser menor que o inicial."
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
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
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
                "Boletim criado com sucesso."
            )

            st.rerun()


    bid = st.session_state.boletim_edit_id


    if bid:

        st.divider()

        st.subheader(
            f"📋 Lançamentos do Boletim #{bid}"
        )


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
            ) if av > 0 else 0


            st.info(
                f"📏 Avanço: {av:.2f} m | "
                f"🧪 Recuperação: {rec:.1f}%"
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

            elif recuperado > av:

                st.error(
                    "A recuperação não pode "
                    "ser maior que o avanço."
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
                        ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?
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
                view["recuperado_m"]
                /
                view["Avanço"].replace(
                    0,
                    pd.NA
                )
                *
                100
            ).fillna(0)


            st.dataframe(
                view.round(2),
                use_container_width=True,
                hide_index=True
            )


        # ====================================================
        # ATIVIDADES
        # ====================================================

        st.divider()

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
                value=time(7, 0)
            )

            fim = c2.time_input(
                "Hora final",
                value=time(8, 0)
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
                (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bid,
                    int(codigo),
                    inicio.strftime("%H:%M"),
                    fim.strftime("%H:%M"),
                    horas,
                    horimetro,
                    obs
                )
            )

            st.success(
                "Atividade adicionada."
            )

            st.rerun()


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


        # ====================================================
        # EXCEL
        # ====================================================

        st.divider()

        st.download_button(
            "📥 Baixar Excel deste Boletim",
            data=excel_boletim(bid),
            file_name=f"BOLETIM_DDH_{bid}.xlsx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            type="primary",
            use_container_width=True
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
        SELECT
            b.*,
            s.codigo AS sonda,
            e.codigo AS equipe,
            f.identificacao AS furo

        FROM boletins b

        LEFT JOIN sondas s
            ON s.id = b.sonda_id

        LEFT JOIN equipes e
            ON e.id = b.equipe_id

        LEFT JOIN furos f
            ON f.id = b.furo_id

        ORDER BY
            b.data DESC,
            b.id DESC
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


        ids = df["id"].tolist()


        bid = st.selectbox(
            "Selecione um boletim",
            ids,
            format_func=lambda x:
                f"Boletim #{x}"
        )


        c1, c2, c3 = st.columns(3)


        if c1.button(
            "✏️ Abrir para lançamento"
        ):

            st.session_state.boletim_edit_id = int(
                bid
            )

            st.session_state.page = (
                "📝 Novo Boletim"
            )

            st.rerun()


        c2.download_button(
            "📥 Baixar Excel",
            data=excel_boletim(
                int(bid)
            ),
            file_name=(
                f"BOLETIM_DDH_{bid}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            )
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

            if (
                st.session_state.boletim_edit_id
                ==
                int(bid)
            ):

                st.session_state.boletim_edit_id = None


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


            salvar = st.form_submit_button(
                "Cadastrar",
                type="primary"
            )


        if salvar:

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
                    VALUES (?, ?, ?, ?)
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

            else:

                st.error(
                    "Informe o nome."
                )


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


        def fmt_colaborador(x):

            row = dfc[
                dfc.id == x
            ]

            if row.empty:
                return str(x)

            return row.iloc[0]["nome"]


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
                format_func=fmt_colaborador
            )

            sondador = st.selectbox(
                "Sondador",
                opts,
                format_func=fmt_colaborador
            )


            a1, a2 = st.columns(2)

            aux1 = a1.selectbox(
                "Auxiliar 1",
                opts,
                format_func=fmt_colaborador
            )

            aux2 = a2.selectbox(
                "Auxiliar 2",
                opts,
                format_func=fmt_colaborador
            )


            status = st.selectbox(
                "Status",
                [
                    "Ativa",
                    "Inativa"
                ]
            )


            salvar = st.form_submit_button(
                "Cadastrar equipe",
                type="primary"
            )


        if salvar:

            if codigo.strip() and nome.strip():

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
                        (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            codigo.strip(),
                            nome.strip(),
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

            else:

                st.error(
                    "Informe código e nome."
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
            "Cadastre uma equipe antes "
            "de cadastrar uma sonda."
        )

    else:

        opts = dfe[
            "id"
        ].tolist()


        def fmt_equipe(x):

            row = dfe[
                dfe.id == x
            ]

            if row.empty:
                return str(x)

            return row.iloc[0]["codigo"]


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
                format_func=fmt_equipe
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


            salvar = st.form_submit_button(
                "Cadastrar sonda",
                type="primary"
            )


        if salvar:

            if codigo.strip():

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
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            codigo.strip(),
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
                SELECT
                    s.*,
                    e.codigo AS equipe

                FROM sondas s

                LEFT JOIN equipes e
                    ON e.id = s.equipe_id

                ORDER BY s.codigo
                """
            ),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# CADASTROS
# ============================================================

elif page == "⚙️ Cadastros":

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


            salvar = st.form_submit_button(
                "Cadastrar furo",
                type="primary"
            )


        if salvar:

            if ident.strip():

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
                        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            ident.strip(),
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


        st.divider()


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
    # ATIVIDADES
    # ========================================================

    with tab_a:

        st.caption(
            "Cadastre ou atualize "
            "os códigos de atividades."
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


            salvar = st.form_submit_button(
                "Salvar código",
                type="primary"
            )


        if salvar:

            if (
                grupo.strip()
                and atividade.strip()
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
                    (?, ?, ?, ?)

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

            else:

                st.error(
                    "Informe Grupo e Atividade."
                )
