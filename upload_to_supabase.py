"""
Uploads the cleaned CSVs to Supabase (PostgREST insert).

1. Create the tables once in the Supabase SQL editor with the SQL printed by `python upload_to_supabase.py --sql`
2. export SUPABASE_URL=https://<project>.supabase.co  SUPABASE_KEY=<service_role or anon key with insert policy>
3. python upload_to_supabase.py
"""
import os
import re
import sys
from pathlib import Path

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parent / "data"
TABLES = {"disney_cruises": "disney_results.csv", "ingredients_companies": "ingredients_results.csv"}


def column_name(col: str) -> str:
    """'Price From (USD, 2 Guests)' -> 'price_from_usd_2_guests'"""
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", col.lower())).strip("_")


def create_sql() -> str:
    out = []
    for table, csv in TABLES.items():
        cols = ",\n  ".join(f'"{column_name(c)}" text' for c in pd.read_csv(DATA_DIR / csv, nrows=1).columns)
        out.append(f"create table if not exists {table} (\n  id bigserial primary key,\n  {cols}\n);")
    return "\n\n".join(out)


def upload():
    url, key = os.environ["SUPABASE_URL"].rstrip("/"), os.environ["SUPABASE_KEY"]
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
               "Prefer": "return=minimal"}
    for table, csv in TABLES.items():
        df = pd.read_csv(DATA_DIR / csv, dtype=str).fillna("")
        df.columns = [column_name(c) for c in df.columns]
        records = df.to_dict(orient="records")
        for i in range(0, len(records), 500):
            r = requests.post(f"{url}/rest/v1/{table}", json=records[i:i + 500], headers=headers, timeout=60)
            r.raise_for_status()
        print(f"{table}: {len(records)} rows uploaded")


if __name__ == "__main__":
    print(create_sql()) if "--sql" in sys.argv else upload()
