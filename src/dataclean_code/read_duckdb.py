import duckdb
con = duckdb.connect("yelp_user.db")
df = con.execute("SELECT * FROM review LIMIT 5").fetchdf()

print(df)