import duckdb
from pathlib import Path

DATA = Path('d:/personalization-agent-banking/data/preloaded/meridian_bank')
con = duckdb.connect(':memory:')

for name, fname in [('transactions','transactions.csv'),('wishlist','wishlist.csv'),('ad_spend','ad_spend_monthly.csv')]:
    p = DATA / fname
    if p.exists():
        con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_csv_auto('{p.as_posix()}', header=True, sample_size=-1)")

print('DATE RANGES')
for tbl, col in [('transactions','transaction_date'),('wishlist','added_date')]:
    r = con.execute(f'SELECT MIN(CAST({col} AS DATE)), MAX(CAST({col} AS DATE)), COUNT(*) FROM {tbl}').fetchone()
    print(f'  {tbl}: {r[0]} to {r[1]} ({r[2]} rows)')

print()
print('TRANSACTIONS PER MONTH')
rows = con.execute("""
    SELECT CAST(year(CAST(transaction_date AS DATE)) AS VARCHAR)
           ||'-'||LPAD(CAST(month(CAST(transaction_date AS DATE)) AS VARCHAR),2,'0') AS mo,
           COUNT(*) AS n,
           ROUND(SUM(amount)/1000,0) AS vk
    FROM transactions GROUP BY mo ORDER BY mo
""").fetchall()
for r in rows:
    print(f'  {r[0]}: {r[1]:>5} txns  ${r[2]:>8,.0f}K')

print()
print('WISHLIST PER MONTH')
rows = con.execute("""
    SELECT CAST(year(CAST(added_date AS DATE)) AS VARCHAR)
           ||'-'||LPAD(CAST(month(CAST(added_date AS DATE)) AS VARCHAR),2,'0') AS mo,
           COUNT(*) AS n
    FROM wishlist GROUP BY mo ORDER BY mo
""").fetchall()
for r in rows:
    print(f'  {r[0]}: {r[1]:>4} entries')

print()
print('AD_SPEND MONTHS')
rows = con.execute("SELECT year, month, COUNT(*) FROM ad_spend GROUP BY year, month ORDER BY year, month").fetchall()
for r in rows:
    print(f'  {r[0]}-{str(r[1]).zfill(2)}: {r[2]} rows')
