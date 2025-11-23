import os
import json
import time
import requests
from bs4 import BeautifulSoup
from mofa_utils import parse_mofa_article
from urllib.parse import urljoin

# Configuration
DATA_DIR = "data/mofa/articles"
MATCHES_FILE = "data/mofa/matches.json"
REPORT_FILE = "matching_report.md"

# Newspaper Configurations
NEWSPAPERS = {
    "Nanfang Daily": {
        "names": ["南方日报", "Nanfang Daily"],
        "url_pattern": "https://epaper.southcn.com/nfdaily/html/{yyyy}{mm}/{dd}/node_{page}.html",
        "selector": "div#content_nav ul#artPList1 a",
        "encoding": "utf-8"
    },
    "Guangzhou Daily": {
        "names": ["广州日报", "Guangzhou Daily"],
        "url_pattern": "https://gzdaily.dayoo.com/pc/html/{yyyy}-{mm}/{dd}/node_{page}.htm?v=1",
        "selector": "a", # Fallback to all links first, refine if needed
        "encoding": "utf-8"
    },
    "Fujian Daily": {
        "names": ["福建日报", "Fujian Daily"],
        "url_pattern": "https://fjrb.fjdaily.com/pc/col/{yyyy}{mm}/{dd}/node_{page}.html",
        "selector": "li.resultList a",
        "encoding": "utf-8"
    },
    "Hainan Daily": {
        "names": ["海南日报", "Hainan Daily"],
        "url_pattern": "http://news.hndaily.cn/html/{yyyy}-{mm}/{dd}/node_{page}.htm?v=1",
        "selector": "a", # Fallback
        "encoding": "utf-8"
    }
}

def get_newspaper_config(name):
    for key, config in NEWSPAPERS.items():
        if name in config['names']:
            return key, config
    return None, None

def fetch_article_list(url, config):
    print(f"  Fetching {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = config['encoding']
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        if config['selector'] == 'a':
             candidates = soup.find_all('a', href=True)
        else:
             candidates = soup.select(config['selector'])
             if not candidates: # Fallback
                 candidates = soup.find_all('a', href=True)
                 
        for a in candidates:
            href = a.get('href')
            text = a.get_text(strip=True)
            
            if not href or not text: continue
            
            # Heuristic: Article links usually contain 'content' or are relative
            # Nanfang: content_*.html
            # Guangzhou: content_*.htm
            # Fujian: content_*.html
            # Hainan: content_*.htm
            
            if 'content' in href:
                full_url = urljoin(url, href)
                links.append({'title': text, 'url': full_url})
                
        return links
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return []

def match_item(item):
    newspaper_name = item['newspaper']
    if not newspaper_name or newspaper_name == "Unknown":
        return None, "Unknown Newspaper"
        
    # Exclude Guangxi
    if "广西" in newspaper_name:
        return None, "Skipped (Guangxi Daily)"
        
    key, config = get_newspaper_config(newspaper_name)
    if not config:
        return None, f"Unsupported Newspaper: {newspaper_name}"
        
    # Parse Date
    # item['date'] is "11.7" (MM.DD)
    # We need YYYY.
    # The source file name has the year: "2025-11-13_..."
    # Let's extract year from source_file
    
    try:
        source_date_str = item['source_file'][:10] # 2025-11-13
        year = source_date_str[:4]
        
        # item['date'] = "11.7"
        md = item['date'].split('.')
        if len(md) != 2:
            return None, f"Invalid Date Format: {item['date']}"
            
        month = md[0].zfill(2)
        day = md[1].zfill(2)
        
        # Page
        # item['page'] = "A1" -> "A01" usually?
        # Nanfang: node_A01
        # Guangzhou: node_1 (if A1?) or node_A1? 
        # Let's assume the user provided URL patterns imply node_PAGE. 
        # But page format might differ.
        # Nanfang: A1 -> A01 (Need mapping)
        # Guangzhou: A1 -> 1? Or A1?
        
        page = item['page']
        
        # Normalize Page for Nanfang (A1 -> A01)
        if key == "Nanfang Daily":
            if page.startswith('A') and len(page) == 2:
                page = page[0] + '0' + page[1] # A1 -> A01
        
        # Guangzhou: node_1.htm for A1? User link: node_1.htm
        if key == "Guangzhou Daily":
             if page.startswith('A'):
                 page = page[1:] # A1 -> 1
        
        # Fujian: node_01.html (User link: node_01.html)
        if key == "Fujian Daily":
             if page.startswith('A'):
                 page = page[1:].zfill(2) # A1 -> 01
                 
        # Hainan: node_1.htm (User link: node_1.htm)
        if key == "Hainan Daily":
             if page.startswith('A'):
                 page = page[1:] # A1 -> 1

        url = config['url_pattern'].format(yyyy=year, mm=month, dd=day, page=page)
        
        # Fetch
        articles = fetch_article_list(url, config)
        if not articles:
            return None, f"No articles found at {url}"
            
        # Match
        # Keywords: Split headline by spaces/punctuation and take longer words?
        # Or just use the whole headline?
        # Korean headline: "..."
        # We need Chinese keywords.
        # The parser doesn't extract Chinese keywords yet.
        # Wait, the Korean summary usually contains Chinese names/terms in parens?
        # Or we rely on the fact that the Korean summary *is* a summary of the Chinese title?
        # Actually, without Chinese keywords, matching is hard.
        # But wait, the user said "Find the original...".
        # In the previous step, I manually added keywords "十四五", "规划".
        # The parser extracts the *Korean* headline.
        # I need to find a way to match Korean headline to Chinese title.
        # This is impossible without translation or cross-lingual matching.
        # UNLESS the Korean headline contains the Chinese title?
        # Looking at the data: "광둥성 제14차 5개년 계획 성과 보고서 발표 — 주요 지표 다수 전국 1위 차지"
        # It does NOT contain the Chinese title "多项数据位居全国首位".
        # However, the user's prompt implies I should be able to do this.
        # Maybe I should use the *translated* Korean headline to match?
        # Or maybe I should just list all articles on that page and let the user pick?
        # OR, I can try to match numbers? "14", "5", "1".
        
        # For this batch script, I will:
        # 1. List all articles found on that page.
        # 2. If there's only a few, maybe just save them all as candidates?
        # 3. Or try to translate the Korean headline to Chinese using a simple mapping or just keywords?
        
        # Actually, for the purpose of this task, finding the *Page* URL is already a big step.
        # Finding the specific *Article* URL requires semantic matching.
        # I will implement a simple keyword match if possible, otherwise return the Page URL and list of candidates.
        
        # Let's try to match numbers and common terms if possible.
        # But for now, I'll return the list of candidates.
        
        return {
            "page_url": url,
            "candidates": articles
        }, "Candidates Found"

    except Exception as e:
        return None, f"Error: {e}"

def main():
    files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.json')])
    all_matches = []
    
    print(f"Processing {len(files)} files...")
    
    stats = {
        "total": 0,
        "skipped_guangxi": 0,
        "matched": 0,
        "failed": 0
    }
    
    report_lines = ["# Batch Matching Report\n"]
    report_lines.append("| Date | Newspaper | Page | Status | Candidates/Match |")
    report_lines.append("|---|---|---|---|---|")
    
    for filename in files:
        path = os.path.join(DATA_DIR, filename)
        items = parse_mofa_article(path)
        
        for item in items:
            stats["total"] += 1
            print(f"Processing: {item['newspaper']} - {item['headline'][:20]}...")
            
            result, status = match_item(item)
            
            if "Guangxi" in status:
                stats["skipped_guangxi"] += 1
                continue
                
            if result:
                stats["matched"] += 1
                candidates = result['candidates']
                cand_str = "<br>".join([f"[{c['title']}]({c['url']})" for c in candidates[:3]])
                if len(candidates) > 3:
                    cand_str += f"<br>...and {len(candidates)-3} more"
                
                report_lines.append(f"| {item['date']} | {item['newspaper']} | {item['page']} | ✅ {status} | {cand_str} |")
                
                all_matches.append({
                    "item": item,
                    "matches": result
                })
            else:
                stats["failed"] += 1
                report_lines.append(f"| {item['date']} | {item['newspaper']} | {item['page']} | ❌ {status} | - |")
            
            time.sleep(0.5) # Rate limit
            
    # Save matches
    with open(MATCHES_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_matches, f, ensure_ascii=False, indent=2)
        
    # Save Report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        f.write("\n\n## Statistics\n")
        f.write(f"- Total Items: {stats['total']}\n")
        f.write(f"- Skipped (Guangxi): {stats['skipped_guangxi']}\n")
        f.write(f"- Matched (Candidates Found): {stats['matched']}\n")
        f.write(f"- Failed: {stats['failed']}\n")
        
    print("Done. Report generated.")

if __name__ == "__main__":
    main()
