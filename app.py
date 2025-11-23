import sys
import os
from flask import Flask, render_template, jsonify, request
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import urllib.parse
import re

if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'))
else:
    app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def get_current_date_strs():
    now = datetime.now()
    # For testing with the specific date provided in the prompt if needed, 
    # but ideally we use today. 
    # However, the user provided links for 2025-11-19. 
    # Since today is 2025-11-19 (per metadata), this works.
    return {
        'yyyymm': now.strftime('%Y%m'),
        'yyyy-mm': now.strftime('%Y-%m'),
        'dd': now.strftime('%d'),
        'date_path': now.strftime('%Y%m/%d')
    }

@app.route('/')
def index():
    return render_template('index.html')

from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator
import threading
from playwright.sync_api import sync_playwright

def translate_text(text, target='ko'):
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return text

def fetch_guangxi_article_with_playwright(url):
    """Fetch Guangxi Daily article using Playwright to execute JavaScript."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Use domcontentloaded instead of networkidle for better compatibility
            page.goto(url, timeout=35000, wait_until='domcontentloaded')
            # Wait longer for JavaScript to execute and load content
            page.wait_for_timeout(5000)
            
            # Get all text content from the page
            all_text = page.inner_text('body')
            browser.close()
            
            # Split into lines and filter
            lines = [line.strip() for line in all_text.split('\n') if line.strip()]
            
            # Find title - try multiple strategies
            title = None
            content_lines = []
            
            # Strategy 1: Look for title with author marker (most reliable)
            for i, line in enumerate(lines):
                # Skip navigation and metadata
                if any(skip in line for skip in ['数字报首页', '按日期查找', '版面导航', '字体：', '返回', '新闻中心', 'ICP证', '广西新闻网版权']):
                    continue
                
                # Look for title - substantial line before author marker
                if not title and 15 < len(line) < 200:
                    # Check if next few lines contain author marker
                    next_lines = lines[i+1:i+5]
                    if any('■' in l or '广西云-广西日报记者' in l or '广西日报记者' in l or '通讯员' in l for l in next_lines):
                        title = line
                        break
            
            # Strategy 2: If no title found, look for substantial lines after date marker
            if not title:
                found_date_marker = False
                for i, line in enumerate(lines):
                    # Look for date/edition marker like "2025年11月20日第 001 版）"
                    if '年' in line and '月' in line and '日' in line and '版）' in line:
                        found_date_marker = True
                        continue
                    
                    # After date marker, find first substantial line
                    if found_date_marker and 10 < len(line) < 200:
                        # Skip common non-title patterns
                        if any(skip in line for skip in ['数字报首页', '按日期查找', '版面导航', '字体', '返回', '发布时间', '各版主要新闻']):
                            continue
                        title = line
                        break
            
            # Collect content
            for i, line in enumerate(lines):
                if len(line) > 30:
                    if '本报讯' in line or '（广西云-广西日报记者' in line:
                        content_lines.append(line)
                    elif not any(skip in line for skip in ['发布时间', '版中缝', '各版主要新闻', '数字报首页', '按日期查找']):
                        # Only add if it looks like content
                        if any(char in line for char in ['，', '。', '、', '：']):
                            content_lines.append(line)
            
            return {
                'title': title,
                'content': content_lines[:10]  # Limit to first 10 paragraphs
            }
            
    except Exception as e:
        logging.error(f"Error fetching Guangxi article with Playwright: {e}")
        return None

def fetch_page_items(session, url, source_type, section_name=""):
    try:
        resp = session.get(url, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        items = []
        
        if source_type == 'fujian':
            # Selector: #main-ed-articlenav-list .wzlb_tr a
            links = soup.select('#main-ed-articlenav-list .wzlb_tr a')
            for link in links:
                title = link.get_text(strip=True)
                href = link.get('href')
                if href:
                    abs_link = urllib.parse.urljoin(url, href)
                    # Translate title
                    title_ko = translate_text(title)
                    items.append({
                        'title': title,
                        'title_ko': title_ko,
                        'link': abs_link,
                        'section': section_name
                    })
                    
        elif source_type == 'hainan':
            # Selector: #main-ed-articlenav-list a
            links = soup.select('#main-ed-articlenav-list a')
            for link in links:
                title = link.get_text(strip=True)
                href = link.get('href')
                if href and title:
                    abs_link = urllib.parse.urljoin(url, href)
                    # Translate title
                    title_ko = translate_text(title)
                    items.append({
                        'title': title,
                        'title_ko': title_ko,
                        'link': abs_link,
                        'section': section_name
                    })
        
        return items
    except Exception as e:
        logging.error(f"Error fetching page {url}: {e}")
        return []

# Global Cache
ARTICLE_CACHE = {}
STARRED_ITEMS = {} # Key: URL, Value: Item Data

def fetch_and_translate_article_logic(url):
    """Helper function to fetch and translate article, used by route and background task."""
    if url in ARTICLE_CACHE:
        print(f"Cache hit for {url}")
        return ARTICLE_CACHE[url]

    print(f"Fetching {url}...")
    
    # Check if this is a Guangxi Daily URL
    if 'gxrb.gxrb.com.cn' in url:
        try:
            # Use Playwright for Guangxi Daily
            article_data = fetch_guangxi_article_with_playwright(url)
            
            if not article_data or not article_data.get('title'):
                return None
            
            # Format content as HTML
            content_html = f"<h2>{article_data['title']}</h2>"
            for para in article_data.get('content', []):
                content_html += f"<p>{para}</p>"
            
            # Translate content paragraphs
            translated_paragraphs = []
            content_paragraphs = article_data.get('content', [])
            
            if content_paragraphs:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(GoogleTranslator(source='zh-CN', target='ko').translate, p) for p in content_paragraphs]
                    for f in futures:
                        try:
                            translated_paragraphs.append(f.result())
                        except Exception as e:
                            print(f"Translation error: {e}")
                            translated_paragraphs.append("[Translation Failed]")
            
            result = {
                'status': 'success',
                'content_cn': content_html,
                'content_ko': translated_paragraphs
            }
            
            # Store in cache
            ARTICLE_CACHE[url] = result
            return result
            
        except Exception as e:
            print(f"Error fetching Guangxi article {url}: {e}")
            return None
    
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
                    # This is likely just the print button, try finding another div
                    print("Found 'Print' button instead of content, retrying...")
                    pass 
                
                original_html = str(content_div)
                paragraphs = [p.get_text(strip=True) for p in content_div.find_all('p') if p.get_text(strip=True)]
                
                # If no paragraphs found, try splitting text by newlines
                if not paragraphs:
                    paragraphs = [line.strip() for line in content_div.get_text().split('\n') if line.strip()]

                translated_paragraphs = []
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(GoogleTranslator(source='zh-CN', target='ko').translate, p) for p in paragraphs]
                    for f in futures:
                        try:
                            translated_paragraphs.append(f.result())
                        except Exception as e:
                            print(f"Translation error: {e}")
                            translated_paragraphs.append("[Translation Failed]")
                
                result = {
                    'status': 'success',
                    'content_cn': original_html,
                    'content_ko': translated_paragraphs
                }
                ARTICLE_CACHE[url] = result
                return result
        except Exception as e:
            print(f"Error fetching Nanfang article {url}: {e}")
            # Fall through to generic logic

    # For other newspapers, use regular requests
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Try different selectors
        content_div = soup.select_one('#founder_content') or \
                      soup.select_one('.article-content') or \
                      soup.select_one('div[class*="content"]')
                      
        if content_div:
            # Remove scripts and styles
            for script in content_div(["script", "style"]):
                script.decompose()
            
            # Remove elements that look like print buttons
            for bad in content_div.select('.print, .print-btn'):
                bad.decompose()
                
            original_html = str(content_div)
            
            # Extract text paragraphs for translation
            paragraphs = [p.get_text(strip=True) for p in content_div.find_all('p') if p.get_text(strip=True)]
            
            # Translate paragraphs concurrently
            translated_paragraphs = []
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(GoogleTranslator(source='zh-CN', target='ko').translate, p) for p in paragraphs]
                for f in futures:
                    try:
                        translated_paragraphs.append(f.result())
                    except Exception as e:
                        print(f"Translation error: {e}")
                        translated_paragraphs.append("[Translation Failed]")
            
            result = {
                'status': 'success',
                'content_cn': original_html,
                'content_ko': translated_paragraphs
            }
            
            # Store in cache
            ARTICLE_CACHE[url] = result
            return result
            
    except Exception as e:
        print(f"Error fetching article {url}: {e}")
        return None
        
    return None

@app.route('/selection')
def selection_page():
    return render_template('selection.html')

@app.route('/guangxi')
def guangxi_page():
    return render_template('guangxi.html')

@app.route('/api/selection')
def get_selection():
    # Return list of starred items
    items = list(STARRED_ITEMS.values())
    return jsonify({'status': 'success', 'data': items})

@app.route('/api/article')
def get_article():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
        
    # Check cache first
    if url in ARTICLE_CACHE:
        return jsonify(ARTICLE_CACHE[url])
        
    result = fetch_and_translate_article_logic(url)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Failed to fetch article'}), 500



@app.route('/api/star', methods=['POST'])
def toggle_star():
    data = request.json
    url = data.get('url')
    starred = data.get('starred')
    item_data = data.get('item') # Receive full item data
    
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
        
    if starred:
        if item_data:
            item_data['starred'] = True
            STARRED_ITEMS[url] = item_data
            
        # Trigger background fetch
        thread = threading.Thread(target=fetch_and_translate_article_logic, args=(url,))
        thread.start()
        return jsonify({'status': 'success', 'message': 'Added to selection and fetching started'})
    else:
        if url in STARRED_ITEMS:
            del STARRED_ITEMS[url]
        
        # Optional: Remove from cache if unstarred? 
        # Keeping in cache for now as per previous decision
        return jsonify({'status': 'success', 'message': 'Removed from selection'})

@app.route('/api/news/<source_key>')
def get_news(source_key):
    date_str = request.args.get('date')
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    else:
        current_date = datetime.now()

    dates = {
        'yyyymm': current_date.strftime('%Y%m'),
        'yyyy-mm': current_date.strftime('%Y-%m'),
        'dd': current_date.strftime('%d'),
        'date_path': current_date.strftime('%Y%m/%d')
    }
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
    
    try:
        all_news_items = []
        source_name = ""
        pages_to_fetch = [] # List of (url, section_name)
        
        if source_key == 'fujian':
            source_name = "福建日报"
            root_url = f"https://fjrb.fjdaily.com/pc/col/{dates['date_path']}/"
            start_url = f"{root_url}node_01.html"
            
            # 1. Fetch first page to get the list of pages
            resp = session.get(start_url, timeout=10)
            if resp.status_code == 404:
                 return jsonify({'source': source_name, 'status': 'success', 'data': []})
                 
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Parse Page Navigation (#bmdhTable)
            page_links = soup.select('#bmdhTable .rigth_bmdh_href')
            
            # If no navigation found, fallback to just the start page
            if not page_links:
                pages_to_fetch.append((start_url, "01 要闻"))
            else:
                for link in page_links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    if href:
                        abs_url = urllib.parse.urljoin(root_url, href)
                        pages_to_fetch.append((abs_url, text))

        elif source_key == 'hainan':
            source_name = "海南日报"
            root_url = f"http://news.hndaily.cn/html/{dates['yyyy-mm']}/{dates['dd']}/"
            start_url = f"{root_url}node_1.htm"
            
            resp = session.get(start_url, timeout=10)
            if resp.status_code == 404:
                 return jsonify({'source': source_name, 'status': 'success', 'data': []})

            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Parse Page Navigation (#bmdhTable a)
            page_links = soup.select('#bmdhTable a')
            
            if not page_links:
                 pages_to_fetch.append((start_url, "第01版"))
            else:
                for link in page_links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    # Filter out PDF links or non-page links if any
                    if href and 'node' in href and not href.endswith('.pdf'):
                        abs_url = urllib.parse.urljoin(root_url, href)
                        pages_to_fetch.append((abs_url, text))

        elif source_key == 'nanfang':
            source_name = "南方日报"
            # Date format: YYYYMM/DD (e.g., 202511/21)
            date_param = date_str.replace('-', '') if date_str else current_date.strftime('%Y%m/%d')
            # Insert slash after YYYYMM
            if len(date_param) == 8:  # YYYYMMDD
                date_param = date_param[:6] + '/' + date_param[6:]
            
            root_url = f"https://epaper.southcn.com/nfdaily/html/{date_param}/"
            
            # Try sections A01-A12
            for section_num in range(1, 13):
                section_code = f"A{section_num:02d}"
                section_url = f"{root_url}node_{section_code}.html"
                
                try:
                    resp = session.get(section_url, timeout=10)
                    if resp.status_code == 404:
                        continue
                    
                    resp.encoding = 'utf-8'
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # Find section name
                    section_name = f"第{section_code}版"
                    
                    # Find article links with href containing 'content_'
                    article_links = soup.select('a[href*="content_"]')
                    
                    for link in article_links:
                        title = link.get_text(strip=True)
                        href = link.get('href')
                        
                        if href and title and len(title) > 3:
                            # Article URLs use different domain
                            if href.startswith('http'):
                                abs_link = href
                            else:
                                abs_link = f"https://epaper.nfnews.com/nfdaily/html/{date_param}/{href}"
                            
                            # Translate title
                            title_ko = translate_text(title)
                            
                            all_news_items.append({
                                'title': title,
                                'title_ko': title_ko,
                                'link': abs_link,
                                'section': section_name
                            })
                except Exception as e:
                    logging.error(f"Error fetching Nanfang section {section_code}: {e}")
                    continue

        elif source_key == 'guangzhou':
            source_name = "广州日报"
            # Date format: YYYY-MM/DD (e.g., 2025-11/21)
            date_param = date_str if date_str else current_date.strftime('%Y-%m/%d')
            # Ensure format is YYYY-MM/DD
            if '-' in date_param and '/' not in date_param:
                parts = date_param.split('-')
                if len(parts) == 3:
                    date_param = f"{parts[0]}-{parts[1]}/{parts[2]}"
            
            root_url = f"https://gzdaily.dayoo.com/pc/html/{date_param}/"
            
            # Use index page to get all articles (more reliable than checking individual sections)
            # Format: index_YYYY-MM-DD.htm
            index_date = date_param.replace('/', '-')  # Convert 2025-11/21 to 2025-11-21
            index_url = f"{root_url}index_{index_date}.htm"
            
            try:
                resp = session.get(index_url, timeout=10)
                if resp.status_code == 404:
                    logging.info(f"Guangzhou Daily index not found for {index_date}")
                else:
                    resp.encoding = 'utf-8'
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    
                    # Find all section divs with class 'bc'
                    section_divs = soup.select('div.bc a[href*="node_"]')
                    
                    # Build a map of section URLs to section names
                    section_map = {}
                    for section_link in section_divs:
                        section_href = section_link.get('href')
                        section_text = section_link.get_text(strip=True)
                        if section_href:
                            section_map[section_href] = section_text
                    
                    logging.info(f"Found {len(section_map)} sections in Guangzhou Daily")
                    
                    # Now fetch each section page to get article titles
                    for section_href, section_name in section_map.items():
                        section_url = urllib.parse.urljoin(root_url, section_href)
                        
                        try:
                            section_resp = session.get(section_url, timeout=10)
                            if section_resp.status_code != 200:
                                continue
                            
                            section_resp.encoding = 'utf-8'
                            section_soup = BeautifulSoup(section_resp.text, 'html.parser')
                            
                            # Find article areas with data-title attribute
                            article_areas = section_soup.select('area[data-title]')
                            
                            for area in article_areas:
                                title = area.get('data-title', '').strip()
                                href = area.get('href')
                                
                                if href and title and len(title) > 3:
                                    # Build absolute URL
                                    if href.startswith('http'):
                                        abs_link = href
                                    else:
                                        abs_link = urllib.parse.urljoin(root_url, href)
                                    
                                    # Translate title
                                    title_ko = translate_text(title)
                                    
                                    all_news_items.append({
                                        'title': title,
                                        'title_ko': title_ko,
                                        'link': abs_link,
                                        'section': section_name
                                    })
                        except Exception as e:
                            logging.error(f"Error fetching Guangzhou section {section_href}: {e}")
                            continue
                    
                    logging.info(f"Guangzhou Daily: found {len(all_news_items)} articles")
                    
            except Exception as e:
                logging.error(f"Error fetching Guangzhou Daily index: {e}")

        elif source_key == 'guangxi':
            source_name = "广西日报"
            base_url = "https://gxrb.gxrb.com.cn/"
            date_param = date_str if date_str else current_date.strftime('%Y-%m-%d')
            
            # Guangxi Daily: Fetch individual articles using Playwright
            # URL pattern: ?name=gxrb&date=YYYY-MM-DD&code=XXX&xuhao=N
            # code: section (001-009), xuhao: article number (1-10)
            
            logging.info(f"Fetching Guangxi Daily for date: {date_param}")
            
            for section_num in range(1, 10):  # Sections 001-009
                code = f"{section_num:03d}"
                section_name = f"第{code}版"
                
                articles_found_in_section = 0
                consecutive_failures = 0
                
                for article_num in range(1, 11):  # Articles 1-10 per section
                    article_url = f"{base_url}?name=gxrb&date={date_param}&code={code}&xuhao={article_num}"
                    
                    try:
                        logging.info(f"Fetching article: {code}-{article_num}")
                        article_data = fetch_guangxi_article_with_playwright(article_url)
                        
                        if not article_data or not article_data.get('title'):
                            # No article found at this position
                            consecutive_failures += 1
                            logging.info(f"No article found at {code}-{article_num}")
                            
                            # If we've had 3 consecutive failures, assume no more articles in this section
                            if consecutive_failures >= 3:
                                logging.info(f"3 consecutive failures in section {code}, moving to next section")
                                break
                            continue
                        
                        # Reset consecutive failures counter
                        consecutive_failures = 0
                        
                        title = article_data['title']
                        
                        # Skip if title is too short or looks like navigation
                        if len(title) < 5:
                            logging.info(f"Skipping article {code}-{article_num}: title too short")
                            continue
                        
                        # Translate title
                        title_ko = translate_text(title)
                        
                        all_news_items.append({
                            'title': title,
                            'title_ko': title_ko,
                            'link': article_url,
                            'section': section_name
                        })
                        
                        articles_found_in_section += 1
                        logging.info(f"Successfully added article {code}-{article_num}: {title[:50]}...")
                        
                    except Exception as e:
                        logging.error(f"Error fetching Guangxi article {code}-{article_num}: {e}")
                        consecutive_failures += 1
                        # Continue trying other articles even if one fails
                        if consecutive_failures >= 3:
                            logging.info(f"Too many errors in section {code}, moving to next section")
                            break
                        continue
                
                logging.info(f"Section {code} complete: found {articles_found_in_section} articles")
                
                # Don't break - continue checking all sections even if some are empty
                # Some sections might be empty but later sections could have content
            
            logging.info(f"Guangxi Daily scraping complete: total {len(all_news_items)} articles found")

        else:
            return jsonify({'error': 'Invalid source'}), 400
            
        # 2. Fetch all pages concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(fetch_page_items, session, url, source_type=source_key, section_name=section): url for url, section in pages_to_fetch}
            for future in as_completed(future_to_url):
                items = future.result()
                all_news_items.extend(items)
        
        # Sort by section to maintain order (01, 02, 03...)
        all_news_items.sort(key=lambda x: x.get('section', ''))
        
        # Mark starred items
        for item in all_news_items:
            item['starred'] = item['link'] in STARRED_ITEMS
        
        return jsonify({
            'source': source_name,
            'status': 'success',
            'data': all_news_items
        })

    except Exception as e:
        logging.error(f"Error fetching {source_key}: {e}")
        return jsonify({'error': str(e)}), 500



# if __name__ == '__main__':
#     app.run(debug=True, port=5001)
