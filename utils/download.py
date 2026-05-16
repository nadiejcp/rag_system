import os
import kagglehub
from pathlib import Path
from .web_scrapping import collect_links_from_pages, load_links_from_json, parse_movie_page, write_transcript_file, append_metadata_file
import json

def download_dataset(config):
  BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  DATA_DIR = os.path.join(BASE_DIR, config.get('path_to_raw'))
  os.makedirs(DATA_DIR, exist_ok=True)
  if os.path.exists(DATA_DIR):
    print("Dataset already exists at:", DATA_DIR)
    return
  kagglehub.dataset_download(config.get('path_to_download'), DATA_DIR)

def download_movies_from_page(config):
	movies_dir = Path(config.get('path_to_save'))
	movies_dir.mkdir(parents=True, exist_ok=True)

	metadata_path = movies_dir / "metadata.txt"
	links_json_path = movies_dir / "movie_links.json"

	# Initialize metadata file if not present
	if not metadata_path.exists():
		metadata_path.write_text("", encoding="utf-8")

	# Collect or load links
	if links_json_path.exists():
		print(f"Loading existing links from {links_json_path}")
		movie_urls = load_links_from_json(links_json_path)
	else:
		print("Collecting movie links...")
		start_page = int(config.get('start_page', 1))
		end_page = int(config.get('end_page', 20))
		movie_urls = collect_links_from_pages(config.get('url_to_scrap'), start_page, end_page)
		links_json_path.write_text(json.dumps(movie_urls, indent=2, ensure_ascii=False), encoding="utf-8")
		print(f"Saved {len(movie_urls)} links to {links_json_path}")

	print(f"Found {len(movie_urls)} movie links.")

	# Scrape each movie page and save transcript + metadata
	for idx, movie_url in enumerate(movie_urls, start=1):
		try:
			print(f"[{idx}/{len(movie_urls)}] Scraping: {movie_url}")
			movie = parse_movie_page(movie_url)
		except Exception as exc:
			print(f"Failed to parse {movie_url}: {exc}")
			continue

		# Skip if title missing
		title = str(movie.get('title', '')).strip()
		if not title:
			print(f"Skipping {movie_url} (no title found)")
			continue

		# Write transcript and append metadata
		try:
			transcript_path = write_transcript_file(movie, movies_dir)
			append_metadata_file(movie, metadata_path)
			print(f"Saved transcript: {transcript_path.name}")
		except Exception as exc:
			print(f"Failed to save data for {movie_url}: {exc}")
			continue