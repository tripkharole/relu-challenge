"""
Bonus challenge - simple web app that shows the scraped data in searchable tables.

Data source:
  * Supabase, when SUPABASE_URL and SUPABASE_KEY are set (tables `disney_cruises` and
    `ingredients_companies`, created/filled with upload_to_supabase.py), otherwise
  * the cleaned CSV files that ship with the app (data/*.csv).

Run locally:   pip install -r requirements.txt && python app.py
Deploy:        Render / Railway - start command `gunicorn app:app`
"""
import os
from pathlib import Path

import pandas as pd
import requests
from flask import Flask, abort, render_template_string

DATA_DIR = Path(__file__).resolve().parent / "data"
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

DATASETS = {
    "cruises": {"title": "Disney Cruise Line - cruises", "csv": "disney_results.csv", "table": "disney_cruises"},
    "companies": {"title": "IngredientsNetwork - companies", "csv": "ingredients_results.csv",
                  "table": "ingredients_companies"},
}

app = Flask(__name__)


def load(key: str) -> tuple[pd.DataFrame, str]:
    ds = DATASETS[key]
    if SUPABASE_URL and SUPABASE_KEY:
        rows, start = [], 0
        while True:   # PostgREST pagination
            r = requests.get(f"{SUPABASE_URL}/rest/v1/{ds['table']}?select=*",
                             headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                                      "Range": f"{start}-{start + 999}"}, timeout=30)
            r.raise_for_status()
            batch = r.json()
            rows += batch
            if len(batch) < 1000:
                break
            start += 1000
        return pd.DataFrame(rows), "Supabase"
    return pd.read_csv(DATA_DIR / ds["csv"]), "CSV"


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<link rel="stylesheet" href="https://cdn.datatables.net/2.0.8/css/dataTables.dataTables.min.css">
<style>
 body{font-family:system-ui,Segoe UI,Arial,sans-serif;margin:0;background:#f6f7f9;color:#1d2433}
 header{background:#12355b;color:#fff;padding:14px 24px;display:flex;gap:24px;align-items:center;flex-wrap:wrap}
 header a{color:#cfe3ff;text-decoration:none;font-weight:600} header a.on{color:#fff;border-bottom:2px solid #fff}
 main{padding:20px 24px} .meta{color:#5b6475;margin-bottom:12px}
 table.dataTable td{font-size:13px;vertical-align:top;max-width:420px}
 .wrap{background:#fff;border-radius:8px;padding:12px;box-shadow:0 1px 3px rgba(0,0,0,.08);overflow-x:auto}
</style></head><body>
<header><strong>Relu Consultancy - scraped data</strong>
{% for k, d in datasets.items() %}<a href="/{{ k }}" class="{{ 'on' if k == key else '' }}">{{ d.title }}</a>{% endfor %}
</header>
<main><h2>{{ title }}</h2>
<div class="meta">{{ n }} rows &middot; source: {{ data_source }}</div>
<div class="wrap">{{ table|safe }}</div></main>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/2.0.8/js/dataTables.min.js"></script>
<script>new DataTable('#data', {pageLength: 25, scrollX: true});</script>
</body></html>"""


@app.route("/")
@app.route("/<key>")
def show(key="cruises"):
    if key not in DATASETS:
        abort(404)
    df, source = load(key)
    table = df.to_html(table_id="data", classes="display compact", index=False, border=0, na_rep="")
    return render_template_string(PAGE, title=DATASETS[key]["title"], datasets=DATASETS, key=key,
                                  n=len(df), data_source=source, table=table)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
