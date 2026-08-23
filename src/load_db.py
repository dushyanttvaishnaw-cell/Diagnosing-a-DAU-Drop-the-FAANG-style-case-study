"""
load_db.py
Loads the daily session data into a SQLite database (metrics.db).
"""
import os
import sqlite3
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "metrics.db")

conn = sqlite3.connect(DB_PATH)
df = pd.read_csv(os.path.join(DATA_DIR, "daily_sessions.csv"), parse_dates=["date"])
df.to_sql("daily_sessions", conn, if_exists="replace", index=False)
conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON daily_sessions(date);")
conn.commit()
conn.close()

print(f"Database written to {DB_PATH}")
print("Table: daily_sessions")
