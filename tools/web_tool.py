from html import unescape
from urllib.parse import quote_plus
import re

import requests

from config import MAX_WEB_RESULTS, MAX_WEB_TEXT_CHARS


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36 Voss/1.0"
)


def _fetch_text(url: str) -> str:
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    return response.text


def _strip_html(html: str) -> str:
    html = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?>.*?</style>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_WEB_TEXT_CHARS:
        return text[:MAX_WEB_TEXT_CHARS] + " [truncated]"
    return text


def search_web(query: str) -> str:
    query = query.strip()
    if not query:
        return "Web search query is empty."

    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    html = _fetch_text(url)

    matches = re.findall(
        r'<a[^>]*class="result__a"[^>]*href="(.*?)"[^>]*>(.*?)</a>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not matches:
        return f"No web results found for '{query}'."

    lines = [f"Web results for '{query}':"]
    for href, title in matches[:MAX_WEB_RESULTS]:
        clean_title = re.sub(r"<[^>]+>", "", unescape(title)).strip()
        lines.append(f"- {clean_title}")
        lines.append(f"  {href}")
    return "\n".join(lines)


def fetch_page(url: str) -> str:
    url = url.strip()
    if not url:
        return "URL is empty."
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        url = f"https://{url}"

    html = _fetch_text(url)
    text = _strip_html(html)
    return f"Page content from {url}:\n{text}"


def summarize_page(url: str) -> str:
    url = url.strip()
    if not url:
        return "URL is empty."
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        url = f"https://{url}"

    html = _fetch_text(url)
    title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    title = re.sub(r"\s+", " ", unescape(title_match.group(1))).strip() if title_match else url
    text = _strip_html(html)
    excerpt = text[:1500]
    return f"Page title: {title}\nURL: {url}\nExtracted text:\n{excerpt}"
