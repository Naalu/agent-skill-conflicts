"""Run ;-separated SQL from stdin against the persistent pilot database and print results."""
import duckdb, sys
import pandas as pd
con = duckdb.connect('pilot.duckdb')
con.execute("SET threads=1; SET memory_limit='2GB';")
con.execute("CREATE OR REPLACE VIEW a AS SELECT * FROM read_parquet('slim/*.parquet')")
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 110); pd.set_option('display.max_rows', 300)
for stmt in [s for s in sys.stdin.read().split(';') if s.strip()]:
    r = con.execute(stmt)
    if r.description and r.description[0][0] not in ('Count',):
        print(r.fetchdf().to_string(index=False)); print()
