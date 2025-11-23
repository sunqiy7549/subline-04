import requests
from bs4 import BeautifulSoup

url = "https://epaper.southcn.com/nfdaily/html/2025-11/21/content_1018375.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

try:
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("Searching for '打印'...")
    for element in soup.find_all(string=lambda text: '打印' in text if text else False):
        print(f"Found in: {element.parent.name} class={element.parent.get('class')} id={element.parent.get('id')}")
        print(f"Parent content: {element.parent.prettify()[:200]}")

    print("\n--- Body Structure (First 2000 chars) ---")
    if soup.body:
        print(soup.body.prettify()[:2000])
    else:
        print("No body found")

except Exception as e:
    print(e)
