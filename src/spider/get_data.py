import snowflake.connector
import pandas as pd

conn = snowflake.connector.connect(
    user='richardspider',
    password='UCBquery123456',
    account='RSRSBDK-YDB67606'
)

tables = [
    "ADVISORIES", "DEPENDENCIES", "DEPENDENCYGRAPHEDGES",
    "DEPENDENTS", "NUGETREQUIREMENTS", "PACKAGEVERSIONHASHES",
    "PACKAGEVERSIONS", "PACKAGEVERSIONTOPROJECT",
    "PROJECTS", "SNAPSHOTS"
]

for t in tables:
    df = pd.read_sql(f"SELECT * FROM DEPS_DEV_V1.DEPS_DEV_V1.{t}", conn)

    df.to_csv(f"{t}.csv", index=False)
    print(f"download {t}.csv")

conn.close()
