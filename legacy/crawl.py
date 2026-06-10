#!/usr/bin/env python3
"""Minimal storefront crawler for collecting Qosmic audit artifacts.

Reads a single storefront URL argument and writes crawl artifacts under
artifacts/crawl/. This script intentionally does not generate an audit report.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "artifacts" / "crawl"
MAX_PAGES = 18
TIMEOUT = 20
USER_AGENT = "QosmicAuditCrawler/0.1 (+storefront artifact collection)"
USAGE = "usage: python3 crawl.py <storefront_url>"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self.buttons: list[str] = []
        self.meta: dict[str, str] = {}
        self.structured_data: list[str] = []
        self.favicons: list[str] = []
        self._tag_stack: list[str] = []
        self._capture_json_ld = False
        self._json_ld_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): v or "" for k, v in attrs}
        self._tag_stack.append(tag)

        if tag == "a" and attrs_dict.get("href"):
            self.links.append(attrs_dict["href"])
        elif tag == "meta":
            key = attrs_dict.get("name") or attrs_dict.get("property")
            if key and attrs_dict.get("content"):
                self.meta[key.lower()] = attrs_dict["content"].strip()
        elif tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            if "icon" in rel and attrs_dict.get("href"):
                self.favicons.append(attrs_dict["href"])
        elif tag == "script" and attrs_dict.get("type", "").lower() == "application/ld+json":
            self._capture_json_ld = True
            self._json_ld_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._capture_json_ld:
            data = "".join(self._json_ld_parts).strip()
            if data:
                self.structured_data.append(data[:5000])
            self._capture_json_ld = False
            self._json_ld_parts = []
        if self._tag_stack:
            self._tag_stack.pop()

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        if self._capture_json_ld:
            self._json_ld_parts.append(data)
            return
        current = self._tag_stack[-1] if self._tag_stack else ""
        if current == "title":
            self.title_parts.append(text)
        elif current in {"button"}:
            self.buttons.append(text)
            self.text_parts.append(text)
        elif current not in {"script", "style", "noscript"}:
            self.text_parts.append(text)


def slug_for(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    stem = (parsed.netloc + parsed.path).strip("/").replace("/", "-") or "home"
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", stem).strip("-").lower()[:80]
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{stem}-{digest}"


def normalize_url(base: str, href: str) -> str | None:
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return None
    joined = urllib.parse.urljoin(base, html.unescape(href))
    parsed = urllib.parse.urlparse(joined)
    if parsed.scheme not in {"http", "https"}:
        return None
    clean = parsed._replace(fragment="", query="" if parsed.path != "/search" else parsed.query)
    return urllib.parse.urlunparse(clean)


def same_host(url: str, host: str) -> bool:
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.") == host


def fetch(url: str, method: str = "GET") -> dict:
    req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read()
            return {
                "url": url,
                "final_url": resp.geturl(),
                "status": resp.status,
                "ok": 200 <= resp.status < 400,
                "content_type": resp.headers.get("content-type", ""),
                "elapsed_ms": round((time.time() - started) * 1000),
                "body": body,
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return {
            "url": url,
            "final_url": exc.geturl(),
            "status": exc.code,
            "ok": False,
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "elapsed_ms": round((time.time() - started) * 1000),
            "body": body,
            "error": str(exc),
        }
    except (urllib.error.URLError, TimeoutError, ssl.SSLError) as exc:
        return {
            "url": url,
            "final_url": url,
            "status": None,
            "ok": False,
            "content_type": "",
            "elapsed_ms": round((time.time() - started) * 1000),
            "body": b"",
            "error": str(exc),
        }


def parse_page(url: str, fetched: dict, host: str) -> dict:
    raw = fetched["body"]
    text = raw.decode("utf-8", errors="replace")
    parser = PageParser()
    if "html" in fetched.get("content_type", "") or text.lstrip().startswith("<"):
        parser.feed(text)

    internal_links = []
    external_links = []
    for href in parser.links:
        normalized = normalize_url(fetched["final_url"] or url, href)
        if not normalized:
            continue
        if same_host(normalized, host):
            internal_links.append(normalized)
        else:
            external_links.append(normalized)

    visible_text = "\n".join(parser.text_parts)
    return {
        "url": url,
        "final_url": fetched["final_url"],
        "status": fetched["status"],
        "ok": fetched["ok"],
        "content_type": fetched["content_type"],
        "elapsed_ms": fetched["elapsed_ms"],
        "error": fetched["error"],
        "title": " ".join(parser.title_parts).strip(),
        "meta_description": parser.meta.get("description", ""),
        "meta": parser.meta,
        "visible_text": visible_text[:30000],
        "html_path": "",
        "text_path": "",
        "screenshot_path": None,
        "internal_links": sorted(set(internal_links)),
        "external_links": sorted(set(external_links)),
        "button_cta_text": sorted(set(parser.buttons)),
        "structured_data_count": len(parser.structured_data),
        "structured_data_samples": parser.structured_data[:3],
        "favicon_links": parser.favicons,
        "product_signals": product_signals(url, visible_text, parser.structured_data),
    }


def product_signals(url: str, visible_text: str, structured_data: list[str]) -> dict:
    lower = (url + "\n" + visible_text[:5000] + "\n".join(structured_data)).lower()
    return {
        "looks_like_product": "/products/" in url or '"@type":"product"' in lower or '"@type": "product"' in lower,
        "mentions_price": bool(re.search(r"\$\s?\d|\bprice\b", lower)),
        "mentions_add_to_cart": "add to cart" in lower or "add-to-cart" in lower,
        "mentions_subscribe": "subscribe" in lower or "subscription" in lower,
        "mentions_reviews": "review" in lower or "stars" in lower,
    }


def classify_link(url: str) -> str:
    path = urllib.parse.urlparse(url).path.lower()
    if path in {"", "/"}:
        return "homepage"
    if "/products/" in path:
        return "product"
    if "/collections/" in path or "/categories/" in path:
        return "collection"
    if path in {"/cart", "/cart/"}:
        return "cart"
    if any(word in path for word in ["faq", "shipping", "return", "contact", "where-to-buy", "store-locator", "blog", "recipe", "guide"]):
        return "content"
    return "other"


def priority(url: str) -> int:
    order = {"homepage": 0, "product": 1, "collection": 2, "cart": 3, "content": 4, "other": 9}
    return order[classify_link(url)]


def write_page_artifacts(page: dict, html_bytes: bytes) -> None:
    slug = slug_for(page["final_url"] or page["url"])
    html_path = OUT / "html" / f"{slug}.html"
    text_path = OUT / "text" / f"{slug}.txt"
    html_path.write_bytes(html_bytes)
    text_path.write_text(page["visible_text"], encoding="utf-8")
    page["html_path"] = str(html_path.relative_to(ROOT))
    page["text_path"] = str(text_path.relative_to(ROOT))


def candidate_seed_urls(base_url: str) -> list[str]:
    parsed = urllib.parse.urlparse(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return [
        base_url,
        urllib.parse.urljoin(origin, "/products.json"),
        urllib.parse.urljoin(origin, "/collections.json"),
        urllib.parse.urljoin(origin, "/cart"),
        urllib.parse.urljoin(origin, "/robots.txt"),
        urllib.parse.urljoin(origin, "/sitemap.xml"),
        urllib.parse.urljoin(origin, "/sitemap_index.xml"),
    ]


def discover_from_shopify_json(url: str, data: bytes) -> list[str]:
    discovered: list[str] = []
    try:
        payload = json.loads(data.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return discovered
    origin = f"{urllib.parse.urlparse(url).scheme}://{urllib.parse.urlparse(url).netloc}"
    for product in payload.get("products", [])[:8]:
        handle = product.get("handle")
        if handle:
            discovered.append(f"{origin}/products/{handle}")
    for collection in payload.get("collections", [])[:6]:
        handle = collection.get("handle")
        if handle:
            discovered.append(f"{origin}/collections/{handle}")
    return discovered


def technical_checks(base_url: str, pages: list[dict], endpoint_results: dict[str, dict]) -> list[dict]:
    parsed = urllib.parse.urlparse(base_url)
    https_url = urllib.parse.urlunparse(("https", parsed.netloc, parsed.path or "/", "", "", ""))
    page_by_kind = {classify_link(page["url"]): page for page in pages if page.get("ok")}

    def status(name: str, ok: bool, detail: str, warn: bool = False) -> dict:
        return {"check": name, "status": "Warn" if warn else ("Pass" if ok else "Fail"), "detail": detail}

    robots = endpoint_results.get("/robots.txt")
    sitemap = endpoint_results.get("/sitemap.xml") or endpoint_results.get("/sitemap_index.xml")
    homepage = next((p for p in pages if classify_link(p["url"]) == "homepage"), None)
    product = page_by_kind.get("product")
    cart = next((p for p in pages if classify_link(p["url"]) == "cart"), None)
    has_meta = any(p.get("title") and p.get("meta_description") for p in pages)
    has_structured_data = any(p.get("structured_data_count", 0) for p in pages)
    has_favicon = any(p.get("favicon_links") for p in pages)

    checks = [
        status("SSL", parsed.scheme == "https", f"Input URL scheme is {parsed.scheme}."),
        status("HTTPS redirect", bool(homepage and str(homepage.get("final_url", "")).startswith("https://")), f"Homepage final URL: {(homepage or {}).get('final_url', 'not loaded')}", warn=not homepage or not homepage.get("ok")),
        status("Sitemap", bool(sitemap and sitemap.get("ok")), f"Status: {(sitemap or {}).get('status', 'not checked')}", warn=bool(sitemap and not sitemap.get("ok"))),
        status("Robots.txt", bool(robots and robots.get("ok")), f"Status: {(robots or {}).get('status', 'not checked')}"),
        status("Critical pages loading", bool(homepage and homepage.get("ok") and product), "Homepage and at least one product page loaded." if homepage and homepage.get("ok") and product else "Missing homepage or product page artifact.", warn=True),
        status("Meta tags", has_meta, "At least one crawled page has both title and meta description." if has_meta else "No crawled page exposed both title and meta description.", warn=True),
        status("Structured data", has_structured_data, "JSON-LD found on at least one crawled page." if has_structured_data else "No JSON-LD found in crawled artifacts.", warn=True),
        status("Favicon", has_favicon, "Favicon link found on at least one crawled page." if has_favicon else "No favicon link found in crawled artifacts.", warn=True),
        status("Checkout reachable", bool(cart and cart.get("ok")), f"Cart status: {(cart or {}).get('status', 'not checked')}", warn=bool(cart and not cart.get("ok"))),
    ]
    checks.append(status("Input preserved", https_url.startswith("https://"), f"Canonical HTTPS candidate: {https_url}", warn=True))
    return checks


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print(USAGE, file=sys.stderr)
        print("error: storefront URL is required", file=sys.stderr)
        return 1

    start_url = args[0].strip()
    if not start_url:
        print(USAGE, file=sys.stderr)
        print("error: storefront URL is empty", file=sys.stderr)
        return 1
    if not urllib.parse.urlparse(start_url).scheme:
        start_url = "https://" + start_url

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "html").mkdir(exist_ok=True)
    (OUT / "text").mkdir(exist_ok=True)
    (OUT / "raw").mkdir(exist_ok=True)

    host = urllib.parse.urlparse(start_url).netloc.lower().removeprefix("www.")
    queue = candidate_seed_urls(start_url)
    seen: set[str] = set()
    pages: list[dict] = []
    endpoint_results: dict[str, dict] = {}

    while queue and len(pages) < MAX_PAGES:
        url = queue.pop(0)
        normalized = normalize_url(start_url, url)
        if not normalized or normalized in seen or not same_host(normalized, host):
            continue
        seen.add(normalized)

        fetched = fetch(normalized)
        path = urllib.parse.urlparse(normalized).path or "/"
        if path in {"/robots.txt", "/sitemap.xml", "/sitemap_index.xml"}:
            endpoint_results[path] = {k: v for k, v in fetched.items() if k != "body"}

        raw_path = OUT / "raw" / f"{slug_for(normalized)}.bin"
        raw_path.write_bytes(fetched["body"])

        if normalized.endswith(".json"):
            queue.extend(discover_from_shopify_json(normalized, fetched["body"]))
            continue

        page = parse_page(normalized, fetched, host)
        page["raw_path"] = str(raw_path.relative_to(ROOT))
        write_page_artifacts(page, fetched["body"])
        pages.append(page)

        useful_links = [link for link in page["internal_links"] if classify_link(link) != "other"]
        queue.extend(sorted(useful_links, key=priority)[:12])
        queue = sorted(dict.fromkeys(queue), key=priority)

    manifest = {
        "input_url": start_url,
        "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "page_count": len(pages),
        "max_pages": MAX_PAGES,
        "pages": pages,
        "technical_checks": technical_checks(start_url, pages, endpoint_results),
        "limits": [
            "No audit report generated by crawl.py.",
            "Screenshots are not captured by this minimal crawler.",
            "Artifacts are limited to pages/endpoints reachable from this runtime.",
        ],
    }

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(pages)} page artifacts to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
