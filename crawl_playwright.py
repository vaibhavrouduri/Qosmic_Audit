#!/usr/bin/env python3
"""Playwright storefront crawler for Qosmic audit artifact collection.

This script collects artifacts only. It does not generate CRO findings,
experiments, competitor analysis, or an audit report.
"""

from __future__ import annotations

import argparse
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
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
ARTIFACT_ROOT = ROOT / "artifacts"
MAX_RENDERED_PAGES = 18
TIMEOUT_MS = 25_000
USER_AGENT = "QosmicAuditCrawler/0.2 (+Playwright storefront artifact collection)"
USAGE = "usage: python3 crawl_playwright.py [--headful] [--no-mobile] <storefront_url>"
DESKTOP_VIEWPORT = {"width": 1440, "height": 1200}
MOBILE_VIEWPORT = {"width": 390, "height": 844}
TECHNICAL_PATHS = [
    "/robots.txt",
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/products.json",
    "/collections.json",
]


@dataclass(frozen=True)
class CrawlOptions:
    start_url: str
    headful: bool
    no_mobile: bool


def read_start_url(argv: list[str]) -> CrawlOptions:
    parser = argparse.ArgumentParser(
        description="Collect Shopify storefront crawl artifacts.",
        usage="python3 crawl_playwright.py [--headful] [--no-mobile] <storefront_url>",
    )
    parser.add_argument("url", nargs="?", metavar="storefront_url", help="Storefront URL, for example https://example-store.com")
    parser.add_argument("--headful", action="store_true", help="Run Chromium in a visible browser window for debugging.")
    parser.add_argument("--no-mobile", action="store_true", help="Skip mobile screenshots for faster debugging crawls.")
    args = parser.parse_args(argv)
    if args.url:
        return CrawlOptions(start_url=args.url.strip(), headful=args.headful, no_mobile=args.no_mobile)
    raise ValueError(f"{USAGE}\nerror: storefront URL is required")


def normalize_start_url(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Storefront URL is empty.")
    if not urllib.parse.urlparse(value).scheme:
        value = "https://" + value
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid storefront URL: {value}")
    clean = parsed._replace(path=parsed.path or "/", params="", query="", fragment="")
    return urllib.parse.urlunparse(clean)


def origin_for(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def host_key(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")


def same_host(url: str, host: str) -> bool:
    return host_key(url) == host


def normalize_link(base: str, href: str | None) -> str | None:
    if not href:
        return None
    href = html.unescape(href).strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "sms:")):
        return None
    joined = urllib.parse.urljoin(base, href)
    parsed = urllib.parse.urlparse(joined)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    keep_query = parsed.query if parsed.path.rstrip("/") == "/search" else ""
    clean = parsed._replace(params="", query=keep_query, fragment="")
    return urllib.parse.urlunparse(clean)


def classify_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path.lower().rstrip("/")
    if path in {"", "/"}:
        return "homepage"
    if path == "/cart":
        return "cart"
    if "/products/" in path:
        return "product"
    if "/collections/" in path or "/categories/" in path:
        return "collection"
    if any(token in path for token in ("faq", "help", "support")):
        return "faq"
    if "shipping" in path:
        return "shipping"
    if "return" in path or "refund" in path:
        return "returns"
    if "contact" in path:
        return "contact"
    if any(token in path for token in ("where-to-buy", "store-locator", "store-locations", "find-us", "locator")):
        return "store_locator"
    if any(token in path for token in ("blog", "recipe", "guide", "learn", "article", "pages/")):
        return "content"
    return "other"


def priority(url: str) -> int:
    order = {
        "homepage": 0,
        "product": 1,
        "collection": 2,
        "cart": 3,
        "faq": 4,
        "shipping": 4,
        "returns": 4,
        "contact": 4,
        "store_locator": 4,
        "content": 5,
        "other": 9,
    }
    return order.get(classify_url(url), 9)


def slug_for(url: str, suffix: str = "") -> str:
    parsed = urllib.parse.urlparse(url)
    stem = (parsed.netloc + parsed.path).strip("/").replace("/", "-") or "home"
    if suffix:
        stem = f"{stem}-{suffix}"
    stem = re.sub(r"[^a-zA-Z0-9._-]+", "-", stem).strip("-").lower()[:90]
    digest = hashlib.sha1(f"{url}:{suffix}".encode("utf-8")).hexdigest()[:8]
    return f"{stem}-{digest}"


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def make_run_folder(normalized_url: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    host = re.sub(r"[^a-zA-Z0-9._-]+", "-", host_key(normalized_url)).strip("-") or "store"
    run = ARTIFACT_ROOT / f"{host}-{timestamp}"
    for child in ("screenshots", "html", "text", "raw"):
        (run / child).mkdir(parents=True, exist_ok=True)
    return run


def fetch_endpoint(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
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
    except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError) as exc:
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


def save_endpoint_artifact(run: Path, result: dict[str, Any]) -> dict[str, Any]:
    path = urllib.parse.urlparse(result["url"]).path.strip("/").replace("/", "-") or "home"
    raw_path = run / "raw" / f"{slug_for(result['url'], path)}.bin"
    raw_path.write_bytes(result.get("body", b""))
    body_preview = result.get("body", b"")[:120_000].decode("utf-8", errors="replace")
    text_path = run / "text" / f"{slug_for(result['url'], path)}.txt"
    text_path.write_text(body_preview, encoding="utf-8")
    return {
        "url": result["url"],
        "final_url": result["final_url"],
        "status": result["status"],
        "ok": result["ok"],
        "content_type": result["content_type"],
        "elapsed_ms": result["elapsed_ms"],
        "raw_path": relative(raw_path),
        "text_path": relative(text_path),
        "error": result["error"],
    }


def discover_from_json(url: str, body: bytes) -> list[str]:
    discovered: list[str] = []
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return discovered
    origin = origin_for(url)
    for product in payload.get("products", [])[:10]:
        handle = product.get("handle")
        if handle:
            discovered.append(f"{origin}/products/{handle}")
    for collection in payload.get("collections", [])[:8]:
        handle = collection.get("handle")
        if handle:
            discovered.append(f"{origin}/collections/{handle}")
    return discovered


def discover_from_sitemap(body: bytes, base_url: str, host: str) -> list[str]:
    text = body.decode("utf-8", errors="replace")
    urls = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text, flags=re.IGNORECASE)
    normalized: list[str] = []
    for url in urls[:300]:
        clean = normalize_link(base_url, url)
        if clean and same_host(clean, host) and priority(clean) < 9:
            normalized.append(clean)
    return normalized


def dedupe_sorted(urls: list[str]) -> list[str]:
    return sorted(dict.fromkeys(urls), key=lambda item: (priority(item), item))


def extract_signals(url: str, text: str, details: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    lower = (url + "\n" + text[:60_000] + "\n" + json.dumps(details, ensure_ascii=False)[:20_000]).lower()
    product = {
        "looks_like_product": "/products/" in urllib.parse.urlparse(url).path.lower() or details.get("json_ld_product", False),
        "product_title_present": bool(details.get("h1_text")),
        "price_visible": bool(re.search(r"(\$\s?\d|\bprice\b|sale price|regular price)", lower)),
        "compare_at_or_discount_visible": bool(re.search(r"(compare at|was \$|save \d|% off|sale)", lower)),
        "add_to_cart_visible": "add to cart" in lower or "add-to-cart" in lower,
        "buy_button_visible": bool(re.search(r"\b(buy now|shop pay|checkout)\b", lower)),
        "subscription_option_visible": "subscribe" in lower or "subscription" in lower,
        "variant_selector_visible": any(token in lower for token in ("variant", "size", "color", "flavor", "select option")),
        "reviews_or_ratings_visible": any(token in lower for token in ("review", "rating", "stars", "★★★★★")),
        "shipping_or_returns_visible": "shipping" in lower or "returns" in lower,
        "stock_or_availability_visible": any(token in lower for token in ("in stock", "sold out", "available", "unavailable")),
        "retailer_handoff_visible": any(token in lower for token in ("where to buy", "find a store", "store locator")),
        "quantity_selector_visible": "quantity" in lower or details.get("quantity_inputs", 0) > 0,
        "bundle_or_upsell_visible": any(token in lower for token in ("bundle", "frequently bought", "you may also like", "related products")),
        "trust_badges_or_guarantees_visible": any(token in lower for token in ("guarantee", "secure checkout", "money back", "free returns")),
    }
    collection = {
        "looks_like_collection": any(token in urllib.parse.urlparse(url).path.lower() for token in ("/collections/", "/categories/")),
        "product_grid_visible": details.get("product_card_count", 0) >= 2,
        "filters_visible": any(token in lower for token in ("filter", "facets", "refine by")),
        "sorting_visible": "sort by" in lower or "sort" in details.get("select_text", "").lower(),
        "category_copy_visible": len(details.get("h1_text", "")) > 0 and len(text) > 500,
        "product_cards_visible": details.get("product_card_count", 0) >= 2,
        "price_visibility": bool(re.search(r"\$\s?\d", lower)),
        "review_visibility": any(token in lower for token in ("review", "rating", "stars", "★★★★★")),
        "quick_add_visible": any(token in lower for token in ("quick add", "quick shop", "add to cart")),
        "need_or_use_case_navigation_visible": any(token in lower for token in ("shop by", "concern", "goal", "use case", "occasion")),
        "empty_or_broken_state": any(token in lower for token in ("no products found", "collection is empty", "404", "page not found")),
    }
    content = {
        "looks_like_content_page": classify_url(url) in {"faq", "shipping", "returns", "contact", "store_locator", "content"},
        "answers_high_intent_question": any(token in lower for token in ("shipping", "returns", "faq", "ingredients", "how to", "where to buy", "contact")),
        "products_linked": "/products/" in lower,
        "calls_to_action_visible": len(details.get("button_texts", [])) > 0,
        "buying_or_locator_path_visible": any(token in lower for token in ("shop now", "add to cart", "where to buy", "find a store", "store locator")),
        "appears_stale_empty_broken_or_thin": len(text.strip()) < 500 or any(token in lower for token in ("404", "page not found", "coming soon")),
    }
    return product, collection, content


def has_cloudflare_challenge_script(rendered_html: str) -> bool:
    return "/cdn-cgi/challenge-platform" in rendered_html


def detect_blocked_page(status: int | None, title: str, visible_text: str) -> list[str]:
    reasons: list[str] = []
    normalized_title = title.strip().lower()
    normalized_text = re.sub(r"\s+", " ", visible_text).strip()
    visible_word_count = len(re.findall(r"\w+", normalized_text))
    if status == 403:
        reasons.append("HTTP status is 403.")
    if "403 forbidden" in normalized_title:
        reasons.append("Page title contains 403 Forbidden.")
    if "You don't have permission" in visible_text:
        reasons.append("Visible text contains You don't have permission.")
    if "Forbidden" in visible_text and visible_word_count <= 80:
        reasons.append("Visible text contains Forbidden with very low page content.")
    return reasons


def page_extract_script() -> str:
    return r"""
() => {
  const textOf = (el) => (el && el.innerText ? el.innerText.trim().replace(/\s+/g, " ") : "");
  const attr = (el, name) => el ? el.getAttribute(name) : "";
  const anchors = Array.from(document.querySelectorAll("a[href]")).map((a) => ({
    href: a.href || a.getAttribute("href") || "",
    text: textOf(a),
  }));
  const buttons = Array.from(document.querySelectorAll("button, [role='button'], input[type='submit'], input[type='button'], a[class*='button' i], a[class*='btn' i]"))
    .map((el) => textOf(el) || attr(el, "value") || attr(el, "aria-label") || attr(el, "title"))
    .filter(Boolean);
  const forms = Array.from(document.querySelectorAll("form")).map((form, index) => ({
    index,
    action: form.action || attr(form, "action"),
    method: (attr(form, "method") || "get").toLowerCase(),
    labels: Array.from(form.querySelectorAll("label")).map(textOf).filter(Boolean).slice(0, 12),
    inputs: Array.from(form.querySelectorAll("input, select, textarea, button")).map((el) => ({
      tag: el.tagName.toLowerCase(),
      type: attr(el, "type"),
      name: attr(el, "name"),
      placeholder: attr(el, "placeholder"),
      text: textOf(el) || attr(el, "value") || attr(el, "aria-label"),
    })).slice(0, 30),
  }));
  const jsonLd = Array.from(document.querySelectorAll("script[type='application/ld+json']")).map((el) => el.textContent || "");
  const productCardCount = document.querySelectorAll("[href*='/products/'], [class*='product-card' i], [class*='grid__item' i]").length;
  const images = Array.from(document.images);
  return {
    title: document.title || "",
    meta_description: attr(document.querySelector("meta[name='description']"), "content"),
    canonical_url: attr(document.querySelector("link[rel='canonical']"), "href"),
    h1_text: Array.from(document.querySelectorAll("h1")).map(textOf).filter(Boolean).join(" | "),
    select_text: Array.from(document.querySelectorAll("select")).map(textOf).filter(Boolean).join(" | "),
    links: anchors,
    button_texts: Array.from(new Set(buttons)).slice(0, 80),
    forms,
    structured_data_count: jsonLd.filter(Boolean).length,
    structured_data_types: jsonLd.join("\n").match(/"@type"\s*:\s*"[^"]+"/gi)?.slice(0, 30) || [],
    json_ld_product: /"@type"\s*:\s*"Product"/i.test(jsonLd.join("\n")),
    favicon_links: Array.from(document.querySelectorAll("link[rel*='icon' i]")).map((el) => el.href || attr(el, "href")).filter(Boolean),
    product_card_count: productCardCount,
    quantity_inputs: document.querySelectorAll("input[name*='quantity' i], input[id*='quantity' i]").length,
    image_count: images.length,
    images_missing_alt_count: images.filter((img) => !img.getAttribute("alt")).length,
    privacy_or_cookie_links: anchors.filter((a) => /privacy|cookie/i.test(a.text + " " + a.href)).map((a) => a.href).slice(0, 20),
    performance_timing: (() => {
      const nav = performance.getEntriesByType("navigation")[0];
      if (!nav) return {};
      return {
        dom_content_loaded_ms: Math.round(nav.domContentLoadedEventEnd),
        load_event_ms: Math.round(nav.loadEventEnd),
        response_end_ms: Math.round(nav.responseEnd),
      };
    })(),
  };
}
"""


def capture_rendered_page(browser: Any, run: Path, url: str, host: str, *, capture_mobile: bool) -> dict[str, Any]:
    base_slug = slug_for(url)
    page_entry: dict[str, Any] = {
        "surface_type": classify_url(url),
        "url": url,
        "final_url": url,
        "status": None,
        "blocked": False,
        "blocked_reasons": [],
        "cloudflare_detected": False,
        "artifact_label": "storefront_evidence",
        "title": "",
        "meta_description": "",
        "screenshot_paths": {"desktop": None, "mobile": None},
        "html_path": None,
        "text_path": None,
        "raw_path": None,
        "internal_links": [],
        "external_links": [],
        "cta_button_text": [],
        "forms_detected": [],
        "product_signals": {},
        "collection_signals": {},
        "content_signals": {},
        "structured_data_count": 0,
        "favicon_links": [],
        "privacy_or_cookie_links": [],
        "image_count": 0,
        "images_missing_alt_count": 0,
        "load_timing_ms": {},
        "errors_or_blocking_details": [],
    }

    context = browser.new_context(
        viewport=DESKTOP_VIEWPORT,
        ignore_https_errors=True,
        locale="en-US",
        timezone_id="America/New_York",
    )
    page = context.new_page()
    started = time.time()
    details: dict[str, Any] = {}
    rendered_html = ""
    visible_text = ""

    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
        try:
            page.wait_for_load_state("networkidle", timeout=6_000)
        except Exception as exc:  # noqa: BLE001 - capture limitation, continue with available DOM.
            page_entry["errors_or_blocking_details"].append(f"Network idle wait skipped: {exc}")
        page_entry["final_url"] = page.url
        page_entry["status"] = response.status if response else None
        page_entry["elapsed_ms"] = round((time.time() - started) * 1000)
        details = page.evaluate(page_extract_script())
        rendered_html = page.content()
        visible_text = page.locator("body").inner_text(timeout=5_000) if page.locator("body").count() else ""
        page_entry["cloudflare_detected"] = has_cloudflare_challenge_script(rendered_html)
        blocked_reasons = detect_blocked_page(page_entry["status"], details.get("title", ""), visible_text)
        if blocked_reasons:
            page_entry["blocked"] = True
            page_entry["blocked_reasons"] = blocked_reasons
            page_entry["artifact_label"] = "blocked_evidence"
            page_entry["errors_or_blocking_details"].extend(blocked_reasons)

        desktop_suffix = "blocked-desktop" if page_entry["blocked"] else "desktop"
        desktop_path = run / "screenshots" / f"{base_slug}-{desktop_suffix}.png"
        try:
            page.screenshot(path=str(desktop_path), full_page=True, timeout=15_000)
        except Exception:
            page.screenshot(path=str(desktop_path), full_page=False, timeout=10_000)
        page_entry["screenshot_paths"]["desktop"] = relative(desktop_path)
    except Exception as exc:  # noqa: BLE001 - blocked pages still belong in manifest.
        page_entry["elapsed_ms"] = round((time.time() - started) * 1000)
        page_entry["errors_or_blocking_details"].append(str(exc))
        try:
            page_entry["final_url"] = page.url
            rendered_html = page.content()
            visible_text = page.locator("body").inner_text(timeout=2_000) if page.locator("body").count() else ""
            title = page.title()
            details["title"] = title
            page_entry["cloudflare_detected"] = has_cloudflare_challenge_script(rendered_html)
            blocked_reasons = detect_blocked_page(page_entry["status"], title, visible_text)
            if blocked_reasons:
                page_entry["blocked"] = True
                page_entry["blocked_reasons"] = blocked_reasons
                page_entry["artifact_label"] = "blocked_evidence"
                page_entry["errors_or_blocking_details"].extend(blocked_reasons)
            desktop_suffix = "blocked-desktop-error" if page_entry["blocked"] else "desktop-error"
            desktop_path = run / "screenshots" / f"{base_slug}-{desktop_suffix}.png"
            page.screenshot(path=str(desktop_path), full_page=False, timeout=5_000)
            page_entry["screenshot_paths"]["desktop"] = relative(desktop_path)
        except Exception as nested_exc:  # noqa: BLE001
            page_entry["errors_or_blocking_details"].append(f"Failed to save error screenshot: {nested_exc}")
    finally:
        context.close()

    if capture_mobile:
        mobile_context = browser.new_context(
            viewport=MOBILE_VIEWPORT,
            is_mobile=True,
            ignore_https_errors=True,
            locale="en-US",
            timezone_id="America/New_York",
        )
        mobile_page = mobile_context.new_page()
        try:
            mobile_page.goto(page_entry["final_url"] or url, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
            try:
                mobile_page.wait_for_load_state("networkidle", timeout=6_000)
            except Exception:
                pass
            mobile_suffix = "blocked-mobile" if page_entry["blocked"] else "mobile"
            mobile_path = run / "screenshots" / f"{base_slug}-{mobile_suffix}.png"
            try:
                mobile_page.screenshot(path=str(mobile_path), full_page=True, timeout=15_000)
            except Exception:
                mobile_page.screenshot(path=str(mobile_path), full_page=False, timeout=10_000)
            page_entry["screenshot_paths"]["mobile"] = relative(mobile_path)
        except Exception as exc:  # noqa: BLE001
            page_entry["errors_or_blocking_details"].append(f"Mobile capture failed: {exc}")
        finally:
            mobile_context.close()
    else:
        page_entry["mobile_capture_skipped"] = True

    internal_links: list[str] = []
    external_links: list[str] = []
    product_signals: dict[str, Any] = {}
    collection_signals: dict[str, Any] = {}
    content_signals: dict[str, Any] = {}
    if not page_entry["blocked"]:
        for link in details.get("links", []):
            normalized = normalize_link(page_entry["final_url"] or url, link.get("href"))
            if not normalized:
                continue
            if same_host(normalized, host):
                internal_links.append(normalized)
            else:
                external_links.append(normalized)

        product_signals, collection_signals, content_signals = extract_signals(page_entry["final_url"] or url, visible_text, details)

    artifact_slug = f"{base_slug}-blocked" if page_entry["blocked"] else base_slug
    html_path = run / "html" / f"{artifact_slug}.html"
    text_path = run / "text" / f"{artifact_slug}.txt"
    raw_path = run / "raw" / f"{artifact_slug}.json"
    html_path.write_text(rendered_html, encoding="utf-8")
    text_path.write_text(visible_text[:120_000], encoding="utf-8")

    page_entry.update(
        {
            "title": details.get("title", ""),
            "meta_description": "" if page_entry["blocked"] else details.get("meta_description", ""),
            "html_path": relative(html_path),
            "text_path": relative(text_path),
            "raw_path": relative(raw_path),
            "internal_links": dedupe_sorted(internal_links)[:200],
            "external_links": sorted(set(external_links))[:200],
            "cta_button_text": [] if page_entry["blocked"] else details.get("button_texts", [])[:80],
            "forms_detected": [] if page_entry["blocked"] else details.get("forms", []),
            "product_signals": product_signals,
            "collection_signals": collection_signals,
            "content_signals": content_signals,
            "structured_data_count": 0 if page_entry["blocked"] else details.get("structured_data_count", 0),
            "structured_data_types": [] if page_entry["blocked"] else details.get("structured_data_types", []),
            "favicon_links": [] if page_entry["blocked"] else details.get("favicon_links", []),
            "privacy_or_cookie_links": [] if page_entry["blocked"] else details.get("privacy_or_cookie_links", []),
            "image_count": 0 if page_entry["blocked"] else details.get("image_count", 0),
            "images_missing_alt_count": 0 if page_entry["blocked"] else details.get("images_missing_alt_count", 0),
            "load_timing_ms": details.get("performance_timing", {}),
        }
    )
    raw_path.write_text(json.dumps({"extracted_dom_details": details, "page_entry": page_entry}, indent=2), encoding="utf-8")
    return page_entry


def seed_urls(normalized_url: str) -> list[str]:
    origin = origin_for(normalized_url)
    seeds = [normalized_url, urllib.parse.urljoin(origin, "/cart")]
    seeds.extend(urllib.parse.urljoin(origin, path) for path in TECHNICAL_PATHS)
    return seeds


def select_render_queue(base_url: str, discovered: list[str]) -> list[str]:
    buckets: dict[str, list[str]] = {
        "homepage": [],
        "product": [],
        "collection": [],
        "cart": [],
        "faq": [],
        "shipping": [],
        "returns": [],
        "contact": [],
        "store_locator": [],
        "content": [],
    }
    for url in dedupe_sorted([base_url, urllib.parse.urljoin(origin_for(base_url), "/cart"), *discovered]):
        kind = classify_url(url)
        if kind in buckets:
            buckets[kind].append(url)

    selected: list[str] = []
    selected.extend(buckets["homepage"][:1])
    selected.extend(buckets["product"][:5])
    selected.extend(buckets["collection"][:3])
    selected.extend(buckets["cart"][:1])
    for kind in ("faq", "shipping", "returns", "contact", "store_locator", "content"):
        selected.extend(buckets[kind][:1])
    return dedupe_sorted(selected)[:MAX_RENDERED_PAGES]


def technical_checks(
    normalized_url: str,
    pages: list[dict[str, Any]],
    endpoints: dict[str, dict[str, Any]],
    sampled_broken_links: list[dict[str, Any]],
) -> list[dict[str, str]]:
    parsed = urllib.parse.urlparse(normalized_url)

    def row(check: str, ok: bool, detail: str, warn: bool = False) -> dict[str, str]:
        return {"check": check, "status": "Pass" if ok else ("Warn" if warn else "Fail"), "detail": detail}

    homepage = next((p for p in pages if p["surface_type"] == "homepage"), None)
    product = next((p for p in pages if p["surface_type"] == "product" and not p.get("blocked") and p.get("status", 0) and p["status"] < 400), None)
    collection = next((p for p in pages if p["surface_type"] == "collection" and not p.get("blocked") and p.get("status", 0) and p["status"] < 400), None)
    cart = next((p for p in pages if p["surface_type"] == "cart"), None)
    robots = endpoints.get("/robots.txt", {})
    sitemap = endpoints.get("/sitemap.xml", {}) or endpoints.get("/sitemap_index.xml", {})
    products_json = endpoints.get("/products.json", {})
    collections_json = endpoints.get("/collections.json", {})
    all_ok_pages = [p for p in pages if not p.get("blocked") and p.get("status") and p["status"] < 400]
    homepage_loaded = bool(homepage and not homepage.get("blocked") and homepage.get("status") and homepage["status"] < 400)
    cart_loaded = bool(cart and not cart.get("blocked") and cart.get("status") and cart["status"] < 400)

    return [
        row("SSL", parsed.scheme == "https", f"Normalized URL scheme: {parsed.scheme}.", warn=parsed.scheme != "https"),
        row("HTTPS redirect", bool(homepage and str(homepage.get("final_url", "")).startswith("https://")), f"Homepage final URL: {(homepage or {}).get('final_url', 'not loaded')}.", warn=True),
        row("Robots.txt", bool(robots.get("ok")), f"Status: {robots.get('status', 'not checked')}.", warn=bool(robots and not robots.get("ok"))),
        row("Sitemap", bool(sitemap.get("ok")), f"Status: {sitemap.get('status', 'not checked')}.", warn=bool(sitemap and not sitemap.get("ok"))),
        row("Shopify products JSON", bool(products_json.get("ok")), f"Status: {products_json.get('status', 'not checked')}.", warn=True),
        row("Shopify collections JSON", bool(collections_json.get("ok")), f"Status: {collections_json.get('status', 'not checked')}.", warn=True),
        row("Homepage loads", homepage_loaded, f"Status: {(homepage or {}).get('status', 'not loaded')}; blocked: {(homepage or {}).get('blocked', False)}."),
        row("Product page sampled", bool(product), f"Sampled URL: {(product or {}).get('final_url', 'none')}.", warn=True),
        row("Collection page sampled", bool(collection), f"Sampled URL: {(collection or {}).get('final_url', 'none')}.", warn=True),
        row("Cart reachable", cart_loaded, f"Status: {(cart or {}).get('status', 'not loaded')}; blocked: {(cart or {}).get('blocked', False)}.", warn=True),
        row("Meta titles", any(p.get("title") for p in all_ok_pages), "At least one rendered page exposed a title." if any(p.get("title") for p in all_ok_pages) else "No title found in rendered pages.", warn=True),
        row("Meta descriptions", any(p.get("meta_description") for p in all_ok_pages), "At least one rendered page exposed a meta description." if any(p.get("meta_description") for p in all_ok_pages) else "No meta description found in rendered pages.", warn=True),
        row("Structured data", any(p.get("structured_data_count", 0) for p in all_ok_pages), "JSON-LD found on at least one rendered page." if any(p.get("structured_data_count", 0) for p in all_ok_pages) else "No JSON-LD found in rendered pages.", warn=True),
        row("Favicon", any(p.get("favicon_links") for p in all_ok_pages), "Favicon link found." if any(p.get("favicon_links") for p in all_ok_pages) else "No favicon link found.", warn=True),
        row("Cookie/privacy link", any(p.get("privacy_or_cookie_links") for p in all_ok_pages), "Privacy or cookie link found." if any(p.get("privacy_or_cookie_links") for p in all_ok_pages) else "No privacy or cookie link found in sampled pages.", warn=True),
        row("Broken internal links sampled", not sampled_broken_links, f"{len(sampled_broken_links)} sampled broken links found.", warn=bool(sampled_broken_links)),
        row("Missing image alt text", not any(p.get("images_missing_alt_count", 0) for p in all_ok_pages), f"{sum(p.get('images_missing_alt_count', 0) for p in all_ok_pages)} images without alt text in rendered samples.", warn=True),
        row("Rough browser timing captured", any(p.get("load_timing_ms") for p in all_ok_pages), "Navigation timing collected from rendered pages.", warn=True),
    ]


def sample_broken_links(links: list[str]) -> list[dict[str, Any]]:
    broken: list[dict[str, Any]] = []
    for link in dedupe_sorted(links)[:30]:
        result = fetch_endpoint(link)
        status = result.get("status")
        if status is None or status >= 400:
            broken.append({"url": link, "status": status, "error": result.get("error")})
    return broken


def main(argv: list[str] | None = None) -> int:
    try:
        options = read_start_url(sys.argv[1:] if argv is None else argv)
        start_url = options.start_url
        normalized_url = normalize_start_url(start_url)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    run = make_run_folder(normalized_url)
    host = host_key(normalized_url)
    origin = origin_for(normalized_url)
    endpoint_summaries: dict[str, dict[str, Any]] = {}
    discovered: list[str] = []
    failed_pages: list[dict[str, Any]] = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright is not installed. Install it with: python3 -m pip install playwright && python3 -m playwright install chromium", file=sys.stderr)
        return 1

    def record_failed_page(page: dict[str, Any]) -> None:
        blocking_details = [
            detail
            for detail in page.get("errors_or_blocking_details", [])
            if not detail.startswith("Network idle wait skipped:")
        ]
        if page.get("blocked") or page.get("status") is None or page.get("status", 0) >= 400 or blocking_details:
            failed_pages.append(
                {
                    "url": page["url"],
                    "final_url": page["final_url"],
                    "status": page["status"],
                    "blocked": page.get("blocked", False),
                    "blocked_reasons": page.get("blocked_reasons", []),
                    "errors_or_blocking_details": blocking_details,
                }
            )

    pages: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not options.headful)
        try:
            seen: set[str] = set()
            homepage = capture_rendered_page(browser, run, normalized_url, host, capture_mobile=not options.no_mobile)
            pages.append(homepage)
            seen.add(normalized_url)
            record_failed_page(homepage)

            for path in TECHNICAL_PATHS:
                endpoint_url = urllib.parse.urljoin(origin, path)
                result = fetch_endpoint(endpoint_url)
                endpoint_summaries[path] = save_endpoint_artifact(run, result)
                body = result.get("body", b"")
                if path in {"/products.json", "/collections.json"} and result.get("ok"):
                    discovered.extend(discover_from_json(endpoint_url, body))
                if path in {"/sitemap.xml", "/sitemap_index.xml"} and result.get("ok"):
                    discovered.extend(discover_from_sitemap(body, endpoint_url, host))

            queue = [item for item in select_render_queue(normalized_url, discovered) if item not in seen]
            while queue and len(pages) < MAX_RENDERED_PAGES:
                url = queue.pop(0)
                normalized = normalize_link(normalized_url, url)
                if not normalized or normalized in seen or not same_host(normalized, host):
                    continue
                seen.add(normalized)
                page = capture_rendered_page(browser, run, normalized, host, capture_mobile=not options.no_mobile)
                pages.append(page)
                record_failed_page(page)

                new_links = [link for link in page.get("internal_links", []) if priority(link) < 9]
                queue = [item for item in dedupe_sorted([*queue, *new_links]) if item not in seen]
                if len(pages) >= 6:
                    queue = select_render_queue(normalized_url, [*queue, *discovered])
                    queue = [item for item in queue if item not in seen]
        finally:
            browser.close()

    sampled_broken_links = sample_broken_links([link for page in pages for link in page.get("internal_links", [])])
    manifest = {
        "input_url": start_url,
        "normalized_url": normalized_url,
        "crawl_timestamp": datetime.now(timezone.utc).isoformat(),
        "run_folder": relative(run),
        "page_count": len(pages),
        "max_rendered_pages": MAX_RENDERED_PAGES,
        "mobile_capture_enabled": not options.no_mobile,
        "headful": options.headful,
        "selected_pages": [
            {
                "surface_type": page["surface_type"],
                "url": page["url"],
                "final_url": page["final_url"],
                "status": page["status"],
                "blocked": page.get("blocked", False),
            }
            for page in pages
        ],
        "pages": pages,
        "technical_endpoints": endpoint_summaries,
        "technical_checks": technical_checks(normalized_url, pages, endpoint_summaries, sampled_broken_links),
        "failed_pages": failed_pages,
        "sampled_broken_internal_links": sampled_broken_links,
        "limits_known_gaps": [
            "Artifact collection only; no audit report, proposed experiments, or competitor analysis generated.",
            "Rendered crawl is intentionally bounded to representative storefront surfaces rather than the full site.",
            "Screenshots and DOM extraction depend on pages that are reachable from this runtime without manual authentication.",
            "Rough browser timing is based on Playwright navigation timing and is not a Lighthouse performance audit.",
            "Broken-link checks are sampled from discovered internal links to keep the crawl bounded.",
        ],
    }
    manifest_path = run / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote Playwright crawl artifacts to {relative(run)}")
    print(f"Manifest: {relative(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
