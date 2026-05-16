from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import re

class ArticleLinkParser(HTMLParser):
	"""Extract <a> links inside a target <article class="..."> block."""

	def __init__(self, article_class: str, href_contains: Optional[str] = None) -> None:
		super().__init__(convert_charrefs=True)
		self.article_class = article_class
		self.href_contains = href_contains

		self._article_depth = 0
		self._inside_target_article = False

		self._inside_link = False
		self._current_href: Optional[str] = None
		self._current_title: Optional[str] = None
		self._current_text_parts: List[str] = []

		self.links: List[Dict[str, str]] = []

	@staticmethod
	def _class_contains(attrs: Dict[str, str], expected_class: str) -> bool:
		class_value = attrs.get("class", "")
		classes = class_value.split()
		return expected_class in classes

	def handle_starttag(self, tag: str, attrs_list: List[tuple[str, Optional[str]]]) -> None:
		attrs = {k: (v or "") for k, v in attrs_list}

		if tag == "article" and self._class_contains(attrs, self.article_class):
			self._inside_target_article = True
			self._article_depth = 1
			return

		if self._inside_target_article and tag == "article":
			self._article_depth += 1

		if not self._inside_target_article:
			return

		if tag == "a":
			href = attrs.get("href", "").strip()
			if not href:
				return
			if self.href_contains and self.href_contains not in href:
				return

			self._inside_link = True
			self._current_href = href
			self._current_title = attrs.get("title", "").strip()
			self._current_text_parts = []

	def handle_data(self, data: str) -> None:
		if self._inside_link:
			self._current_text_parts.append(data)

	def handle_endtag(self, tag: str) -> None:
		if self._inside_target_article and tag == "article":
			self._article_depth -= 1
			if self._article_depth <= 0:
				self._inside_target_article = False
				self._article_depth = 0

		if tag == "a" and self._inside_link:
			text = " ".join(part.strip() for part in self._current_text_parts if part.strip())
			self.links.append(
				{
					"href": self._current_href or "",
					"title": self._current_title or "",
					"text": text,
				}
			)
			self._inside_link = False
			self._current_href = None
			self._current_title = None
			self._current_text_parts = []


class MoviePageParser(HTMLParser):
	"""Extract title, plot and cue lines from a movie page article."""

	def __init__(self, article_class: str = "main-article") -> None:
		super().__init__(convert_charrefs=True)
		self.article_class = article_class

		self._inside_target_article = False
		self._article_depth = 0

		self._inside_h1 = False
		self._inside_plot = False
		self._inside_cue_line = False

		self._inside_full_script = False
		self._full_script_depth = 0

		self._title_parts: List[str] = []
		self._plot_parts: List[str] = []
		self._cue_parts: List[str] = []

		self.title = ""
		self.plot = ""
		self.cue_lines: List[str] = []

	@staticmethod
	def _class_contains(attrs: Dict[str, str], expected_class: str) -> bool:
		class_value = attrs.get("class", "")
		return expected_class in class_value.split()

	def handle_starttag(self, tag: str, attrs_list: List[tuple[str, Optional[str]]]) -> None:
		attrs = {k: (v or "") for k, v in attrs_list}

		if tag == "article" and self._class_contains(attrs, self.article_class):
			self._inside_target_article = True
			self._article_depth = 1
			return

		if not self._inside_target_article:
			return

		if tag == "article":
			self._article_depth += 1

		if tag == "h1":
			self._inside_h1 = True

		if tag == "p" and self._class_contains(attrs, "plot"):
			self._inside_plot = True

		if tag == "div" and self._class_contains(attrs, "full-script"):
			self._inside_full_script = True
			self._full_script_depth = 1
		elif self._inside_full_script and tag == "div":
			self._full_script_depth += 1

		if tag == "p" and self._inside_full_script and self._class_contains(attrs, "cue-line"):
			self._inside_cue_line = True
			self._cue_parts = []

	def handle_data(self, data: str) -> None:
		text = data.strip()
		if not text:
			return

		if self._inside_h1:
			self._title_parts.append(text)

		if self._inside_plot:
			self._plot_parts.append(text)

		if self._inside_cue_line:
			self._cue_parts.append(text)

	def handle_endtag(self, tag: str) -> None:
		if self._inside_target_article and tag == "article":
			self._article_depth -= 1
			if self._article_depth <= 0:
				self._inside_target_article = False
				self._article_depth = 0

		if tag == "h1":
			self._inside_h1 = False

		if tag == "p" and self._inside_plot:
			self._inside_plot = False

		if tag == "p" and self._inside_cue_line:
			line = " ".join(self._cue_parts).strip()
			if line:
				self.cue_lines.append(line)
			self._inside_cue_line = False
			self._cue_parts = []

		if tag == "div" and self._inside_full_script:
			self._full_script_depth -= 1
			if self._full_script_depth <= 0:
				self._inside_full_script = False
				self._full_script_depth = 0

	def finalize(self) -> None:
		self.title = " ".join(self._title_parts).strip()
		self.plot = " ".join(self._plot_parts).strip()

def fetch_html(url: str, timeout: int = 30) -> str:
	request = Request(
		url,
		headers={
			"User-Agent": (
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
				"AppleWebKit/537.36 (KHTML, like Gecko) "
				"Chrome/124.0.0.0 Safari/537.36"
			)
		},
	)
	with urlopen(request, timeout=timeout) as response:
		return response.read().decode("utf-8", errors="replace")

def extract_links_url(url: str) -> List[Dict[str, str]]:
	html = fetch_html(url)
	parser = ArticleLinkParser(article_class='main-article', href_contains='/movie/')
	parser.feed(html)

	unique: Dict[str, Dict[str, str]] = {}
	for item in parser.links:
		href = item["href"].strip()
		absolute = urljoin(url, href) if url else href
		if absolute not in unique:
			unique[absolute] = {
				"href": href,
				"url": absolute,
				"title": item.get("title", ""),
				"text": item.get("text", ""),
			}
	return list(unique.values())

def parse_movie_page(url: str) -> Dict[str, object]:
	html = fetch_html(url)
	parser = MoviePageParser(article_class="main-article")
	parser.feed(html)
	parser.finalize()

	return {
		"title": parser.title,
		"plot": parser.plot,
		"cue_lines": parser.cue_lines,
		"url": url,
	}

def safe_filename(name: str) -> str:
	clean = re.sub(r"[\\/:*?\"<>|]", "_", name).strip()
	clean = re.sub(r"\s+", " ", clean)
	return clean[:180] or "untitled_movie"

def write_transcript_file(movie: Dict[str, object], output_dir: Path) -> Path:
	title = str(movie.get("title", "untitled_movie")).strip() or "untitled_movie"
	filename = safe_filename(title) + ".txt"
	path = output_dir / filename

	lines = movie.get("cue_lines", [])
	content_lines = [str(line).strip() for line in lines if str(line).strip()]
	path.write_text("\n".join(content_lines), encoding="utf-8")
	return path

def append_metadata_file(movie: Dict[str, object], metadata_path: Path) -> None:
	title = str(movie.get("title", "")).strip()
	plot = str(movie.get("plot", "")).strip()
	url = str(movie.get("url", "")).strip()

	block = (
		f"Title: {title}\n"
		f"Description: {plot}\n"
		f"Link: {url}\n"
		"=" * 80
		+ "\n"
	)
	with metadata_path.open("a", encoding="utf-8") as f:
		f.write(block)

def load_links_from_json(path: Path) -> List[str]:
	if not path.exists():
		raise SystemExit(f"Links JSON file not found: {path}")

	data = json.loads(path.read_text(encoding="utf-8"))
	urls: List[str] = []

	if isinstance(data, list):
		for item in data:
			if isinstance(item, str):
				urls.append(item.strip())
			elif isinstance(item, dict):
				url = str(item.get("url", "")).strip()
				if url:
					urls.append(url)

	unique_urls: List[str] = []
	seen = set()
	for url in urls:
		if url and url not in seen:
			seen.add(url)
			unique_urls.append(url)

	return unique_urls

def collect_links_from_pages(url: str, start_page: int, end_page: int) -> List[str]:
	all_links: List[str] = []
	seen = set()

	for page in range(start_page, end_page + 1):
		print(f"Processing list page {page}...")
		url = f"{url}?page={page}"
		try:
			links = extract_links_url(url)
		except Exception as exc:
			print(f"Failed page {page}: {exc}")
			continue

		for item in links:
			movie_url = str(item.get("url", "")).strip()
			if movie_url and movie_url not in seen:
				seen.add(movie_url)
				all_links.append(movie_url)

	return all_links

	args = parse_args()

	movies_dir = Path(args.movies_dir)
	movies_dir.mkdir(parents=True, exist_ok=True)

	metadata_path = Path(args.metadata_file)
	metadata_path.parent.mkdir(parents=True, exist_ok=True)
	metadata_path.write_text("", encoding="utf-8")

	if args.collect_links:
		print("Collecting movie links...")
		movie_urls = collect_links_from_pages(args.start_page, args.end_page)
		links_json_path = Path(args.links_json)
		links_json_path.parent.mkdir(parents=True, exist_ok=True)
		links_json_path.write_text(json.dumps(movie_urls, indent=2, ensure_ascii=False), encoding="utf-8")
		print(f"Saved {len(movie_urls)} movie links to {links_json_path}")
	else:
		movie_urls = load_links_from_json(Path(args.links_json))

	print(f"Scraping {len(movie_urls)} movie pages...")
	for idx, movie_url in enumerate(movie_urls, start=1):
		print(f"[{idx}/{len(movie_urls)}] {movie_url}")
		try:
			movie = parse_movie_page(movie_url)
		except Exception as exc:
			print(f"Failed: {movie_url} -> {exc}")
			continue

		transcript_path = write_transcript_file(movie, movies_dir)
		append_metadata_file(movie, metadata_path)
		print(f"Saved transcript: {transcript_path.name}")

	print(f"Done. Metadata file: {metadata_path}")