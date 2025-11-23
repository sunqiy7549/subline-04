from datetime import date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def build_node_url(d: date, section: str = "A01") -> str:
    """
    生成南方日报数字报 node URL，例如：
    https://epaper.southcn.com/nfdaily/html/202511/22/node_A01.html
    """
    return f"https://epaper.southcn.com/nfdaily/html/{d:%Y%m}/{d:%d}/node_{section}.html"


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def parse_nanfang_node(html: str, base_url: str):
    """
    解析 node_A01.html 这种版面页，返回 [ {title, url}, ... ]
    """
    soup = BeautifulSoup(html, "lxml")
    results = []

    # 优先找"第A01版"这一块
    h3 = None
    for candidate in soup.find_all(["h3", "h2"]):
        text = candidate.get_text(strip=True)
        if text.startswith("第A01版"):
            h3 = candidate
            break

    if h3 is not None:
        ul = h3.find_next("ul")
    else:
        # 如果没找到"第A01版"，退而求其次：找包含"标题导航"的块附近的第一个 <ul>
        nav_label = soup.find(string=lambda t: t and "标题导航" in t)
        if nav_label:
            ul = soup.find("ul")
        else:
            ul = None

    if not ul:
        return results

    for li in ul.find_all("li"):
        a = li.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        if not title:
            continue
        href = a.get("href")
        if not href:
            continue
        full_url = urljoin(base_url, href)
        results.append({"title": title, "url": full_url})

    return results


def fetch_nanfang_articles(d: date, section: str = "A01"):
    """
    对外暴露的统一接口：给定日期 -> 返回该版面文章列表
    """
    url = build_node_url(d, section=section)
    html = fetch_html(url)
    return parse_nanfang_node(html, base_url=url)
