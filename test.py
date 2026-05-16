import csv
import time
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = "https://subslikescript.com"
START_URL = f"{BASE}/movies"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

session = requests.Session()
session.headers.update(HEADERS)


def get_soup(url):
    r = session.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_movie_links(list_page_soup):
    links = []
    for a in list_page_soup.select('.scripts-list a[href^="/movie/"]'):
        href = a.get("href")
        text = " ".join(a.get_text(" ", strip=True).split())
        if href:
            links.append((text, urljoin(BASE, href)))

    seen = set()
    clean = []
    for item in links:
        if item[1] not in seen:
            clean.append(item)
            seen.add(item[1])
    return clean


def find_next_page(list_page_soup):
    for a in list_page_soup.select("a[href]"):
        text = " ".join(a.get_text(" ", strip=True).split())
        if text == "›":
            return urljoin(BASE, a["href"])
    return None


def extract_description(soup):
    selectors = [".description", ".main-article p", "article p", ".mainpage p"]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            txt = " ".join(el.get_text(" ", strip=True).split())
            if txt:
                return txt

    meta = soup.select_one('meta[name="description"]')
    if meta and meta.get("content"):
        return meta["content"].strip()

    return ""


def extract_transcript(soup):
    selectors = [".full-script", ".script", ".transcript", ".main-article", "article"]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = el.get_text("\n", strip=True)
            if len(text) > 200:
                return text
    return ""


def extract_movie_data(movie_url, listing_title=""):
    soup = get_soup(movie_url)

    title = ""
    for sel in ["h1", "h2", ".title"]:
        el = soup.select_one(sel)
        if el:
            title = " ".join(el.get_text(" ", strip=True).split())
            if title:
                break

    if not title:
        title = listing_title

    return {
        "url": movie_url,
        "name": title,
        "description": extract_description(soup),
        "transcript": extract_transcript(soup),
    }


def scrape_listing_pages(max_pages=None):
    all_links = []
    seen_urls = set()

    page_url = START_URL
    page_count = 0

    while page_url:
        page_count += 1
        print(f"Listado {page_count}: {page_url}")
        soup = get_soup(page_url)

        movie_links = extract_movie_links(soup)
        for title, url in movie_links:
            if url not in seen_urls:
                all_links.append((title, url))
                seen_urls.add(url)

        page_url = find_next_page(soup)

        if max_pages is not None and page_count >= max_pages:
            break

    return all_links


def scrape_all_movies_parallel(max_pages=None, max_workers=6):
    links = scrape_listing_pages(max_pages=max_pages)
    print(f"Links únicos encontrados: {len(links)}")

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(extract_movie_data, url, title): (title, url)
            for title, url in links
        }

        for future in as_completed(future_map):
            title, url = future_map[future]
            try:
                row = future.result()
                results.append(row)
                print(f"OK: {row['name']}")
            except Exception as e:
                print(f"ERROR: {title} | {url} | {e}")

    return results


def save_to_sqlite(rows, db_name="movies_transcripts.db"):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            transcript TEXT,
            url TEXT UNIQUE
        )
    """)

    for row in rows:
        cur.execute("""
            INSERT OR REPLACE INTO movies (name, description, transcript, url)
            VALUES (?, ?, ?, ?)
        """, (
            row.get("name", ""),
            row.get("description", ""),
            row.get("transcript", ""),
            row.get("url", "")
        ))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    movies = scrape_all_movies_parallel(max_pages=2, max_workers=6)
    print(f"Total: {len(movies)}")
    save_to_sqlite(movies)
    print("Guardado en movies_transcripts.db")