import duckdb

def connect_db():
    return duckdb.connect("data/warehouse.duckdb")

def init_tables(con):
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    con.execute("CREATE TABLE IF NOT EXISTS raw.api_calls(" \
    "source VARCHAR, location VARCHAR, status INTEGER, body JSON, ingested_at TIMESTAMP)")

def save_api_call(con, source, location, status, body):
    con.execute("INSERT INTO raw.api_calls VALUES (?, ?, ?, ?, now())", [source, location, status, body])