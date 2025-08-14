import duckdb

con = duckdb.connect("yelp_user.db")


con.execute("""
    CREATE TABLE review AS
    SELECT * FROM read_json_auto('../query_yelp/origin_dataset/review_query.json')
""")

con.execute("""
    CREATE TABLE tip AS
    SELECT * FROM read_json_auto('../query_yelp/origin_dataset/tip_query.json')
""")

con.execute("""
    CREATE TABLE user AS
    SELECT * FROM read_json_auto('../query_yelp/origin_dataset/user_query.json')
""")

print(con.execute("SHOW TABLES").fetchdf())
