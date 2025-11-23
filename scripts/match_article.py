import requests
from bs4 import BeautifulSoup
import re

def match_article():
    # Target: Nanfang Daily, 2025-11-07, Page A01
    # URL Pattern: https://epaper.southcn.com/nfdaily/html/202511/07/node_A01.html
    
    date_str = "202511/07"
    page_str = "A01"
    base_url = f"https://epaper.southcn.com/nfdaily/html/{date_str}/node_{page_str}.html"
    
    print(f"Fetching e-paper page: {base_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract articles
        # Based on typical e-paper structure, links are usually in a map or list
        # Let's look for all links first
        
        print("Scanning for articles...")
        candidates = []
        
        # Strategy: Look for links that point to content_*.html
        # Based on inspection: div#content_nav ul#artPList1 a
        
        links = soup.select("div#content_nav ul#artPList1 a")
        if not links:
             # Fallback: try finding all links with content_
             links = soup.find_all('a', href=True)
             
        for a in links:
            href = a.get('href')
            if not href: continue
            
            text = a.get_text(strip=True)
            
            if 'content_' in href and text:
                # Resolve full URL
                if not href.startswith('http'):
                    # href is relative like "content_1018375.html"
                    # base is https://epaper.southcn.com/nfdaily/html/2025-11/07/
                    full_url = base_url.rsplit('/', 1)[0] + '/' + href
                else:
                    full_url = href
                    
                candidates.append({
                    "title": text,
                    "url": full_url
                })
        
        print(f"Found {len(candidates)} articles on page {page_str}.")
        
        # Keywords from Korean summary: "광둥성 제14차 5개년 계획 성과 보고서 발표 — 주요 지표 다수 전국 1위 차지"
        # "주요 지표 다수 전국 1위 차지" -> "Multiple major indicators rank 1st in the country"
        # Observed title: "多项数据位居全国首位"
        
        keywords = ["十四五", "规划", "广东", "全国首位", "数据", "第一"]
        
        print(f"Filtering for keywords: {keywords}")
        
        matches = []
        for cand in candidates:
            score = 0
            for kw in keywords:
                if kw in cand['title']:
                    score += 1
            
            if score > 0:
                matches.append((score, cand))
        
        # Sort by score
        matches.sort(key=lambda x: x[0], reverse=True)
        
        if matches:
            print("\nTop Matches:")
            for score, cand in matches:
                print(f"[Score: {score}] {cand['title']}")
                print(f"  URL: {cand['url']}")
        else:
            print("\nNo matches found.")
            print("All titles found:")
            for cand in candidates:
                print(f"- {cand['title']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    match_article()
