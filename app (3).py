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
    return sqlite3.connect(
        DB,
        check_same_thread=False
    )


def query(sql, params=()):
    c = conn()
    df = pd.read_sql_query(
        sql,
        c,
        params=params
    )
    c.close()
    return df


def execute(sql, params=()):
    c = conn()
    cur = c.cursor()

    cur.execute(
        sql,
        params
    )

    c.commit()

    last = cur.lastrowid

    c.close()

    return last


def delete(table, idv):
    execute(
        f"DELETE FROM {table} WHERE id=?",
        (int(idv),)
    )


# ============================================================
# CRIAÇÃO DAS TABELAS
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
    # APONTAMENTOS / TEMPOS E PARADAS
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
# CÓDIGOS INICIAIS DE ATIVIDADES
# ============================================================

def seed_activities():

    df = query(
        "SELECT COUNT(*) qtd FROM atividades"
    )

    if int(df.iloc[0]["qtd"]) > 0:
        return

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
        ),
    ]

    c = conn()

    c.executemany(
        """
        INSERT INTO atividades
        VALUES (?,?,?,?)
        """,
        rows
    )

    c.commit()
    c.close()


init_db()


# ============================================================
# FUNÇÕES GERAIS
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

    # Permite atividades que passam da meia-noite

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

    sql = f"SELECT * FROM {table}"

    if where:
        sql += " WHERE " + where

    df = query(sql)

    if df.empty:
        return df, {}

    mapping = {
        int(r["id"]): str(r[label_col])
        for _, r in df.iterrows()
    }

    return df, mapping


def safe_name(
    df,
    col,
    idv
):

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
# RESUMO OPERACIONAL DO BOLETIM
# ============================================================

def resumo_operacional_boletim(boletim_id):

    # --------------------------------------------------------
    # MANOBRAS
    # --------------------------------------------------------

    man = query(
        """
        SELECT *
        FROM manobras
        WHERE boletim_id=?
        """,
        (boletim_id,)
    )

    metros_furados = 0.0
    recuperacao_m = 0.0

    if not man.empty:

        man["de_m"] = pd.to_numeric(
            man["de_m"],
            errors="coerce"
        ).fillna(0)

        man["ate_m"] = pd.to_numeric(
            man["ate_m"],
            errors="coerce"
        ).fillna(0)

        man["recuperado_m"] = pd.to_numeric(
            man["recuperado_m"],
            errors="coerce"
        ).fillna(0)

        man["avanco"] = (
            man["ate_m"]
            - man["de_m"]
        )

        metros_furados = float(
            man["avanco"]
            .clip(lower=0)
            .sum()
        )

        recuperacao_m = float(
            man["recuperado_m"]
            .sum()
        )

    recuperacao_pct = (
        recuperacao_m
        / metros_furados
        * 100
        if metros_furados > 0
        else 0
    )

    # --------------------------------------------------------
    # APONTAMENTOS
    # --------------------------------------------------------

    ap = query(
        """
        SELECT
            p.*,
            a.grupo,
            a.atividade,
            a.classificacao

        FROM apontamentos p

        LEFT JOIN atividades a
            ON p.codigo_atividade=a.codigo

        WHERE p.boletim_id=?
        """,
        (boletim_id,)
    )

    classificacoes = [

        "OPERAÇÃO DIRETA",

        "APOIO OPERACIONAL",

        "MANUTENÇÃO PREVENTIVA",

        "MECÂNICA CORRETIVA",

        "PARADA EXTERNA",

        "ADMINISTRATIVO",

        "SEGURANÇA",

        "INTERVENÇÃO NO FURO"

    ]

    totais = {
        classificacao: 0.0
        for classificacao
        in classificacoes
    }

    horas_programadas = 0.0

    if not ap.empty:

        ap["horas"] = pd.to_numeric(
            ap["horas"],
            errors="coerce"
        ).fillna(0)

        horas_programadas = float(
            ap["horas"].sum()
        )

        for classificacao in classificacoes:

            valor = ap.loc[
                ap["classificacao"]
                == classificacao,
                "horas"
            ].sum()

            totais[classificacao] = float(
                valor
            )

    # --------------------------------------------------------
    # HORAS POR CLASSIFICAÇÃO
    # --------------------------------------------------------

    h_direta = (
        totais["OPERAÇÃO DIRETA"]
    )

    h_apoio = (
        totais["APOIO OPERACIONAL"]
        +
        totais["INTERVENÇÃO NO FURO"]
    )

    h_prev = (
        totais["MANUTENÇÃO PREVENTIVA"]
    )

    h_mec = (
        totais["MECÂNICA CORRETIVA"]
    )

    h_parada_externa = (
        totais["PARADA EXTERNA"]
    )

    h_administrativa = (
        totais["ADMINISTRATIVO"]
        +
        totais["SEGURANÇA"]
    )

    # --------------------------------------------------------
    # HORAS DE PARADA
    # --------------------------------------------------------

    horas_parada = (

        h_prev

        +

        h_mec

        +

        h_parada_externa

        +

        h_administrativa

    )

    # --------------------------------------------------------
    # INDICADORES
    # --------------------------------------------------------

    rop = (

        metros_furados
        /
        h_direta

        if h_direta > 0

        else 0

    )

    disponibilidade_fisica = (

        (
            horas_programadas
            -
            h_mec
        )

        /

        horas_programadas

        *

        100

        if horas_programadas > 0

        else 0

    )

    base_utilizacao = (
        horas_programadas
        -
        h_mec
    )

    utilizacao = (

        h_direta
        /
        base_utilizacao
        *
        100

        if base_utilizacao > 0

        else 0

    )

    return {

        "metros_furados":
            metros_furados,

        "recuperacao_m":
            recuperacao_m,

        "recuperacao_pct":
            recuperacao_pct,

        "horas_programadas":
            horas_programadas,

        "rop":
            rop,

        "h_direta":
            h_direta,

        "h_apoio":
            h_apoio,

        "h_prev":
            h_prev,

        "h_mec":
            h_mec,

        "h_parada_externa":
            h_parada_externa,

        "h_administrativa":
            h_administrativa,

        "horas_parada":
            horas_parada,

        "disponibilidade_fisica":
            disponibilidade_fisica,

        "utilizacao":
            utilizacao
    }


# ============================================================
# EXCEL
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

    from openpyxl.utils import (
        get_column_letter
    )

    b = query(
        """
        SELECT *
        FROM boletins
        WHERE id=?
        """,
        (boletim_id,)
    ).iloc[0].to_dict()

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
            ON p.codigo_atividade=a.codigo

        WHERE p.boletim_id=?

        ORDER BY p.id
        """,
        (boletim_id,)
    )

    resumo = resumo_operacional_boletim(
        boletim_id
    )

    sondas = query(
        "SELECT * FROM sondas"
    )

    equipes = query(
        "SELECT * FROM equipes"
    )

    furos = query(
        "SELECT * FROM furos"
    )

    wb = Workbook()

    ws = wb.active

    ws.title = "BOLETIM_DDH"

    # --------------------------------------------------------
    # CORES
    # --------------------------------------------------------

    dark = PatternFill(
        "solid",
        fgColor="1F4E45"
    )

    light = PatternFill(
        "solid",
        fgColor="D9EAD3"
    )

    yellow = PatternFill(
        "solid",
        fgColor="FFF2CC"
    )

    white = Font(
        color="FFFFFF",
        bold=True,
        size=12
    )

    bold = Font(
        bold=True
    )

    thin = Side(
        style="thin",
        color="808080"
    )

    border = Border(
        left=thin,
        right=thin,
        top=thin,
        bottom=thin
    )

    # --------------------------------------------------------
    # TÍTULO
    # --------------------------------------------------------

    ws.merge_cells(
        "A1:J1"
    )

    ws["A1"] = (
        "BOLETIM DE SONDAGEM "
        "ROTATIVA DIAMANTADA - DDH"
    )

    ws["A1"].fill = dark
    ws["A1"].font = Font(
        color="FFFFFF",
        bold=True,
        size=14
    )

    ws["A1"].alignment = Alignment(
        horizontal="center"
    )

    # --------------------------------------------------------
    # IDENTIFICAÇÃO
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

        ("Data", b["data"]),

        ("Turno", b["turno"]),

        ("Projeto", b["projeto"]),

        ("Cliente", b["cliente"]),

        ("Sonda", sonda),

        ("Equipe", equipe),

        ("Furo", furo),

        (
            "Horímetro inicial",
            b["horimetro_inicial"]
        ),

        (
            "Horímetro final",
            b["horimetro_final"]
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

    # --------------------------------------------------------
    # MANOBRAS
    # --------------------------------------------------------

    r += 1

    ws.cell(
        r,
        1,
        "MANOBRAS / PERFURAÇÃO"
    )

    ws.cell(
        r,
        1
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

    for c, h in enumerate(
        heads,
        1
    ):

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

            float(
                x["recuperado_m"]
                or 0
            )

            /

            av

            *

            100

            if av

            else 0

        )

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

        for c, v in enumerate(
            vals,
            1
        ):

            ws.cell(
                r,
                c,
                v
            )

    # --------------------------------------------------------
    # TEMPOS E PARADAS
    # --------------------------------------------------------

    r += 2

    ws.cell(
        r,
        1,
        "TEMPOS E PARADAS"
    )

    ws.cell(
        r,
        1
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

        "Atividade / Evento",

        "Classificação",

        "Início",

        "Fim",

        "Duração (h)",

        "Duração (min)",

        "Observações"

    ]

    for c, h in enumerate(
        heads,
        1
    ):

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

        minutos = round(
            float(
                x["horas"]
                or 0
            )
            *
            60
        )

        vals = [

            x["codigo_atividade"],

            x["grupo"],

            x["atividade"],

            x["classificacao"],

            x["hora_inicio"],

            x["hora_fim"],

            x["horas"],

            minutos,

            x["observacao"]

        ]

        for c, v in enumerate(
            vals,
            1
        ):

            ws.cell(
                r,
                c,
                v
            )

    # --------------------------------------------------------
    # RESUMO OPERACIONAL
    # --------------------------------------------------------

    r += 2

    ws.cell(
        r,
        1,
        "RESUMO OPERACIONAL DO TURNO"
    )

    ws.cell(
        r,
        1
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

    resumo_excel = [

        (
            "METROS FURADOS",
            f"{resumo['metros_furados']:.2f} m"
        ),

        (
            "RECUPERAÇÃO (m)",
            f"{resumo['recuperacao_m']:.2f} m"
        ),

        (
            "RECUPERAÇÃO %",
            f"{resumo['recuperacao_pct']:.1f}%"
        ),

        (
            "HORAS PROGRAMADAS",
            f"{resumo['horas_programadas']:.2f} h"
        ),

        (
            "ROP (m/h)",
            f"{resumo['rop']:.2f}"
        ),

        (
            "H. DIRETA",
            f"{resumo['h_direta']:.2f}"
        ),

        (
            "H. APOIO OPERACIONAL",
            f"{resumo['h_apoio']:.2f}"
        ),

        (
            "H. MANUT. PREVENTIVA",
            f"{resumo['h_prev']:.2f}"
        ),

        (
            "H. MECÂNICA CORRETIVA",
            f"{resumo['h_mec']:.2f}"
        ),

        (
            "H. PARADA EXTERNA",
            f"{resumo['h_parada_externa']:.2f}"
        ),

        (
            "H. ADMINISTRATIVA",
            f"{resumo['h_administrativa']:.2f}"
        ),

        (
            "HORAS DE PARADA",
            f"{resumo['horas_parada']:.2f}"
        ),

        (
            "DISPONIBILIDADE FÍSICA",
            f"{resumo['disponibilidade_fisica']:.1f}%"
        ),

        (
            "UTILIZAÇÃO",
            f"{resumo['utilizacao']:.1f}%"
        )

    ]

    for label, value in resumo_excel:

        ws.cell(
            r,
            1,
            label
        ).fill = light

        ws.cell(
            r,
            1
        ).font = bold

        ws.cell(
            r,
            2,
            value
        )

        r += 1

    # --------------------------------------------------------
    # OBSERVAÇÕES GERAIS
    # --------------------------------------------------------

    r += 1

    ws.cell(
        r,
        1,
        "OBSERVAÇÕES GERAIS"
    )

    ws.cell(
        r,
        1
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

    ws.merge_cells(
        start_row=r,
        start_column=1,
        end_row=r + 3,
        end_column=10
    )

    ws.cell(
        r,
        1,
        b.get("observacoes")
        or ""
    )

    ws.cell(
        r,
        1
    ).fill = yellow

    ws.cell(
        r,
        1
    ).alignment = Alignment(
        wrap_text=True,
        vertical="top"
    )

    # --------------------------------------------------------
    # FORMATAÇÃO
    # --------------------------------------------------------

    for row in ws.iter_rows():

        for cell in row:

            cell.border = border

            cell.alignment = Alignment(
                vertical="center",
                wrap_text=True
            )

    widths = [

        14,
        22,
        35,
        25,
        14,
        14,
        14,
        15,
        35,
        20

    ]

    for i, w in enumerate(
        widths,
        1
    ):

        ws.column_dimensions[
            get_column_letter(i)
        ].width = w

    out = BytesIO()

    wb.save(out)

    return out.getvalue()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "⛏️ DDH CAMPO"
)

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


# ============================================================
# PAINEL
# ============================================================

if page == "🏠 Painel DDH":

    st.title(
        "📊 PAINEL DDH"
    )

    boletins = query(
        "SELECT * FROM boletins"
    )

    man = query(
        "SELECT * FROM manobras"
    )

    ap = query(
        """
        SELECT
            p.*,
            a.classificacao

        FROM apontamentos p

        LEFT JOIN atividades a
            ON p.codigo_atividade=a.codigo
        """
    )

    metros = (

        0.0

        if man.empty

        else float(

            (
                man["ate_m"].fillna(0)
                -
                man["de_m"].fillna(0)
            ).sum()

        )

    )

    rec_total = (

        0.0

        if man.empty

        else float(

            man["recuperado_m"]
            .fillna(0)
            .sum()

        )

    )

    rec_pct = (

        rec_total
        /
        metros
        *
        100

        if metros

        else 0

    )

    horas_op = (

        0.0

        if ap.empty

        else float(

            ap.loc[
                ap["classificacao"]
                ==
                "OPERAÇÃO DIRETA",
                "horas"
            ]

            .fillna(0)

            .sum()

        )

    )

    horas_mec = (

        0.0

        if ap.empty

        else float(

            ap.loc[
                ap["classificacao"]
                ==
                "MECÂNICA CORRETIVA",
                "horas"
            ]

            .fillna(0)

            .sum()

        )

    )

    horas_total = (

        0.0

        if ap.empty

        else float(

            ap["horas"]
            .fillna(0)
            .sum()

        )

    )

    disponibilidade = (

        (
            horas_total
            -
            horas_mec
        )

        /

        horas_total

        *

        100

        if horas_total

        else 0

    )

    utilizacao = (

        horas_op
        /
        (
            horas_total
            -
            horas_mec
        )

        *
        100

        if (
            horas_total
            -
            horas_mec
        ) > 0

        else 0

    )

    rop = (

        metros
        /
        horas_op

        if horas_op

        else 0

    )

    c = st.columns(4)

    c[0].metric(
        "METROS",
        f"{metros:.2f} m"
    )

    c[1].metric(
        "RECUPERAÇÃO",
        f"{rec_pct:.1f}%"
    )

    c[2].metric(
        "HORAS OPERAÇÃO",
        f"{horas_op:.2f} h"
    )

    c[3].metric(
        "ROP",
        f"{rop:.2f} m/h"
    )

    c = st.columns(3)

    c[0].metric(
        "HORAS APONTADAS",
        f"{horas_total:.2f} h"
    )

    c[1].metric(
        "MECÂNICA CORRETIVA",
        f"{horas_mec:.2f} h"
    )

    c[2].metric(
        "DISPONIBILIDADE",
        f"{disponibilidade:.1f}%"
    )

    st.subheader(
        "Resumo por classificação"
    )

    if not ap.empty:

        resumo = (

            ap.groupby(
                "classificacao",
                dropna=False
            )["horas"]

            .sum()

            .reset_index()

        )

        st.bar_chart(
            resumo.set_index(
                "classificacao"
            )
        )

    else:

        st.info(
            "Ainda não existem apontamentos."
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
            "Cadastre pelo menos uma Sonda, "
            "uma Equipe e um Furo antes "
            "de criar o boletim."
        )

        st.stop()

    if (
        "boletim_edit_id"
        not in st.session_state
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
            list(map_s.keys()),
            format_func=lambda x: map_s[x]
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
                row_s.iloc[0]["equipe_id"]
            )

        idx_e = (

            list(map_e.keys()).index(
                equipe_padrao
            )

            if equipe_padrao in map_e

            else 0

        )

        equipe_id = d.selectbox(
            "Equipe",
            list(map_e.keys()),
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

        if (
            h_fim
            and
            h_fim < h_ini
        ):

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
                    ?,?,?,?,?,?,?,?,?,?,?
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
                "Boletim criado. Agora adicione "
                "manobras e atividades abaixo."
            )

            st.rerun()

    bid = st.session_state.boletim_edit_id

    # ========================================================
    # CONTEÚDO DO BOLETIM
    # ========================================================

    if bid:

        # ----------------------------------------------------
        # MANOBRAS
        # ----------------------------------------------------

        st.divider()

        st.subheader(
            "⛏️ MANOBRAS E PERFURAÇÃO"
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

                if av

                else 0

            )

            st.info(
                f"Avanço automático: {av:.2f} m "
                f"| Recuperação automática: "
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
                    "O valor 'Até' deve ser "
                    "maior que 'De'."
                )

            elif recuperado > (
                ate_m - de_m
            ):

                st.error(
                    "A recuperação não pode ser "
                    "maior que o avanço."
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
                        ?,?,?,?,?,?,?,?,?,?,?
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

            ).round(1)

            st.dataframe(
                view,
                use_container_width=True,
                hide_index=True
            )

        # ====================================================
        # TEMPOS E PARADAS
        # ====================================================

        st.divider()

        st.subheader(
            "⏱️ TEMPOS E PARADAS"
        )

        st.caption(
            "Selecione o código da atividade. "
            "O grupo, atividade e classificação "
            "serão preenchidos automaticamente."
        )

        acts = query(
            """
            SELECT *
            FROM atividades
            ORDER BY codigo
            """
        )

        codes = acts["codigo"].tolist()

        if len(codes) == 0:

            st.warning(
                "Nenhum código de atividade "
                "cadastrado."
            )

        else:

            with st.form(
                "nova_atividade",
                clear_on_submit=True
            ):

                c1, c2 = st.columns(
                    [1, 3]
                )

                codigo = c1.selectbox(
                    "Código da atividade",
                    codes
                )

                ar = activity_row(
                    codigo
                )

                c2.info(
                    f"""
**Grupo:** {ar.get("grupo", "")}

**Atividade / Evento:** {ar.get("atividade", "")}

**Classificação:** {ar.get("classificacao", "")}
                    """
                )

                st.markdown(
                    "### Horário"
                )

                c1, c2, c3, c4 = st.columns(4)

                inicio = c1.time_input(
                    "Início",
                    value=time(7, 0)
                )

                fim = c2.time_input(
                    "Fim",
                    value=time(8, 0)
                )

                horas = horas_intervalo(
                    inicio,
                    fim
                )

                minutos = round(
                    horas * 60
                )

                c3.metric(
                    "Duração (h)",
                    f"{horas:.2f}"
                )

                c4.metric(
                    "Duração (min)",
                    f"{minutos}"
                )

                c1, c2 = st.columns(2)

                horimetro = c1.number_input(
                    "Horímetro",
                    min_value=0.0,
                    step=0.1
                )

                obs = c2.text_input(
                    "Observações"
                )

                add_a = st.form_submit_button(
                    "➕ ADICIONAR ATIVIDADE",
                    type="primary"
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
                        ?,?,?,?,?,?,?
                    )
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
                    "Atividade adicionada "
                    "com sucesso."
                )

                st.rerun()

        # ----------------------------------------------------
        # TABELA DE TEMPOS E PARADAS
        # ----------------------------------------------------

        dfa = query(
            """
            SELECT

                p.id,

                p.codigo_atividade
                AS "Código",

                a.grupo
                AS "Grupo",

                a.atividade
                AS "Atividade / Evento",

                a.classificacao
                AS "Classificação",

                p.hora_inicio
                AS "Início",

                p.hora_fim
                AS "Fim",

                p.horas
                AS "Duração (h)",

                ROUND(
                    p.horas * 60
                )
                AS "Duração (min)",

                p.observacao
                AS "Observações"

            FROM apontamentos p

            LEFT JOIN atividades a
                ON a.codigo=p.codigo_atividade

            WHERE p.boletim_id=?

            ORDER BY p.id
            """,
            (bid,)
        )

        if dfa.empty:

            st.info(
                "Nenhuma atividade lançada "
                "neste boletim."
            )

        else:

            tabela_visual = dfa.drop(
                columns=["id"]
            )

            st.dataframe(
                tabela_visual,
                use_container_width=True,
                hide_index=True
            )

            # ------------------------------------------------
            # EXCLUIR ATIVIDADE
            # ------------------------------------------------

            st.markdown(
                "#### 🗑️ Excluir lançamento"
            )

            opcoes_excluir = (
                dfa["id"].tolist()
            )

            def descricao_apontamento(
                id_ap
            ):

                linha = dfa[
                    dfa["id"]
                    ==
                    id_ap
                ].iloc[0]

                return (

                    f"Código {linha['Código']} | "

                    f"{linha['Atividade / Evento']} | "

                    f"{linha['Início']} - "

                    f"{linha['Fim']}"

                )

            c1, c2 = st.columns(
                [4, 1]
            )

            apontamento_excluir = c1.selectbox(
                "Selecione a atividade",
                opcoes_excluir,
                format_func=descricao_apontamento
            )

            if c2.button(
                "🗑️ Excluir"
            ):

                delete(
                    "apontamentos",
                    apontamento_excluir
                )

                st.success(
                    "Atividade excluída."
                )

                st.rerun()

        # ====================================================
        # RESUMO OPERACIONAL DO TURNO
        # ====================================================

        st.divider()

        st.subheader(
            "📊 RESUMO OPERACIONAL DO TURNO"
        )

        resumo = resumo_operacional_boletim(
            bid
        )

        # ----------------------------------------------------
        # LINHA 1
        # ----------------------------------------------------

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "METROS FURADOS",
            f"{resumo['metros_furados']:.2f} m"
        )

        c2.metric(
            "RECUPERAÇÃO (m)",
            f"{resumo['recuperacao_m']:.2f} m"
        )

        c3.metric(
            "RECUPERAÇÃO %",
            f"{resumo['recuperacao_pct']:.1f}%"
        )

        c4.metric(
            "HORAS PROGRAMADAS",
            f"{resumo['horas_programadas']:.2f} h"
        )

        c5.metric(
            "ROP (m/h)",
            f"{resumo['rop']:.2f}"
        )

        # ----------------------------------------------------
        # LINHA 2
        # ----------------------------------------------------

        c1, c2, c3, c4, c5 = st.columns(5)

        c1.metric(
            "H. DIRETA",
            f"{resumo['h_direta']:.2f} h"
        )

        c2.metric(
            "H. APOIO OPERACIONAL",
            f"{resumo['h_apoio']:.2f} h"
        )

        c3.metric(
            "H. MANUT. PREVENTIVA",
            f"{resumo['h_prev']:.2f} h"
        )

        c4.metric(
            "H. MECÂNICA CORRETIVA",
            f"{resumo['h_mec']:.2f} h"
        )

        c5.metric(
            "H. PARADA EXTERNA",
            f"{resumo['h_parada_externa']:.2f} h"
        )

        # ----------------------------------------------------
        # LINHA 3
        # ----------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "H. ADMINISTRATIVA",
            f"{resumo['h_administrativa']:.2f} h"
        )

        c2.metric(
            "HORAS DE PARADA",
            f"{resumo['horas_parada']:.2f} h"
        )

        c3.metric(
            "DISPONIBILIDADE FÍSICA",
            f"{resumo['disponibilidade_fisica']:.1f}%"
        )

        c4.metric(
            "UTILIZAÇÃO",
            f"{resumo['utilizacao']:.1f}%"
        )

        # ====================================================
        # OBSERVAÇÕES GERAIS
        # ====================================================

        st.divider()

        st.subheader(
            "📝 OBSERVAÇÕES GERAIS"
        )

        boletim_atual = query(
            """
            SELECT observacoes
            FROM boletins
            WHERE id=?
            """,
            (bid,)
        )

        obs_atual = ""

        if not boletim_atual.empty:

            obs_atual = (

                boletim_atual
                .iloc[0]["observacoes"]

                or

                ""

            )

        nova_obs = st.text_area(
            "Observações gerais do turno",
            value=obs_atual,
            height=150,
            key=f"observacoes_gerais_{bid}"
        )

        if st.button(
            "💾 Salvar observações"
        ):

            execute(
                """
                UPDATE boletins
                SET observacoes=?
                WHERE id=?
                """,
                (
                    nova_obs,
                    bid
                )
            )

            st.success(
                "Observações salvas."
            )

        # ====================================================
        # EXCEL
        # ====================================================

        st.divider()

        if st.button(
            "📥 Gerar Excel deste Boletim",
            type="primary"
        ):

            st.download_button(

                "⬇️ Baixar Excel",

                excel_boletim(bid),

                file_name=(
                    f"BOLETIM_DDH_{bid}.xlsx"
                ),

                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                )
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
        ORDER BY data DESC, id DESC
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
            ids
        )

        c1, c2, c3 = st.columns(3)

        if c1.button(
            "✏️ Abrir para lançamento"
        ):

            st.session_state.boletim_edit_id = int(
                bid
            )

            st.success(
                "Boletim selecionado. "
                "Abra 'Novo Boletim' para continuar."
            )

        c2.download_button(

            "📥 Excel",

            excel_boletim(
                int(bid)
            ),

            file_name=(
                f"BOLETIM_DDH_{bid}.xlsx"
            ),

            mime=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
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
                (
                    f"{x} - "
                    f"{df[df.id == x].iloc[0].nome}"
                )
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
                            ?,?,?,?
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

        opts = dfc["id"].tolist()

        def fmt_colaborador(x):

            return dfc[
                dfc.id == x
            ].iloc[0]["nome"]

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
                                ?,?,?,?,?,?,?
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
            "Cadastre uma equipe antes "
            "de cadastrar uma sonda."
        )

    else:

        opts = dfe["id"].tolist()

        def fmt_equipe(x):

            return dfe[
                dfe.id == x
            ].iloc[0]["codigo"]

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
                                ?,?,?,?,?,?
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

    # --------------------------------------------------------
    # FUROS
    # --------------------------------------------------------

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
                                ?,?,?,?,?,?,?,?,?,?
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
                            "Identificação já cadastrada."
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

    # --------------------------------------------------------
    # CÓDIGOS DE ATIVIDADES
    # --------------------------------------------------------

    with tab_a:

        st.caption(
            "Edite ou cadastre os códigos "
            "para deixá-los exatamente iguais "
            "aos códigos da sua planilha."
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
                        ?,?,?,?
                    )

                    ON CONFLICT(codigo)

                    DO UPDATE SET

                        grupo=excluded.grupo,

                        atividade=excluded.atividade,

                        classificacao=
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
