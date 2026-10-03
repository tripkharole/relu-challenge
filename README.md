# Relu Consultancy – Data Extraction Engineer Challenge

Run date: 3 Oct 2026. Python 3.12 + Playwright (Chromium), pandas, requests, BeautifulSoup.

```
relu_challenge/
├── objective1_disney/
│   ├── disney_cruise_scraper.py      # scraper (.py)
│   ├── disney_cruise_scraper.ipynb   # Colab notebook
│   ├── run.log                       # terminal output of the final run (incl. answers)
│   └── output/
│       ├── results.csv               # FINAL: 171 cruises (one row per cruise card)
│       ├── sailings.csv              # 948 individual sailing dates with stateroom prices
│       ├── raw_cruises.csv / .json   # temporary raw data before cleaning
├── objective2_ingredients/
│   ├── ingredients_network_scraper.py
│   ├── ingredients_network_scraper.ipynb
│   ├── run.log
│   └── output/
│       ├── results.csv                         # FINAL: 185 companies, 10 required fields
│       ├── results_complete_profiles_only.csv  # 76 companies that publish every field
│       ├── temp_raw_companies.csv              # temporary CSV before cleaning
│       └── search_results_raw.json / search_cards_raw.csv
└── bonus_webapp/                     # Flask app + optional Supabase upload
```

## Setup
```
pip install playwright pandas requests beautifulsoup4 lxml
python -m playwright install chromium
python objective1_disney/disney_cruise_scraper.py
python objective2_ingredients/ingredients_network_scraper.py
```

---

## Objective 1 – Disney Cruise Line

**Steps**
1. The scraper opens `https://disneycruise.disney.go.com/en-in/` and accepts the cookie banner.
2. It clicks **View Dates**. A `--port "Port Canaveral, Florida"` option sets the *Departing from* filter first; the default is no filter, which returns every cruise.
3. It waits for the result cards.
4. It scrolls to the end of the infinite list and loads all **35 pages**. While scrolling it reads every card from the DOM: title, banner, ports, price and the "Show N Dates" button. It also captures the site's own page responses (`available-products`).
   - For each card it requests that card's sailing list, which is the same call the *Show N Dates* button makes. This gives every date, ship and stateroom price.
   - It then applies the site's **More Filters → "Themed or Holiday cruise"** filter (Halloween on the High Seas + Very Merrytime) to tag the holiday cruises.
5. Cleaning:
   - Whitespace is trimmed.
   - Duplicates are removed, both exact rows and the same product + itinerary served on two pages.
   - Location fields are never empty. Departure and arrival ports come from the title. Round trips with no port stops (Singapore) are marked "At Sea (no ports of call…)".
   - Sold-out stateroom categories are marked "Unavailable".
6. The script writes `results.csv` (plus `sailings.csv`) and prints the answers.

**Robustness**
- Akamai blocks headless Chrome, so the browser runs headed (on a server, use `xvfb-run`).
- Requests are retried with back-off and paced with random delays.
- A second slow scroll pass catches cards the virtual list skipped.
- Extra page sweeps continue until the unique cards add up to the site counter (948 sailings), because the "Recommended" order can shift between pages.
- If the browser tab is lost, a fresh tab is opened and the run resumes.

**Answers**

| # | Question | Answer |
|---|---|---|
| i | Cruises with Pacific as destination | **2** (site filter *Pacific Coast Cruises*; 5 sailing dates) |
| ii | Total cruises | **171** cruise cards (948 individual sailing dates; the site's header reads "948 Cruises") |
| iii | Holiday cruises | **71** (Very Merrytime 44 + Halloween on the High Seas 27, from the site's holiday filter) |
| iv | Cruises offering more than 2 dates | **67** |
| v | Cruises departing Miami and London | **0**: Disney sails from neither port. The nearest ports are Fort Lauderdale (Miami area, 50 cruises) and Southampton (London area, 10 cruises), 60 combined |

## Objective 2 – IngredientsNetwork.com

**Steps**
1. The scraper opens `https://www.ingredientsnetwork.com/`.
2. It clicks **Search**.
3. It waits for the result cards.
   - The page loads one JSON document with all **3,962 results**: 3,777 products and 185 suppliers, each with a category bit-mask.
   - The supplier cards are read from the DOM.
   - Every supplier profile page is visited, with 3 polite workers and retries. Each visit extracts *Company Name, Company Description, Sales Markets, Primary Business Activity, Categories, Events, Address, Email, Telephone, Website*.
   - Contact details come from the profile's contact block. Cloudflare-protected e-mails are decoded, and the page's schema.org JSON-LD serves as a fallback.
4. The raw extraction is saved to `temp_raw_companies.csv` **before cleaning**. Cleaning then:
   - fixes HTML entities and whitespace;
   - validates e-mails;
   - normalises websites and phone numbers;
   - de-duplicates on row, company ID and name + website.
5. `results.csv` is written. All 185 companies are kept. A field that a company does not publish on its profile reads `Not listed on website` instead of being left empty. Spot checks confirmed these fields are genuinely absent on the site, not missed by the parser. `results_complete_profiles_only.csv` holds the 76 companies that publish every required field.

**Answers** (the site's category facets, cross-checked against the categories scraped from every company profile; both methods agree)

| # | Question | Answer |
|---|---|---|
| i | Total ingredients | **2,575** products listed under *Ingredients* |
| ii | Total finished products | **766** products listed under *Finished Products* |
| iii | Companies with Herbs & Spices | **22** |
| iv | Companies with Physical delivery formats | **55** |
| v | Companies in Cognitive & Mental Health | **47** |

Both sites change daily (prices, dates, listings), so a later run can give slightly different numbers.

---

## Bonus – web app
`bonus_webapp/app.py` is a Flask app that shows both cleaned datasets as searchable, sortable tables.
- **Data source:** Supabase when `SUPABASE_URL` and `SUPABASE_KEY` are set; otherwise the bundled CSVs in `bonus_webapp/data/`.
- **Supabase setup:** `python upload_to_supabase.py --sql` prints the `CREATE TABLE` SQL. `python upload_to_supabase.py` uploads the rows.
- **Deploy on Render:** build command `pip install -r requirements.txt`, start command `gunicorn app:app`.
