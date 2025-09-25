import psycopg2
from psycopg2.extras import RealDictCursor

CFG = dict(
    host="pgm-bp1ksg5v1lo5z2r8eo.rwlb.rds.aliyuncs.com",
    port=5432,
    dbname="Bio_data",
    user="nju_bio",
    password="980605Hyz",
    # sslmode="prefer",   # 可选：prefer=优先SSL，失败时自动改明文
    # sslmode="disable",  # 若 prefer 仍报错，再试 disable
)

TABLE = ("public", "organism_data")

with psycopg2.connect(**CFG, connect_timeout=10) as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        print("== Columns ==")
        cur.execute("""
            SELECT
              c.ordinal_position AS col_no,
              c.column_name, c.data_type,
              c.character_maximum_length AS char_len,
              c.numeric_precision, c.numeric_scale,
              c.is_nullable, c.column_default
            FROM information_schema.columns c
            WHERE c.table_schema=%s AND c.table_name=%s
            ORDER BY c.ordinal_position;
        """, TABLE)
        for r in cur.fetchall():
            print(dict(r))

        print("\n== Constraints (PK/UNIQUE) ==")
        cur.execute("""
            SELECT
              tc.constraint_type, kcu.column_name, tc.constraint_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema=%s AND tc.table_name=%s
              AND tc.constraint_type IN ('PRIMARY KEY','UNIQUE')
            ORDER BY tc.constraint_type, kcu.ordinal_position;
        """, TABLE)
        for r in cur.fetchall():
            print(dict(r))

        print("\n== Indexes ==")
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname=%s AND tablename=%s
            ORDER BY indexname;
        """, TABLE)
        for r in cur.fetchall():
            print(dict(r))

        print("\n== Row count ==")
        cur.execute('SELECT COUNT(*) AS cnt FROM public.organism_data;')
        print(cur.fetchone())

        print("\n== Guess sheet column + distinct values ==")
        candidates = ["sheet_name", "sheet", "category"]
        found = None
        for col in candidates:
            cur.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema=%s AND table_name=%s AND column_name=%s
            """, (TABLE[0], TABLE[1], col))
            if cur.fetchone():
                found = col
                break
        print("Sheet-like column:", found)
        if found:
            cur.execute(f"SELECT COUNT(*) AS cnt FROM public.organism_data WHERE {found}='Bacteria';")
            print("Rows with Bacteria:", cur.fetchone())
            cur.execute(f"SELECT DISTINCT {found} FROM public.organism_data ORDER BY 1 LIMIT 100;")
            print("Distinct values:", [row[found] for row in cur.fetchall()])

        print("\n== Sample rows (first 10) ==")
        cur.execute("SELECT * FROM public.organism_data LIMIT 10;")
        for r in cur.fetchall():
            print(dict(r))
