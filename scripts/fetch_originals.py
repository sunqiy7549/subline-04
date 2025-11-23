import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup

# Configuration
MATCHES_FILE = "data/mofa/matches.json"
DATASET_FILE = "data/dataset.json"
ORIGINALS_DIR = "data/originals"

os.makedirs(ORIGINALS_DIR, exist_ok=True)

def extract_keywords(text):
    """Extracts numbers and Chinese characters (often in parens) from Korean text."""
    keywords = []
    
    # 1. Chinese characters in parens: (黄坤明) or （黄坤明）
    # Also sometimes just in text? Usually in parens in these reports.
    # Handle both ASCII and Full-width parens
    chinese_matches = re.findall(r'[\(\（]([\u4e00-\u9fff]+)[\)\）]', text)
    keywords.extend(chinese_matches)
    
    # 2. Numbers (2+ digits to avoid "1.", "2." item numbers if possible, but "5개년" has 1 digit)
    # Let's take all numbers for now, but ignore the leading item number "1. " which is usually stripped already.
    numbers = re.findall(r'\d+', text)
    keywords.extend(numbers)
    
    return keywords

def score_candidate(candidate, keywords):
    score = 0
    title = candidate['title']
    
    chinese_keywords = [k for k in keywords if not re.match(r'^\d+$', k)]
    number_keywords = [k for k in keywords if re.match(r'^\d+$', k)]
    
    # 1. Check Chinese Keywords (High Confidence)
    matched_chinese = 0
    for kw in chinese_keywords:
        if kw in title:
            score += 10
            matched_chinese += 1
            
    # 2. Check Number Keywords (Low Confidence)
    matched_numbers = 0
    for kw in number_keywords:
        # Exact match for numbers to avoid "1" matching "10"
        # But title might be "10月...", so just check containment for now but maybe stricter?
        if kw in title:
            score += 1
            matched_numbers += 1
            
    # PENALTY: If we have Chinese keywords but NONE matched, this is likely wrong.
    if chinese_keywords and matched_chinese == 0:
        score = -100 # Strong penalty
        
    # REQUIREMENT: If only numbers, need at least 2 matches to be somewhat confident
    if not chinese_keywords and matched_numbers < 2:
        score = -50 # Penalty for weak number-only match
        
    return score

def fetch_content(url, newspaper):
    print(f"    Fetching content from {url}...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8' # Most are utf-8
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Selectors based on newspaper
        content_div = None
        
        if "Nanfang" in newspaper or "南方" in newspaper:
            content_div = soup.select_one('#content') or soup.select_one('.article-content')
            
        elif "Guangzhou" in newspaper or "广州" in newspaper:
            content_div = soup.select_one('div.article-content') or soup.select_one('#content') or soup.select_one('.content')
            
        elif "Fujian" in newspaper or "福建" in newspaper:
            content_div = soup.select_one('.article-content') or soup.select_one('#content')
            
        elif "Hainan" in newspaper or "海南" in newspaper:
            content_div = soup.select_one('#content') or soup.select_one('.content')
            
        # Fallback: specific common IDs
        if not content_div:
            content_div = soup.select_one('#articleContent') or soup.select_one('.art_txt')
            
        if content_div:
            # Clean up
            for bad in content_div.select('script, style, .print, .tools'):
                bad.decompose()
            return content_div.get_text(strip=True)
        else:
            # Last resort: largest text block
            ps = soup.find_all('p')
            if ps:
                text = "\n".join([p.get_text(strip=True) for p in ps])
                if len(text) > 100:
                    return text
            return None

    except Exception as e:
        print(f"    Error fetching content: {e}")
        return None

def main():
    if not os.path.exists(MATCHES_FILE):
        print("Matches file not found.")
        return

    with open(MATCHES_FILE, 'r', encoding='utf-8') as f:
        matches = json.load(f)
        
    dataset = []
    
    print(f"Processing {len(matches)} matched items...")
    
    for entry in matches:
        item = entry['item']
        candidates = entry['matches']['candidates']
        
        if not candidates:
            continue
            
        print(f"Processing: {item['headline'][:30]}...")
        
        # Score candidates
        keywords = extract_keywords(item['full_text']) # Use full text for keywords (contains parens)
        
        best_cand = None
        best_score = -1
        
        for cand in candidates:
            score = score_candidate(cand, keywords)
            if score > best_score:
                best_score = score
                best_cand = cand
        
        # Threshold? If score is 0, maybe the first one is still the intended one if it's the only one?
        # Or if there are multiple 0s, we can't decide.
        # If there is only 1 candidate, take it regardless of score (it was found on the specific page/edition).
        
        selected = None
        if len(candidates) == 1:
            selected = candidates[0]
            reason = "Only Candidate"
        elif best_score > 0:
            selected = best_cand
            reason = f"Score {best_score}"
        else:
            # Multiple candidates, score 0.
            # Heuristic: Maybe the first one? Or skip?
            # Let's skip to be safe, or maybe log it.
            print(f"  Skipping: Multiple candidates ({len(candidates)}) but score 0. Keywords: {keywords}")
            continue
            
        print(f"  Selected: {selected['title']} ({reason})")
        
        # Fetch Content
        content = fetch_content(selected['url'], item['newspaper'])
        
        if content:
            # Save to dataset
            data_entry = {
                "korean_summary": item['full_text'],
                "korean_headline": item['headline'],
                "chinese_title": selected['title'],
                "chinese_content": content,
                "source_url": selected['url'],
                "newspaper": item['newspaper'],
                "date": item['date'],
                "page": item['page']
            }
            dataset.append(data_entry)
            
            # Save individual file
            safe_title = re.sub(r'[\\/*?:"<>|]', "", selected['title'])[:50]
            filename = f"{item['date']}_{item['newspaper']}_{safe_title}.json"
            with open(os.path.join(ORIGINALS_DIR, filename), 'w', encoding='utf-8') as f:
                json.dump(data_entry, f, ensure_ascii=False, indent=2)
                
            print(f"  Saved to {filename}")
        else:
            print("  Failed to extract content.")
            
        time.sleep(0.5)
        
    # Save full dataset
    with open(DATASET_FILE, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
        
    print(f"Done. Created dataset with {len(dataset)} items.")

if __name__ == "__main__":
    main()
