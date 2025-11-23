import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from deep_translator import GoogleTranslator
import logging

# Mocking the ARTICLE_CACHE
ARTICLE_CACHE = {}

def translate_text(text, target='ko'):
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

def fetch_and_translate_article_logic(url):
    print(f"Fetching {url}...")
    
    # Check if this is a Nanfang Daily URL (southcn.com or nfnews.com)
    if 'southcn.com' in url or 'nfnews.com' in url:
        try:
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Try specific selectors for Nanfang
            # 1. Standard e-paper content
            content_div = soup.select_one('#content') or \
                          soup.select_one('.article-content') or \
                          soup.select_one('#article_content') or \
                          soup.select_one('.article')
            
            # 2. If not found, try finding the largest text block that isn't a list
            if not content_div:
                # Fallback: look for div with most text
                divs = soup.find_all('div')
                if divs:
                    content_div = max(divs, key=lambda d: len(d.get_text(strip=True)) if 'list' not in d.get('class', []) else 0)
            
            if content_div:
                # Remove print buttons and other non-content elements
                for bad in content_div.select('.print, .print-btn, .tools, script, style'):
                    bad.decompose()
                
                # Double check we didn't just get the "Print" button
                text = content_div.get_text(strip=True)
                if len(text) < 50 and "打印" in text:
                    print("Found 'Print' button instead of content, retrying...")
                    pass 
                
                original_html = str(content_div)
                paragraphs = [p.get_text(strip=True) for p in content_div.find_all('p') if p.get_text(strip=True)]
                
                # If no paragraphs found, try splitting text by newlines
                if not paragraphs:
                    paragraphs = [line.strip() for line in content_div.get_text().split('\n') if line.strip()]

                print(f"Found {len(paragraphs)} paragraphs.")
                print("First paragraph:", paragraphs[0] if paragraphs else "None")
                
                return {
                    'status': 'success',
                    'content_cn': original_html,
                    'paragraphs_count': len(paragraphs)
                }
            else:
                print("No content div found.")
        except Exception as e:
            print(f"Error fetching Nanfang article {url}: {e}")
            
    return None

if __name__ == "__main__":
    # Test with a URL from the desktop HTML
    test_url = "https://static.nfnews.com/content/202511/21/c11931402.html"
    result = fetch_and_translate_article_logic(test_url)
    if result:
        print("Success!")
    else:
        print("Failed.")
