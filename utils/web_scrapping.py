import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
	"User-Agent": (
		"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
		"AppleWebKit/537.36 (KHTML, like Gecko) "
		"Chrome/124.0.0.0 Safari/537.36"
	)
}

session = requests.Session()
session.headers.update(HEADERS)

class DatabaseManager:
	def __init__(self, db_name):
		self.db_name = db_name
		self.conn = sqlite3.connect(self.db_name)
		self.cur = self.conn.cursor()

	def close(self):
		if self.conn:
			self.conn.commit()
			self.conn.close()

	def create_tables(self):
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS movies (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				name TEXT,
				description TEXT,
				url TEXT UNIQUE
			)
		""")
		self.cur.execute("""
			CREATE TABLE IF NOT EXISTS movies_transcript (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				movie_id INTEGER,
				transcript TEXT,
				FOREIGN KEY(movie_id) REFERENCES movies(id)
			)
		""")
		self.conn.commit()

	def insert_movie(self, name, description, url, transcript):
		self.cur.execute("""
			INSERT OR IGNORE INTO movies (name, description, url) VALUES (?, ?, ?)
		""", (name, description, url))
		movie_id = self.cur.lastrowid
		if movie_id:
			self.cur.execute("""
				INSERT INTO movies_transcript (movie_id, transcript) VALUES (?, ?)
			""", (movie_id, transcript))
		self.conn.commit()

	def movie_exists(self, url):
		self.cur.execute("SELECT id FROM movies WHERE url = ?", (url,))
		return self.cur.fetchone() is not None

def get_soup(url):
	r = session.get(url, timeout=30)
	r.raise_for_status()
	return BeautifulSoup(r.text, "html.parser")

def extract_movie_links(base_url, list_page_soup):
	links = []
	for a in list_page_soup.select('.scripts-list a[href^="/movie/"]'):
		href = a.get("href")
		text = " ".join(a.get_text(" ", strip=True).split())
		if href:
			links.append((text, urljoin(base_url, href)))

	seen = set()
	clean = []
	for item in links:
		if item[1] not in seen:
			clean.append(item)
			seen.add(item[1])
	return clean

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

def scrape_listing_pages(config=None):
	all_links = []
	seen_urls = set()

	page_url = config.get('url_to_scrap')
	start_page = config.get('start_page', 1)
	end_page = config.get('end_page', None)
	for page_num in range(start_page, end_page + 1):
		print(f"Listado {page_num}: {page_url}")
		soup = get_soup(f'{page_url}?page={page_num}')
		movie_links = extract_movie_links(page_url, soup)
		for title, url in movie_links:
			if url not in seen_urls:
				all_links.append((title, url))
				seen_urls.add(url)
	return all_links

def scrape_all_movies_parallel(config, max_workers=6):
	links = scrape_listing_pages(config)
	print(f"Links únicos encontrados: {len(links)}")
	database = DatabaseManager(config.get('database_name', 'movies.db'))
	database.create_tables()
	filtered_links = [
		(title, url)
		for title, url in links
		if not database.movie_exists(url)
	]
	with ThreadPoolExecutor(max_workers=max_workers) as executor:
		future_map = { executor.submit(extract_movie_data, url, title): (title, url) for title, url in filtered_links }
		for future in as_completed(future_map):
			title, url = future_map[future]
			try:
				row = future.result()
				database.insert_movie(row['name'].replace(' - full transcript', ' '), row['description'], row['url'], row['transcript'])
				print(f"OK: {row['name']}")
			except Exception as e:
				print(f"ERROR: {title} | {url} | {e}")
