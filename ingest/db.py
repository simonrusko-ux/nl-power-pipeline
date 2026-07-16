import duckdb

def connectDB():
    return duckdb.connect()

def init_tables(con):
    con.execute("CREATE SCHEMA IF NOT EXISTS raw"
                )