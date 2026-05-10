import requests, sqlite3, time, random
from datetime import datetime

API_KEY = "78BE42F6737E4F6EA6CC817975429547"
STORE_TAG = "fahadalbalawi-20"

def setup_db():
    conn = sqlite3.connect("prices.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT, store TEXT, title TEXT,
        price REAL, url TEXT, fetched_at TEXT)""")
    conn.commit()
    return conn

def search_amazon(term):
    r = requests.get("https://api.rainforestapi.com/request", params={
        "api_key": API_KEY, "type": "search",
        "amazon_domain": "amazon.sa", "search_term": term
    }, timeout=30)
    results = []
    for item in r.json().get("search_results", [])[:5]:
        price = item.get("price", {}).get("value")
        if price:
            asin = item.get("asin","")
            results.append({
                "store": "امازون السعودية",
                "title": item.get("title","")[:80],
                "price": float(str(price).replace(",","")),
                "url": f"https://www.amazon.sa/dp/{asin}?tag={STORE_TAG}"
            })
    return results

def save(conn, product, results):
    for r in results:
        conn.execute("INSERT INTO prices (product,store,title,price,url,fetched_at) VALUES (?,?,?,?,?,?)",
            (product, r["store"], r["title"], r["price"], r["url"], datetime.now().isoformat()))
    conn.commit()

def show(conn, product):
    rows = conn.execute("SELECT store,title,price,url FROM prices WHERE product=? ORDER BY price", (product,)).fetchall()
    print(f"\n{'='*60}")
    print(f"نتائج: {product}")
    print(f"{'='*60}")
    for store,title,price,url in rows:
        print(f"\n{store}")
        print(f"  {title[:60]}")
        print(f"  السعر: {price:,.0f} ريال")
        print(f"  {url[:70]}")
    if len(rows) >= 2:
        saving = rows[-1][2] - rows[0][2]
        print(f"\nتوفير: {saving:,.0f} ريال")

products = ["iPhone 15", "Samsung Galaxy S24"]
conn = setup_db()
for p in products:
    print(f"جاري البحث: {p}")
    results = search_amazon(p)
    save(conn, p, results)
    show(conn, p)
    time.sleep(random.uniform(2,4))
conn.close()
print("\nتم! البيانات محفوظة في prices.db")
