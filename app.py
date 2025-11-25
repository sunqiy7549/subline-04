import sys
import os
from flask import Flask, render_template, jsonify, request
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import urllib.parse
import re
import threading
from queue import Queue
from enum import Enum

# Initialize Flask app
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'))
else:
    app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database and scheduler
from database import init_db, get_articles_by_date, get_stats
from scheduler.scheduler import init_scheduler, shutdown_scheduler, get_next_run_times

# Initialize database on startup
logger.info("Initializing database...")
init_db()
logger.info("✓ Database ready")

# Initialize scheduler on startup
logger.info("Initializing background scheduler...")
init_scheduler()
logger.info("✓ Scheduler ready")

# Register cleanup on shutdown
import atexit
atexit.register(shutdown_scheduler)

# ============ 状态管理系统 ============
class CrawlState(Enum):
    """爬取任务状态"""
    IDLE = "idle"              # 空闲
    RUNNING = "running"        # 运行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败

class SourceCrawlStatus:
    """单个数据源的爬取状态"""
    def __init__(self, source_key):
        self.source_key = source_key
        self.state = CrawlState.IDLE
        self.progress = 0  # 0-100
        self.logs = []  # 日志队列
        self.total_articles = 0
        self.start_time = None
        self.end_time = None
    
    def add_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        # 只保留最后100条日志
        if len(self.logs) > 100:
            self.logs.pop(0)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'source_key': self.source_key,
            'state': self.state.value,
            'progress': self.progress,
            'logs': self.logs[-20:],  # 返回最后20条日志
            'total_articles': self.total_articles,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

# 全局爬取状态管理
CRAWL_STATUS = {
    'fujian': SourceCrawlStatus('fujian'),
    'hainan': SourceCrawlStatus('hainan'),
    'nanfang': SourceCrawlStatus('nanfang'),
    'guangzhou': SourceCrawlStatus('guangzhou'),
    'guangxi': SourceCrawlStatus('guangxi')
}

CRAWL_LOCK = threading.Lock()  # 保证线程安全


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

def get_current_date_strs():
    now = datetime.now()
    return {
        'yyyymm': now.strftime('%Y%m'),
        'yyyy-mm': now.strftime('%Y-%m'),
        'dd': now.strftime('%d'),
        'date_path': now.strftime('%Y%m/%d')
    }

@app.route('/')
def index():
    return render_template('index.html')

# ============ 状态管理API ============

@app.route('/api/crawl/status/<source_key>')
def get_crawl_status(source_key):
    """获取指定数据源的爬取状态"""
    if source_key not in CRAWL_STATUS:
        return jsonify({'error': 'Invalid source'}), 400
    
    status = CRAWL_STATUS[source_key]
    return jsonify(status.to_dict())

@app.route('/api/crawl/status/all')
def get_all_crawl_status():
    """获取所有数据源的爬取状态"""
    return jsonify({
        source_key: status.to_dict()
        for source_key, status in CRAWL_STATUS.items()
    })

@app.route('/api/crawl/start/<source_key>', methods=['POST'])
def start_crawl(source_key):
    """手动启动某个数据源的爬取"""
    if source_key not in CRAWL_STATUS:
        return jsonify({'error': 'Invalid source'}), 400
    
    date_str = request.json.get('date') if request.json else None
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    status = CRAWL_STATUS[source_key]
    
    # 如果已在运行，返回错误
    if status.state == CrawlState.RUNNING:
        return jsonify({'error': 'Crawl already running'}), 400
    
    # 在后台线程启动爬取
    thread = threading.Thread(
        target=_crawl_source_background,
        args=(source_key, date_str),
        daemon=True
    )
    thread.start()
    
    return jsonify({'status': 'success', 'message': f'Crawl started for {source_key}'})

def _crawl_source_background(source_key, date_str):
    """后台爬取任务"""
    status = CRAWL_STATUS[source_key]
    
    with CRAWL_LOCK:
        status.state = CrawlState.RUNNING
        status.start_time = datetime.now()
        status.logs.clear()
        status.total_articles = 0
        status.add_log(f"Starting crawl for {date_str}")
    
    # 在应用上下文中执行爬取
    with app.app_context():
        try:
            # 调用爬取逻辑
            current_date = datetime.strptime(date_str, '%Y-%m-%d')
            result = _perform_crawl(source_key, current_date, date_str, status)
            
            with CRAWL_LOCK:
                status.total_articles = result.get('count', 0)
                status.state = CrawlState.COMPLETED
                status.progress = 100
                status.end_time = datetime.now()
                status.add_log(f"✓ Crawl completed: {result.get('count', 0)} articles")
        
        except Exception as e:
            with CRAWL_LOCK:
                status.state = CrawlState.FAILED
                status.end_time = datetime.now()
                status.add_log(f"✗ Crawl failed: {str(e)}")
                logger.error(f"Crawl error for {source_key}: {e}")

from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator
import threading
from playwright.sync_api import sync_playwright

# Import new fetcher and URL generators
from utils.fetcher import fetch_html
from sources.gzdaily import gzdaily_index_url, gzdaily_section_url
from sources.nfdaily import nfdaily_section_url, nfdaily_article_url
from sources.nanfang_live import fetch_nanfang_articles

def translate_text(text, target='ko'):
    """
    暂时关闭后端翻译，直接返回原文，避免外网访问导致 worker 超时。
    以后如果要恢复翻译，可以在这里换成别的实现（比如 OpenAI API）。
    """
    # Translation disabled to prevent timeout issues
    # logger.debug("Translation disabled, returning original text")
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
            # Translation disabled - return original paragraphs
            content_paragraphs = article_data.get('content', [])
            translated_paragraphs = content_paragraphs  # No translation
            
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

                # Translation disabled - return original paragraphs
                translated_paragraphs = paragraphs  # No translation
                
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
            # Translation disabled - return original paragraphs
            translated_paragraphs = paragraphs  # No translation
            
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

def _perform_crawl(source_key, current_date, date_str, status):
    """
    执行爬取任务，返回结果字典
    """
    try:
        # 直接调用 get_news_realtime 处理爬取
        response = get_news_realtime(source_key, current_date, date_str, status)
        
        # 如果返回的是 Response 对象，获取 JSON 数据
        if hasattr(response, 'get_json'):
            response_data = response.get_json()
        else:
            response_data = response
        
        if response_data.get('status') != 'success':
            return {'count': 0, 'error': response_data.get('error', 'Unknown error')}
        
        articles = response_data.get('data', [])
        
        # 保存到数据库
        if articles:
            from database.db import save_articles
            success_count, error_count = save_articles(articles, source_key, date_str)
            status.add_log(f"Saved {success_count} articles to database")
            return {'count': success_count}
        
        return {'count': 0}
        
    except Exception as e:
        status.add_log(f"Error during crawl: {str(e)}")
        logger.error(f"Crawl error: {e}")
        return {'count': 0, 'error': str(e)}
    
    return {'count': 0}

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
    """
    Get news for a source with status tracking.
    
    Response states:
    1. 'loaded' - News available from database/cache
    2. 'loading' - Currently crawling, show progress
    3. 'empty' - No news available and not crawling, show fetch button
    """
    date_str = request.args.get('date')
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    else:
        current_date = datetime.now()
        date_str = current_date.strftime('%Y-%m-%d')
    
    if source_key not in CRAWL_STATUS:
        return jsonify({'error': 'Invalid source'}), 400
    
    status = CRAWL_STATUS[source_key]
    
    source_names = {
        'fujian': '福建日报',
        'hainan': '海南日报',
        'nanfang': '南方日报',
        'guangzhou': '广州日报',
        'guangxi': '广西日报'
    }
    
    # Try to get from database first
    try:
        articles = get_articles_by_date(source_key=source_key, date_str=date_str)
        
        if articles and len(articles) > 0:
            # Found data in database - return loaded state
            logger.info(f"[{source_key}] Serving {len(articles)} articles from database for {date_str}")
            
            # Convert to dict format
            articles_data = [article.to_dict() for article in articles]
            
            # Mark starred items
            for item in articles_data:
                item['starred'] = item['link'] in STARRED_ITEMS
            
            return jsonify({
                'source': source_names.get(source_key, source_key),
                'status': 'loaded',
                'crawl_status': status.to_dict(),
                'data': articles_data
            })
        else:
            # No data in database
            if status.state == CrawlState.RUNNING:
                # Currently crawling - return loading state with progress
                logger.info(f"[{source_key}] Currently crawling...")
                return jsonify({
                    'source': source_names.get(source_key, source_key),
                    'status': 'loading',
                    'crawl_status': status.to_dict(),
                    'data': []
                })
            else:
                # Not crawling and no data - return empty state with fetch button
                logger.info(f"[{source_key}] No cached data, allow manual fetch")
                return jsonify({
                    'source': source_names.get(source_key, source_key),
                    'status': 'empty',
                    'crawl_status': status.to_dict(),
                    'data': []
                })
            
    except Exception as e:
        logger.error(f"[{source_key}] Database error: {e}")
        # Return empty state if database error
        return jsonify({
            'source': source_names.get(source_key, source_key),
            'status': 'empty',
            'crawl_status': status.to_dict(),
            'error': str(e),
            'data': []
        })


def get_news_realtime(source_key, current_date, date_str, status=None):
    """Original real-time crawling logic (fallback when DB is empty).
    
    Args:
        source_key: Source identifier
        current_date: datetime object
        date_str: Date string in YYYY-MM-DD format
        status: Optional SourceCrawlStatus object for tracking progress
    """
    dates = {
        'yyyymm': current_date.strftime('%Y%m'),
        'yyyy-mm': current_date.strftime('%Y-%m'),
        'dd': current_date.strftime('%d'),
        'date_path': current_date.strftime('%Y%m/%d')
    }
    
    def log_message(msg):
        """Helper to log both to logger and status"""
        logger.info(f"[{source_key}] {msg}")
        if status:
            status.add_log(msg)
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'})
    
    try:
        all_news_items = []
        source_name = ""
        pages_to_fetch = [] # List of (url, section_name)
        
        if source_key == 'fujian':
            source_name = "福建日报"
            log_message(f"Starting to crawl Fujian Daily for {date_str}")
            root_url = f"https://fjrb.fjdaily.com/pc/col/{dates['date_path']}/"
            start_url = f"{root_url}node_01.html"
            
            # 1. Fetch first page to get the list of pages
            resp = session.get(start_url, timeout=10)
            if resp.status_code == 404:
                 log_message("No data available for this date (404)")
                 return {'source': source_name, 'status': 'success', 'data': []}
                 
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Parse Page Navigation (#bmdhTable)
            page_links = soup.select('#bmdhTable .rigth_bmdh_href')
            
            # If no navigation found, fallback to just the start page
            if not page_links:
                pages_to_fetch.append((start_url, "01 要闻"))
                log_message("Found 1 page")
            else:
                for link in page_links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    if href:
                        abs_url = urllib.parse.urljoin(root_url, href)
                        pages_to_fetch.append((abs_url, text))
                log_message(f"Found {len(pages_to_fetch)} pages")

        elif source_key == 'hainan':
            source_name = "海南日报"
            log_message(f"Starting to crawl Hainan Daily for {date_str}")
            root_url = f"http://news.hndaily.cn/html/{dates['yyyy-mm']}/{dates['dd']}/"
            start_url = f"{root_url}node_1.htm"
            
            resp = session.get(start_url, timeout=10)
            if resp.status_code == 404:
                 log_message("No data available for this date (404)")
                 return {'source': source_name, 'status': 'success', 'data': []}

            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Parse Page Navigation (#bmdhTable a)
            page_links = soup.select('#bmdhTable a')
            
            if not page_links:
                 pages_to_fetch.append((start_url, "第01版"))
                 log_message("Found 1 page")
            else:
                for link in page_links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    # Filter out PDF links or non-page links if any
                    if href and 'node' in href and not href.endswith('.pdf'):
                        abs_url = urllib.parse.urljoin(root_url, href)
                        pages_to_fetch.append((abs_url, text))
                log_message(f"Found {len(pages_to_fetch)} pages")

        elif source_key == 'nanfang':
            source_name = "南方日报"
            log_message(f"Starting to crawl Nanfang Daily for {date_str}")
            
            try:
                # Use the verified parser from nanfang_live module
                log_message("Fetching sections A01-A08...")
                
                # Fetch core sections A01-A08 (要闻/广东/时政等主版面)
                # A09/A10 are mostly supplements/ads and can cause SSL timeout issues
                for section_num in range(1, 9):  # A01 through A08
                    section_code = f"A{section_num:02d}"
                    
                    try:
                        # Use the verified fetch_nanfang_articles function
                        raw_articles = fetch_nanfang_articles(current_date, section=section_code)
                        
                        # DEBUG: Log results for A01
                        if section_code == "A01":
                            log_message(f"Section {section_code}: found {len(raw_articles)} articles")
                        
                        # Convert to our format and translate
                        section_name = f"第{section_code}版"
                        for item in raw_articles:
                            title = item['title']
                            url = item['url']
                            
                            # Translate title
                            title_ko = translate_text(title)
                            
                            all_news_items.append({
                                'title': title,
                                'title_ko': title_ko,
                                'link': url,
                                'section': section_name
                            })
                    except Exception as e:
                        # 404 is expected for non-existent sections
                        if "404" not in str(e):
                            log_message(f"Error in section {section_code}: {str(e)[:50]}")
                        continue
                
                log_message(f"✓ Completed: {len(all_news_items)} articles found")
                
            except Exception as e:
                log_message(f"✗ Crawl error: {str(e)[:100]}")

        elif source_key == 'guangzhou':
            source_name = "广州日报"
            log_message(f"Starting to crawl Guangzhou Daily for {date_str}")
            
            try:
                # Use PC version index - this is the stable, pure HTML page
                index_url = gzdaily_index_url(current_date)
                log_message("Fetching index...")
                
                html = fetch_html(index_url)
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # PC version structure: find section links
                # Look for links to section pages (node_XXX.htm)
                section_links = soup.select('a[href*="node_"]')
                
                # Build a map of section URLs to section names
                section_map = {}
                for section_link in section_links:
                    section_href = section_link.get('href')
                    section_text = section_link.get_text(strip=True)
                    if section_href and 'node_' in section_href:
                        # Build absolute URL
                        if section_href.startswith('http'):
                            abs_url = section_href
                        else:
                            # For PC version, construct the full path
                            date_path = current_date.strftime("%Y-%m/%d")
                            abs_url = f"https://gzdaily.dayoo.com/pc/html/{date_path}/{section_href}"
                        section_map[abs_url] = section_text if section_text else "未知版面"
                
                log_message(f"Found {len(section_map)} sections")
                
                # Now fetch each section page to get article titles
                for section_url, section_name in section_map.items():
                    try:
                        section_html = fetch_html(section_url)
                        section_soup = BeautifulSoup(section_html, 'html.parser')
                        
                        # Find article links - PC version uses area tags with data-title
                        article_areas = section_soup.select('area[data-title]')
                        
                        for area in article_areas:
                            title = area.get('data-title', '').strip()
                            href = area.get('href')
                            
                            if href and title and len(title) > 3:
                                # Build absolute URL
                                if href.startswith('http'):
                                    abs_link = href
                                else:
                                    date_path = current_date.strftime("%Y-%m/%d")
                                    abs_link = f"https://gzdaily.dayoo.com/pc/html/{date_path}/{href}"
                                
                                # Translate title
                                title_ko = translate_text(title)
                                
                                all_news_items.append({
                                    'title': title,
                                    'title_ko': title_ko,
                                    'link': abs_link,
                                    'section': section_name
                                })
                    except Exception as e:
                        log_message(f"Error in section: {str(e)[:50]}")
                        continue
                
                log_message(f"✓ Completed: {len(all_news_items)} articles found")
                
            except Exception as e:
                log_message(f"✗ Crawl error: {str(e)[:100]}")

        elif source_key == 'guangxi':
            source_name = "广西日报"
            base_url = "https://gxrb.gxrb.com.cn/"
            date_param = date_str if date_str else current_date.strftime('%Y-%m-%d')
            
            log_message(f"Starting to crawl Guangxi Daily for {date_param}")
            
            # Guangxi Daily: Fetch individual articles using Playwright
            # URL pattern: ?name=gxrb&date=YYYY-MM-DD&code=XXX&xuhao=N
            # code: section (001-009), xuhao: article number (1-10)
            
            for section_num in range(1, 10):  # Sections 001-009
                code = f"{section_num:03d}"
                section_name = f"第{code}版"
                
                articles_found_in_section = 0
                consecutive_failures = 0
                
                log_message(f"Fetching section {code}...")
                
                for article_num in range(1, 11):  # Articles 1-10 per section
                    article_url = f"{base_url}?name=gxrb&date={date_param}&code={code}&xuhao={article_num}"
                    
                    try:
                        article_data = fetch_guangxi_article_with_playwright(article_url)
                        
                        if not article_data or not article_data.get('title'):
                            # No article found at this position
                            consecutive_failures += 1
                            
                            # If we've had 3 consecutive failures, assume no more articles in this section
                            if consecutive_failures >= 3:
                                log_message(f"No more articles in section {code}")
                                break
                            continue
                        
                        # Reset consecutive failures counter
                        consecutive_failures = 0
                        
                        title = article_data['title']
                        
                        # Skip if title is too short or looks like navigation
                        if len(title) < 5:
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
                        
                    except Exception as e:
                        log_message(f"Error in article: {str(e)[:50]}")
                        consecutive_failures += 1
                        # Continue trying other articles even if one fails
                        if consecutive_failures >= 3:
                            log_message(f"Too many errors in section {code}")
                            break
                        continue
                
                if articles_found_in_section > 0:
                    log_message(f"Section {code}: {articles_found_in_section} articles")
                
                # Don't break - continue checking all sections even if some are empty
                # Some sections might be empty but later sections could have content
            
            log_message(f"✓ Completed: {len(all_news_items)} articles found")

        else:
            return {'error': 'Invalid source'}
            
        # 2. Fetch all pages concurrently
        log_message(f"Fetching {len(pages_to_fetch)} pages with articles...")
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
        
        return {
            'source': source_name,
            'status': 'success',
            'cached': False,
            'data': all_news_items
        }

    except Exception as e:
        logging.error(f"Error fetching {source_key}: {e}")
        return {'error': str(e)}


# Admin API endpoints
@app.route('/api/admin/scheduler/status')
def scheduler_status():
    """Get scheduler status and next run times."""
    try:
        next_runs = get_next_run_times()
        stats = get_stats()
        
        return jsonify({
            'status': 'success',
            'scheduler': {
                'active': True,
                'next_runs': next_runs
            },
            'database': stats
        })
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/trigger/<job_id>', methods=['POST'])
def trigger_job(job_id):
    """Manually trigger a scheduled job."""
    from scheduler.scheduler import trigger_job_now
    
    try:
        success = trigger_job_now(job_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Job {job_id} triggered successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to trigger job {job_id}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error triggering job {job_id}: {e}")
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True, port=5001)
