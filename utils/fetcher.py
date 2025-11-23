"""
Unified HTML fetcher with browser-like headers and JS redirect handling.
"""
import time
import random
import re
from urllib.parse import urljoin
import requests
import logging

logger = logging.getLogger(__name__)

# Create a session with browser-like headers
session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
})


def fetch_html(url: str, max_js_redirect: int = 2) -> str:
    """
    Universal HTML fetcher with:
    - Browser User-Agent and headers
    - Proper encoding handling (fixes 乱码 issues)
    - Simple rate limiting
    - Common JS redirect handling (window.location.href)
    
    Args:
        url: The URL to fetch
        max_js_redirect: Maximum number of JS redirects to follow
        
    Returns:
        The HTML content as a string with correct encoding
    """
    for redirect_count in range(max_js_redirect):
        # Light rate limiting to avoid bot detection
        time.sleep(random.uniform(0.5, 1.2))
        
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            
            # CRITICAL: Fix encoding to avoid 乱码
            # If encoding is None or ISO-8859-1 (default fallback), use apparent_encoding
            if resp.encoding is None or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding or "utf-8"
            
            text = resp.text
            
            # Log first part of content for debugging (only on first fetch)
            if redirect_count == 0:
                logger.debug(f"Fetched URL: {url}, encoding: {resp.encoding}, first 200 chars: {text[:200]!r}")
            
            # Handle simple JS redirect: window.location.href = 'xxx'
            m = re.search(r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", text)
            if m:
                next_url = urljoin(url, m.group(1))
                logger.info(f"Following JS redirect to: {next_url}")
                url = next_url
                continue
            
            # Handle: var loc = 'xxx'; location.href = loc;
            m2 = re.search(r"loc\s*=\s*['\"]([^'\"]+)['\"]", text)
            if m2 and "location.href" in text:
                next_url = urljoin(url, m2.group(1))
                logger.info(f"Following JS redirect (loc var) to: {next_url}")
                url = next_url
                continue
            
            return text
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    # Return last fetched content if max redirects reached
    logger.warning(f"Max JS redirects ({max_js_redirect}) reached for {url}")
    return text
