"""Crawling job functions for background scheduler."""
import logging
from datetime import datetime
from database import save_articles, cleanup_old_articles

logger = logging.getLogger(__name__)


def crawl_source_job(source_key):
    """
    Crawl a news source and save to database.
    
    Args:
        source_key: Source identifier (e.g., 'fujian', 'hainan', etc.)
    
    Returns:
        Dictionary with crawl results
    """
    # Import here to avoid circular dependency
    from app import get_news_realtime
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    current_date = datetime.now()
    
    logger.info(f"[{source_key}] Starting scheduled crawl for {date_str}")
    
    try:
        # Call the real-time crawler
        response = get_news_realtime(source_key, current_date, date_str)
        
        # Extract data from JSON response
        response_data = response.get_json()
        
        if response_data['status'] != 'success':
            logger.error(f"[{source_key}] Crawl returned error status")
            return {
                'source': source_key,
                'date': date_str,
                'success': False,
                'error': 'Crawl returned error status'
            }
        
        articles = response_data.get('data', [])
        
        if not articles:
            logger.warning(f"[{source_key}] No articles found for {date_str}")
            return {
                'source': source_key,
                'date': date_str,
                'success': True,
                'article_count': 0,
                'errors': 0
            }
        
        # Save to database
        success_count, error_count = save_articles(articles, source_key, date_str)
        
        logger.info(f"[{source_key}] ✓ Saved {success_count} articles, {error_count} errors")
        
        return {
            'source': source_key,
            'date': date_str,
            'success': True,
            'article_count': success_count,
            'errors': error_count
        }
        
    except Exception as e:
        logger.error(f"[{source_key}] ✗ Crawl failed: {e}")
        return {
            'source': source_key,
            'date': date_str,
            'success': False,
            'error': str(e)
        }


def crawl_fujian_job():
    """Crawl Fujian Daily and save to database."""
    return crawl_source_job('fujian')


def crawl_hainan_job():
    """Crawl Hainan Daily and save to database."""
    return crawl_source_job('hainan')


def crawl_nanfang_job():
    """Crawl Nanfang Daily and save to database."""
    return crawl_source_job('nanfang')


def crawl_guangzhou_job():
    """Crawl Guangzhou Daily and save to database."""
    return crawl_source_job('guangzhou')


def crawl_guangxi_job():
    """Crawl Guangxi Daily and save to database (slow, ~30-40 mins)."""
    logger.info("[guangxi] Starting SLOW crawl (30-40 mins expected)")
    return crawl_source_job('guangxi')


def crawl_all_fast_sources():
    """Crawl all fast sources (Fujian, Hainan, Nanfang, Guangzhou)."""
    logger.info("=" * 60)
    logger.info("Starting scheduled crawl for FAST sources")
    logger.info("=" * 60)
    
    results = []
    
    # Crawl each fast source
    for job_func, name in [
        (crawl_fujian_job, 'Fujian Daily'),
        (crawl_hainan_job, 'Hainan Daily'),
        (crawl_nanfang_job, 'Nanfang Daily'),
        (crawl_guangzhou_job, 'Guangzhou Daily'),
    ]:
        logger.info(f"\n>>> Crawling {name}...")
        result = job_func()
        results.append(result)
        
        if result['success']:
            logger.info(f"✓ {name}: {result['article_count']} articles")
        else:
            logger.error(f"✗ {name}: {result.get('error', 'Unknown error')}")
    
    # Summary
    total_articles = sum(r['article_count'] for r in results if r['success'])
    logger.info(f"\n{' =' * 60}")
    logger.info(f"Fast sources crawl complete: {total_articles} total articles")
    logger.info(f"{'=' * 60}\n")
    
    return results


def crawl_guangxi_source():
    """Crawl Guangxi Daily (slow source)."""
    logger.info("=" * 60)
    logger.info("Starting scheduled crawl for Guangxi Daily (SLOW)")
    logger.info("=" * 60)
    
    result = crawl_guangxi_job()
    
    if result['success']:
        logger.info(f"✓ Guangxi Daily: {result['article_count']} articles")
    else:
        logger.error(f"✗ Guangxi Daily: {result.get('error', 'Unknown error')}")
    
    logger.info(f"{'=' * 60}\n")
    
    return result


def cleanup_job():
    """Clean up articles older than 7 days."""
    logger.info("=" * 60)
    logger.info("Running scheduled cleanup (7-day retention)")
    logger.info("=" * 60)
    
    try:
        deleted_count = cleanup_old_articles(days=7)
        logger.info(f"✓ Cleanup complete: {deleted_count} old articles deleted")
        logger.info(f"{'=' * 60}\n")
        return {'success': True, 'deleted': deleted_count}
    except Exception as e:
        logger.error(f"✗ Cleanup failed: {e}")
        logger.info(f"{'=' * 60}\n")
        return {'success': False, 'error': str(e)}
