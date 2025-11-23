import requests
from bs4 import BeautifulSoup
import os
import json
import time
from datetime import datetime, timedelta
import re

# Configuration
BASE_URL = "https://guangzhou.mofa.go.kr/cn-guangzhou-ko/brd/m_123"
LIST_URL = f"{BASE_URL}/list.do"
DATA_DIR = "data/mofa"
ARTICLES_DIR = os.path.join(DATA_DIR, "articles")

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

def get_date_cutoff():
    # 1 Year ago
    return datetime.now() - timedelta(days=365)

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def scrape_mofa():
    print("Starting MOFA scraper (Text Mode)...")
    
    # Ensure directories exist
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    # 1. Fetch List Page
    print(f"Fetching list page: {LIST_URL}")
    try:
        response = session.get(LIST_URL)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching list page: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 2. Parse Articles
    articles = []
    rows = soup.select("table tbody tr")
    
    cutoff_date = get_date_cutoff()
    print(f"Filtering articles since: {cutoff_date.strftime('%Y-%m-%d')}")

    page = 1
    has_more = True
    
    while has_more:
        print(f"Fetching list page {page}: {LIST_URL}?page={page}")
        try:
            response = session.get(f"{LIST_URL}?page={page}")
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching list page {page}: {e}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select("table tbody tr")
        
        if not rows:
            print("No more rows found.")
            break
            
        found_new_articles = False
        
        for row in rows:
            # Extract Title
            title_elem = row.select_one("td.al a")
            if not title_elem:
                title_elem = row.select_one("td.title a") or row.select_one("td.left a")
                
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            
            # Extract Link (Handle JS)
            onclick = title_elem.get('onclick', '')
            match = re.search(r"f_view\('(\d+)'\)", onclick)
            if match:
                seq_id = match.group(1)
                link = f"view.do?seq={seq_id}"
            else:
                link = title_elem['href']
            
            # Filter by Title
            if "화남지역 주간 정무 동향" not in title:
                continue
                
            # Extract Date
            date_str = ""
            for td in row.select("td"):
                text = td.get_text(strip=True)
                if re.match(r"\d{4}-\d{2}-\d{2}", text):
                    date_str = text
                    break
            
            if not date_str:
                continue
                
            article_date = parse_date(date_str)
            if not article_date:
                continue
                
            if article_date < cutoff_date:
                print(f"Reached cutoff date: {title} ({date_str})")
                has_more = False
                break
                
            print(f"Found relevant article: {title} ({date_str})")
            found_new_articles = True
            
            # Resolve full URL
            if link.startswith("/"):
                full_url = f"https://guangzhou.mofa.go.kr{link}"
            elif link.startswith("view.do"):
                 full_url = f"{BASE_URL}/{link}"
            else:
                full_url = link

            articles.append({
                "title": title,
                "date": date_str,
                "url": full_url
            })
        
        if not found_new_articles and has_more:
             # If we parsed a whole page and found nothing relevant, but haven't hit cutoff,
             # it might just be a page of other types of posts. Continue.
             # But if we are very deep, maybe stop?
             # For now, just continue.
             pass
             
        page += 1
        time.sleep(1) # Be polite

    # 3. Process Articles (Scrape Text)
    for article in articles:
        print(f"Processing: {article['title']}")
        try:
            resp = session.get(article['url'])
            resp.raise_for_status()
            detail_soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Strategy 1: Look for specific content container
            # Common classes: view_cont, board_view, view_content
            content_elem = detail_soup.select_one("div.view_cont") or \
                           detail_soup.select_one("div.board_view") or \
                           detail_soup.select_one("div.view_content")
            
            content_text = ""
            if content_elem:
                content_text = content_elem.get_text("\n", strip=True)
            else:
                # Strategy 2: Heuristic extraction from body
                print("  Container not found, using heuristic...")
                full_text = detail_soup.body.get_text("\n", strip=True)
                
                # Improved Heuristics
                # Start: "[광둥성]" or "1. " after a date
                # End: "끝." or "목록"
                
                start_marker = "[광둥성]"
                end_markers = ["끝.", "목록", "이전 글"]
                
                start_idx = full_text.find(start_marker)
                if start_idx == -1:
                    # Fallback: try finding the date and taking text after
                    date_match = re.search(r"작성일\s*\n\s*\d{4}-\d{2}-\d{2}", full_text)
                    if date_match:
                        start_idx = date_match.end()
                
                end_idx = -1
                for marker in end_markers:
                    idx = full_text.find(marker, start_idx if start_idx != -1 else 0)
                    if idx != -1:
                        end_idx = idx
                        break
                
                if start_idx != -1 and end_idx != -1:
                    content_text = full_text[start_idx:end_idx].strip()
                elif start_idx != -1:
                    content_text = full_text[start_idx:].strip()
                else:
                    print("  Heuristic failed. Saving full body text.")
                    content_text = full_text

            # Save JSON
            safe_title = sanitize_filename(article['title'])
            save_name = f"{article['date']}_{safe_title}.json"
            save_path = os.path.join(ARTICLES_DIR, save_name)
            
            data = {
                "title": article['title'],
                "date": article['date'],
                "url": article['url'],
                "content": content_text
            }
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"  Saved to {save_path}")
            time.sleep(1)
            
        except Exception as e:
            print(f"  Failed to process article: {e}")

    print("Done.")

if __name__ == "__main__":
    scrape_mofa()
