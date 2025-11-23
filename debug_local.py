from bs4 import BeautifulSoup

with open('nanfang.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

print("--- Searching for '打印' ---")
for element in soup.find_all(string=lambda text: '打印' in text if text else False):
    print(f"Found '打印' in: {element.parent.name} class={element.parent.get('class')} id={element.parent.get('id')}")
    print(f"Parent content: {element.parent.prettify()[:200]}")

print("\n--- Searching for 'content' divs ---")
for div in soup.find_all('div', class_=lambda c: c and 'content' in c):
    print(f"Div class={div.get('class')} id={div.get('id')}")
    # print(div.prettify()[:100])

print("\n--- Searching for 'article' divs ---")
for div in soup.find_all('div', class_=lambda c: c and 'article' in c):
    print(f"Div class={div.get('class')} id={div.get('id')}")
