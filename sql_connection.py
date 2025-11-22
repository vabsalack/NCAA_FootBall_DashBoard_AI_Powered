import mysql.connector
from sqlalchemy import create_engine
import requests

DB_NAME = "ncaafb_db"
SCHEMA_FILE = "schema.sql"
HOST_ID = "localhost"
USER_NAME = "root"
USER_PASSWORD = "root"


def connect_root():
    return mysql.connector.connect(
        host=HOST_ID,
        user=USER_NAME,
        password=USER_PASSWORD
    )

def _apply_schema(cursor):
    print(f"Creating {DB_NAME}", f"Loading schema file from ./{SCHEMA_FILE}", sep="\n")
    with open(SCHEMA_FILE) as f: schema = f.read()
    for stmt in schema.split(";"):
        s = stmt.strip()
        if s: cursor.execute(s + ";")
    print(f"Database {DB_NAME} is hot and fresh, ready to kill")

def ensure_database(cursor):
    cursor.execute("SHOW DATABASES;")
    dbs = [db[0] for db in cursor.fetchall()]
    if DB_NAME not in dbs:
        _apply_schema(cursor)
    print(f"Accessing {DB_NAME} database...")
    cursor.execute(f"USE {DB_NAME};")

def fetch_api(url):
    return requests.get(url).json()

def insert_incremental(df, table, engine):
    df.to_sql(table, engine, if_exists="append", index=False)

def main():
    conn = connect_root()
    cursor = conn.cursor()

    ensure_database(cursor)

    # engine = create_engine(f"mysql+mysqlconnector://root:root@localhost/{DB_NAME}")

    # users = fetch_api("https://api.example.com/users")
    # df_users = pd.json_normalize(users)
    # insert_incremental(df_users, "users", engine)

    conn.close()

if __name__ == "__main__":
    main()
