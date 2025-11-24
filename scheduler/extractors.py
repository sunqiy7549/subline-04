"""Content extraction using newspaper3k with BeautifulSoup fallback."""
import logging
from newspaper import Article
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Smart content extractor using newspaper3k with BeautifulSoup fallback."""
    
    def __init__(self, language='zh'):
        """
        Initialize extractor.
        
        Args:
            language: Language code for newspaper3k (default: 'zh' for Chinese)
        """
        self.language = language
    
    def extract_from_url(self, url, timeout=10):
        """
        Extract article content from URL using newspaper3k.
        Falls back to BeautifulSoup if newspaper3k fails.
        
        Args:
            url: Article URL
            timeout: Request timeout in seconds
        
        Returns:
            Dict with extracted data: {
                'title': str,
                'text': str,
                'preview': str (first 200 chars),
                'method': 'newspaper3k' or 'beautifulsoup'
            }
        """
        # Try newspaper3k first
        try:
            article_data = self._extract_with_newspaper(url, timeout)
            article_data['method'] = 'newspaper3k'
            logger.info(f"✓ Extracted with newspaper3k: {url[:50]}...")
            return article_data
        except Exception as e:
            logger.warning(f"newspaper3k failed for {url[:50]}...: {e}")
        
        # Fallback to BeautifulSoup
        try:
            article_data = self._extract_with_beautifulsoup(url, timeout)
            article_data['method'] = 'beautifulsoup'
            logger.info(f"✓ Extracted with BeautifulSoup fallback: {url[:50]}...")
            return article_data
        except Exception as e:
            logger.error(f"✗ Both extraction methods failed for {url}: {e}")
            return {
                'title': '',
                'text': '',
                'preview': '',
                'method': 'failed'
            }
    
    def _extract_with_newspaper(self, url, timeout):
        """Extract using newspaper3k library."""
        article = Article(url, language=self.language)
        article.download()
        article.parse()
        
        title = article.title or ''
        text = article.text or ''
        preview = text[:200] if text else ''
        
        return {
            'title': title.strip(),
            'text': text.strip(),
            'preview': preview.strip()
        }
    
    def _extract_with_beautifulsoup(self, url, timeout):
        """Fallback extraction using BeautifulSoup (basic implementation)."""
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find title
        title = ''
        title_tag = soup.find('h1') or soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        
        # Try to extract main content (basic heuristic)
        # Look for common content containers
        content_div = (
            soup.find('div', class_='content') or
            soup.find('div', class_='article') or
            soup.find('article') or
            soup.find('div', id='content')
        )
        
        text = ''
        if content_div:
            # Extract paragraphs
            paragraphs = content_div.find_all('p')
            text = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        preview = text[:200] if text else ''
        
        return {
            'title': title.strip(),
            'text': text.strip(),
            'preview': preview.strip()
        }


# Singleton instance
extractor = ContentExtractor(language='zh')


def extract_article(url, timeout=10):
    """
    Convenience function to extract article content.
    
    Args:
        url: Article URL
        timeout: Request timeout
    
    Returns:
        Dict with article data
    """
    return extractor.extract_from_url(url, timeout)
