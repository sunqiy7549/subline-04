import requests
from bs4 import BeautifulSoup

URL = "https://guangzhou.mofa.go.kr/cn-guangzhou-ko/brd/m_123/list.do"

def get_first_title(page):
    params = {'page': page}
    print(f"Fetching page {page} with params {params}...")
    resp = requests.get(URL, params=params)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Find first article title
    title_elem = soup.select_one("td.al a")
    if not title_elem:
        title_elem = soup.select_one("td.title a")
        
    if title_elem:
        return title_elem.get_text(strip=True)
    return None

t1 = get_first_title(1)
t2 = get_first_title(2)

print(f"Page 1 First Title: {t1}")
print(f"Page 2 First Title: {t2}")

if t1 == t2:
    print("FAIL: Content is identical. pageIndex is ignored.")
else:
    print("SUCCESS: Content is different.")
