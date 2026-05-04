"""
generate_ddl.py
---------------
Conecta a DB_SIERRADRON y extrae el DDL completo de todas las tablas
(columnas, tipos, nullability, defaults, PKs, FKs, índices y constraints).
Genera dos archivos:
  - ddl_DB_SIERRADRON.sql  : script SQL ejecutable para recrear la base en otro servidor
  - ddl_DB_SIERRADRON.md   : resumen en Markdown con la estructura de cada tabla
"""

import os
import sys
import datetime
import pyodbc
from dotenv import load_dotenv

load_dotenv(override=True)

# ─────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────
SERVER   = os.environ["DB_DRON_SERVER"]
DATABASE = os.environ["DB_DRON_DATABASE"]
USERNAME = os.environ["DB_DRON_USERNAME"]
PASSWORD = os.environ["DB_DRON_PASSWORD"]
TIMEOUT  = int(os.getenv("DB_DRON_CONN_TIMEOUT", "10"))
ENCRYPT  = os.getenv("DB_DRON_ENCRYPT", "yes")
TRUST    = os.getenv("DB_DRON_TRUST_CERT", "yes")

OUTPUT_SQL = f"ddl_{DATABASE}.sql"
OUTPUT_MD  = f"ddl_{DATABASE}.md"


# ─────────────────────────────────────────
# Conexión
# ─────────────────────────────────────────
def get_connection():
    preferred_drivers = [
        os.getenv("DB_DRON_DRIVER", "").strip(),
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server",
    ]
    available = [d.strip() for d in pyodbc.drivers()]
    drivers   = [d for d in preferred_drivers if d and d in available]

    if not drivers:
        print(f"[ERROR] No se encontraron drivers ODBC compatibles. Disponibles: {available}")
        sys.exit(1)

    # Candidatos de servidor
    port = os.getenv("DB_DRON_PORT", "").strip()
    candidates = []
    if port and "\\" not in SERVER and "," not in SERVER:
        candidates.append(f"tcp:{SERVER},{port}")
    candidates.append(SERVER)
    for fb in os.getenv("DB_DRON_SERVER_FALLBACKS", "").split(","):
        fb = fb.strip()
        if fb:
            candidates.append(fb)

    for server_candidate in candidates:
        for driver in drivers:
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server_candidate};"
                f"DATABASE={DATABASE};"
                f"UID={USERNAME};"
                f"PWD={PASSWORD};"
                f"Encrypt={'yes' if ENCRYPT in ('1','true','yes') else 'no'};"
                f"TrustServerCertificate={'yes' if TRUST in ('1','true','yes') else 'no'};"
                f"Connection Timeout={TIMEOUT};"
            )
            try:
                conn = pyodbc.connect(conn_str)
                print(f"[OK] Conectado → Server={server_candidate} | DB={DATABASE} | Driver={driver}")
                return conn
            except Exception as e:
                print(f"[WARN] {server_candidate} / {driver} → {e}")

    print("[ERROR] No se pudo establecer conexión a la base de datos.")
    sys.exit(1)


# ─────────────────────────────────────────
# Queries de extracción
# ─────────────────────────────────────────

SQL_TABLES = """
SELECT
    t.TABLE_SCHEMA,
    t.TABLE_NAME,
    t.TABLE_TYPE
FROM INFORMATION_SCHEMA.TABLES t
WHERE t.TABLE_TYPE IN ('BASE TABLE','VIEW')
ORDER BY t.TABLE_SCHEMA, t.TABLE_NAME;
"""

SQL_COLUMNS = """
SELECT
    c.COLUMN_NAME,
    c.ORDINAL_POSITION,
    c.COLUMN_DEFAULT,
    c.IS_NULLABLE,
    c.DATA_TYPE,
    c.CHARACTER_MAXIMUM_LENGTH,
    c.NUMERIC_PRECISION,
    c.NUMERIC_SCALE,
    c.DATETIME_PRECISION,
    COLUMNPROPERTY(OBJECT_ID(c.TABLE_SCHEMA+'.'+c.TABLE_NAME), c.COLUMN_NAME, 'IsIdentity') AS IS_IDENTITY,
    IDENT_SEED(c.TABLE_SCHEMA+'.'+c.TABLE_NAME)  AS IDENT_SEED,
    IDENT_INCR(c.TABLE_SCHEMA+'.'+c.TABLE_NAME)  AS IDENT_INCR
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_SCHEMA = ? AND c.TABLE_NAME = ?
ORDER BY c.ORDINAL_POSITION;
"""

SQL_PKS = """
SELECT
    kcu.COLUMN_NAME,
    kcu.ORDINAL_POSITION,
    tc.CONSTRAINT_NAME
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
    ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
    AND tc.TABLE_SCHEMA   = kcu.TABLE_SCHEMA
    AND tc.TABLE_NAME     = kcu.TABLE_NAME
WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
  AND tc.TABLE_SCHEMA = ?
  AND tc.TABLE_NAME   = ?
ORDER BY kcu.ORDINAL_POSITION;
"""

SQL_FKS = """
SELECT
    fk.name                        AS FK_NAME,
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id)       AS COLUMN_NAME,
    OBJECT_NAME(fkc.referenced_object_id)                      AS REF_TABLE,
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS REF_COLUMN,
    fk.delete_referential_action_desc AS ON_DELETE,
    fk.update_referential_action_desc AS ON_UPDATE
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE OBJECT_SCHEMA_NAME(fk.parent_object_id) = ?
  AND OBJECT_NAME(fk.parent_object_id)        = ?
ORDER BY fk.name, fkc.constraint_column_id;
"""

SQL_INDEXES = """
SELECT
    i.name         AS INDEX_NAME,
    i.type_desc    AS INDEX_TYPE,
    i.is_unique,
    i.is_primary_key,
    STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS COLUMNS
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns       c  ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE OBJECT_SCHEMA_NAME(i.object_id) = ?
  AND OBJECT_NAME(i.object_id)        = ?
  AND i.is_primary_key = 0          -- PKs ya se muestran por separado
  AND i.name IS NOT NULL
GROUP BY i.name, i.type_desc, i.is_unique, i.is_primary_key
ORDER BY i.name;
"""

SQL_CHECK_CONSTRAINTS = """
SELECT DISTINCT
    cc.CONSTRAINT_NAME,
    cc.CHECK_CLAUSE
FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS cc
JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
    ON cc.CONSTRAINT_NAME  = tc.CONSTRAINT_NAME
    AND cc.CONSTRAINT_SCHEMA = tc.TABLE_SCHEMA
WHERE tc.TABLE_SCHEMA = ?
  AND tc.TABLE_NAME   = ?
ORDER BY cc.CONSTRAINT_NAME;
"""


# ─────────────────────────────────────────
# Helpers de formato
# ─────────────────────────────────────────
def col_type_str(col):
    dt = col["DATA_TYPE"].upper()
    if dt in ("CHAR", "VARCHAR", "NCHAR", "NVARCHAR", "BINARY", "VARBINARY"):
        length = col["CHARACTER_MAXIMUM_LENGTH"]
        if length == -1:
            length = "MAX"
        return f"{dt}({length})"
    if dt in ("NUMERIC", "DECIMAL"):
        return f"{dt}({col['NUMERIC_PRECISION']},{col['NUMERIC_SCALE']})"
    if dt in ("FLOAT", "REAL"):
        if col["NUMERIC_PRECISION"]:
            return f"{dt}({col['NUMERIC_PRECISION']})"
        return dt
    if dt in ("DATETIME2", "TIME", "DATETIMEOFFSET"):
        if col["DATETIME_PRECISION"] is not None:
            return f"{dt}({col['DATETIME_PRECISION']})"
        return dt
    return dt


def fetch_all_as_dicts(cursor, sql, params=()):
    cursor.execute(sql, params)
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


# ─────────────────────────────────────────
# Generador de DDL por tabla
# ─────────────────────────────────────────
def build_create_table(schema, table, columns, pks, fks, checks):
    lines = []
    pk_cols = {pk["COLUMN_NAME"] for pk in pks}
    fk_cols = {fk["COLUMN_NAME"]: fk for fk in fks}

    # Columnas
    col_defs = []
    for col in columns:
        name   = col["COLUMN_NAME"]
        dtype  = col_type_str(col)
        is_id  = col["IS_IDENTITY"]
        seed   = col["IDENT_SEED"]
        incr   = col["IDENT_INCR"]
        null   = "NOT NULL" if col["IS_NULLABLE"] == "NO" else "NULL"
        defval = ""
        if col["COLUMN_DEFAULT"] and not is_id:
            defval = f" DEFAULT {col['COLUMN_DEFAULT']}"

        identity_clause = f" IDENTITY({int(seed)},{int(incr)})" if is_id else ""
        col_defs.append(f"    [{name}] {dtype}{identity_clause} {null}{defval}")

    # PK constraint
    if pks:
        pk_name = pks[0]["CONSTRAINT_NAME"]
        pk_col_list = ", ".join(f"[{pk['COLUMN_NAME']}]" for pk in pks)
        col_defs.append(f"    CONSTRAINT [{pk_name}] PRIMARY KEY ({pk_col_list})")

    # FK constraints
    fk_seen = {}
    for fk in fks:
        fkname = fk["FK_NAME"]
        if fkname not in fk_seen:
            on_del = f" ON DELETE {fk['ON_DELETE']}" if fk["ON_DELETE"] != "NO_ACTION" else ""
            on_upd = f" ON UPDATE {fk['ON_UPDATE']}" if fk["ON_UPDATE"] != "NO_ACTION" else ""
            col_defs.append(
                f"    CONSTRAINT [{fkname}] FOREIGN KEY ([{fk['COLUMN_NAME']}]) "
                f"REFERENCES [{fk['REF_TABLE']}]([{fk['REF_COLUMN']}]){on_del}{on_upd}"
            )
            fk_seen[fkname] = True

    # CHECK constraints
    for ck in checks:
        clause = ck['CHECK_CLAUSE']
        if clause:
            col_defs.append(f"    CONSTRAINT [{ck['CONSTRAINT_NAME']}] CHECK {clause}")

    body = ",\n".join(col_defs)
    return (
        f"CREATE TABLE [{schema}].[{table}] (\n"
        f"{body}\n"
        f");\nGO\n"
    )


def build_indexes_sql(schema, table, indexes):
    stmts = []
    for idx in indexes:
        unique     = "UNIQUE " if idx["is_unique"] else ""
        index_type = idx["INDEX_TYPE"]
        # CLUSTERED / NONCLUSTERED / etc.
        if index_type not in ("CLUSTERED", "NONCLUSTERED"):
            index_type = "NONCLUSTERED"
        stmts.append(
            f"CREATE {unique}{index_type} INDEX [{idx['INDEX_NAME']}]\n"
            f"    ON [{schema}].[{table}] ({idx['COLUMNS']});\nGO\n"
        )
    return "\n".join(stmts)


# ─────────────────────────────────────────
# Sección Markdown por tabla
# ─────────────────────────────────────────
def build_md_section(schema, table, table_type, columns, pks, fks, indexes):
    pk_cols = {pk["COLUMN_NAME"] for pk in pks}
    lines = []
    lines.append(f"\n## {schema}.{table}  {'*(VIEW)*' if table_type == 'VIEW' else ''}\n")
    lines.append("| PK | Columna | Tipo | Nullable | Default | Identity |")
    lines.append("|:--:|---------|------|:--------:|---------|:--------:|")
    for col in columns:
        pk_mark   = "✓" if col["COLUMN_NAME"] in pk_cols else ""
        dtype     = col_type_str(col)
        nullable  = col["IS_NULLABLE"]
        default   = col["COLUMN_DEFAULT"] or ""
        is_id     = "✓" if col["IS_IDENTITY"] else ""
        lines.append(
            f"| {pk_mark} | `{col['COLUMN_NAME']}` | {dtype} | {nullable} | {default} | {is_id} |"
        )

    if fks:
        lines.append("\n**Foreign Keys:**")
        for fk in fks:
            lines.append(
                f"- `{fk['COLUMN_NAME']}` → `{fk['REF_TABLE']}.{fk['REF_COLUMN']}` "
                f"(constraint: `{fk['FK_NAME']}`)"
            )

    if indexes:
        lines.append("\n**Índices:**")
        for idx in indexes:
            uniq = " UNIQUE" if idx["is_unique"] else ""
            lines.append(
                f"- `{idx['INDEX_NAME']}` [{idx['INDEX_TYPE']}{uniq}] → ({idx['COLUMNS']})"
            )

    return "\n".join(lines)


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f" Extracción DDL  ·  {DATABASE}  ·  {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'='*60}\n")

    conn   = get_connection()
    cursor = conn.cursor()

    # Obtener todas las tablas/vistas
    tables = fetch_all_as_dicts(cursor, SQL_TABLES)
    print(f"[INFO] Objetos encontrados: {len(tables)}\n")

    sql_sections  = []
    md_sections   = []

    header_sql = (
        f"-- DDL generado automáticamente desde {DATABASE}\n"
        f"-- Fecha: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"-- Servidor origen: {SERVER}\n"
        f"-- Generado por: generate_ddl.py\n"
        f"--\n"
        f"-- Para recrear la base de datos en otro servidor:\n"
        f"--   1. Crear la base de datos destino\n"
        f"--   2. Ejecutar este script en orden\n"
        f"-- ============================================================\n\n"
        f"USE [{DATABASE}];\nGO\n\n"
    )

    header_md = (
        f"# DDL — {DATABASE}\n\n"
        f"**Servidor origen:** `{SERVER}`  \n"
        f"**Fecha extracción:** {datetime.datetime.now():%Y-%m-%d %H:%M:%S}  \n"
        f"**Tablas/Vistas:** {len(tables)}\n\n"
        f"---\n"
    )

    sql_sections.append(header_sql)
    md_sections.append(header_md)

    # ─── Ordenar tablas por dependencias FK (padres primero) ───────────
    # Construir mapa de dependencias para poder hacer DROP en orden inverso
    # y CREATE en orden directo
    table_keys = [(t["TABLE_SCHEMA"], t["TABLE_NAME"]) for t in tables]
    fk_deps: dict[tuple, set] = {k: set() for k in table_keys}  # tabla → tablas de las que depende

    for tbl in tables:
        if tbl["TABLE_TYPE"] != "BASE TABLE":
            continue
        fks_tmp = fetch_all_as_dicts(cursor, SQL_FKS, (tbl["TABLE_SCHEMA"], tbl["TABLE_NAME"]))
        for fk in fks_tmp:
            ref = (tbl["TABLE_SCHEMA"], fk["REF_TABLE"])
            if ref in fk_deps and ref != (tbl["TABLE_SCHEMA"], tbl["TABLE_NAME"]):
                fk_deps[(tbl["TABLE_SCHEMA"], tbl["TABLE_NAME"])].add(ref)

    # Kahn's topological sort
    sorted_keys: list[tuple] = []
    visited: set[tuple] = set()

    def topo_visit(node):
        if node in visited:
            return
        visited.add(node)
        for dep in fk_deps.get(node, []):
            topo_visit(dep)
        sorted_keys.append(node)

    for k in table_keys:
        topo_visit(k)

    # Re-ordenar tables según sorted_keys
    key_to_tbl = {(t["TABLE_SCHEMA"], t["TABLE_NAME"]): t for t in tables}
    tables_ordered = [key_to_tbl[k] for k in sorted_keys if k in key_to_tbl]
    # ─────────────────────────────────────────────────────────────────────

    for tbl in tables_ordered:
        schema     = tbl["TABLE_SCHEMA"]
        table      = tbl["TABLE_NAME"]
        table_type = tbl["TABLE_TYPE"]

        print(f"  · {schema}.{table} ({table_type})")

        columns = fetch_all_as_dicts(cursor, SQL_COLUMNS, (schema, table))
        pks     = fetch_all_as_dicts(cursor, SQL_PKS, (schema, table))
        checks  = fetch_all_as_dicts(cursor, SQL_CHECK_CONSTRAINTS, (schema, table))

        if table_type == "BASE TABLE":
            fks     = fetch_all_as_dicts(cursor, SQL_FKS, (schema, table))
            indexes = fetch_all_as_dicts(cursor, SQL_INDEXES, (schema, table))
        else:
            fks     = []
            indexes = []

        # ── SQL ──────────────────────────────────────────
        sql_sections.append(f"-- ────────────────────────────────────────────────────\n")
        sql_sections.append(f"-- Tabla: {schema}.{table}\n")
        sql_sections.append(f"-- ────────────────────────────────────────────────────\n")

        if table_type == "BASE TABLE":
            sql_sections.append(
                f"IF OBJECT_ID('[{schema}].[{table}]', 'U') IS NOT NULL\n"
                f"    DROP TABLE [{schema}].[{table}];\nGO\n\n"
            )
            sql_sections.append(build_create_table(schema, table, columns, pks, fks, checks))
            idx_sql = build_indexes_sql(schema, table, indexes)
            if idx_sql:
                sql_sections.append(idx_sql)
        else:
            sql_sections.append(f"-- VISTA — se omite DDL automático para vistas\n-- {schema}.{table}\n\nGO\n")

        sql_sections.append("\n")

        # ── Markdown ─────────────────────────────────────
        md_sections.append(
            build_md_section(schema, table, table_type, columns, pks, fks, indexes)
        )

    cursor.close()
    conn.close()

    # Escribir archivos de salida
    with open(OUTPUT_SQL, "w", encoding="utf-8") as f:
        f.write("".join(sql_sections))

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_sections))

    print(f"\n[OK] Archivos generados:")
    print(f"     {OUTPUT_SQL}")
    print(f"     {OUTPUT_MD}")
    print(f"\n[INFO] Tablas/Vistas procesadas: {len(tables)}")


if __name__ == "__main__":
    main()
