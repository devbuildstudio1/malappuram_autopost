"""The newspapers' own Malappuram district pages (the "district list"): every link on them is Malappuram-district news, so these items
are trusted as district news even when the headline names no town. Free sources only; polite 1.5 s gaps. Used inside GitHub Actions."""
import re, time, urllib.parse
import requests
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept-Language": "ml-IN,ml;q=0.9,en;q=0.5"}

# (outlet name, district page, regex for the article links on it). Checked 30 Oct 2026.
LIST_PAGES = [
    ("മാതൃഭൂമി മലപ്പുറം", "https://www.mathrubhumi.com/malappuram",
     r"(https://www\.mathrubhumi\.com/malappuram/news/[a-z0-9-]+)"),
    ("മനോരമ മലപ്പുറം", "https://www.manoramaonline.com/district-news/malappuram.html",
     r"href=\"((?:https://www\.manoramaonline\.com)?/district-news/malappuram/20\d\d/\d\d/\d\d/[^\"#?]+\.html)\""),
]


def _get(u):
    time.sleep(1.5)
    r = requests.get(u, headers=UA, timeout=40)
    r.raise_for_status()
    return r.text


def candidate_links(limit=60, log=None):
    """article links from every district page (one failing page never stops the others)"""
    links = []
    for name, page, pat in LIST_PAGES:
        try:
            h = _get(page)
        except Exception as e:
            if log is not None:
                log.append(f"district list {name} FAILED: {str(e)[:100]}")
            continue
        base = "{0.scheme}://{0.netloc}".format(urllib.parse.urlparse(page))
        for m in re.finditer(pat, h):
            u = urllib.parse.urljoin(base, m.group(1))
            if u not in links:
                links.append(u)
    return links[:limit]


def article(url):
    """returns dict(url, title, published, text) parsed from the page (same reader as every other outlet)"""
    import allnews
    return allnews.article_any(url)
