from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import requests
import sqlite3
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

API_KEY = "78BE42F6737E4F6EA6CC817975429547"
STORE_TAG = "fahadalbalawi-20"

def get_db():
    conn = sqlite3.connect("prices.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT, store TEXT, title TEXT,
        price REAL, url TEXT, fetched_at TEXT)""")
    conn.commit()
    return conn

def search_amazon(term):
    r = requests.get("https://api.rainforestapi.com/request", params={
        "api_key": API_KEY,
        "type": "search",
        "amazon_domain": "amazon.sa",
        "search_term": term
    }, timeout=30)
    results = []
    if r.status_code == 200:
        for item in r.json().get("search_results", [])[:6]:
            price = item.get("price", {}).get("value")
            if price:
                asin = item.get("asin", "")
                results.append({
                    "store": "أمازون السعودية",
                    "title": item.get("title", "")[:80],
                    "price": float(str(price).replace(",", "")),
                    "url": f"https://www.amazon.sa/dp/{asin}?tag={STORE_TAG}",
                    "image": item.get("image", ""),
                    "rating": item.get("rating", 0),
                    "ratings_total": item.get("ratings_total", 0),
                })
    return sorted(results, key=lambda x: x["price"])

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/search")
async def search(q: str):
    if not q or len(q) < 2:
        return JSONResponse({"error": "اكتب اسم المنتج"}, status_code=400)

    results = search_amazon(q)

    # احفظ في قاعدة البيانات
    conn = get_db()
    for r in results:
        conn.execute(
            "INSERT INTO prices (product,store,title,price,url,fetched_at) VALUES (?,?,?,?,?,?)",
            (q, r["store"], r["title"], r["price"], r["url"], datetime.now().isoformat())
        )
    conn.commit()
    conn.close()

    return JSONResponse({"results": results, "count": len(results), "query": q})