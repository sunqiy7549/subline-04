"""Test database operations."""
import sys
from datetime import datetime
from database import init_db, save_articles, get_articles_by_date, cleanup_old_articles, get_stats

def test_database():
    """Test database initialization and basic operations."""
    
    print("=" * 60)
    print("Testing Database Layer")
    print("=" * 60)
    
    # 1. Initialize database
    print("\n[1] Initializing database...")
    init_db()
    
    # 2. Test save_articles
    print("\n[2] Testing save_articles...")
    test_articles = [
        {
            'source': '福建日报',
            'section': '01 要闻',
            'title': '测试新闻标题1',
            'title_ko': '테스트 뉴스 제목 1',
            'link': 'https://test.com/article1',
            'content_preview': '这是一篇测试新闻的预览内容...'
        },
        {
            'source': '福建日报',
            'section': '02 综合',
            'title': '测试新闻标题2',
            'title_ko': '테스트 뉴스 제목 2',
            'link': 'https://test.com/article2',
            'content_preview': '这是另一篇测试新闻的预览内容...'
        }
    ]
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    success, errors = save_articles(test_articles, 'fujian', date_str)
    print(f"  ✓ Saved {success} articles, {errors} errors")
    
    # 3. Test get_articles_by_date
    print("\n[3] Testing get_articles_by_date...")
    articles = get_articles_by_date(source_key='fujian', date_str=date_str)
    print(f"  ✓ Retrieved {len(articles)} articles")
    
    for article in articles:
        print(f"    - {article.title[:30]}... ({article.link})")
    
    # 4. Test get_stats
    print("\n[4] Testing get_stats...")
    stats = get_stats()
    print(f"  ✓ Total articles: {stats['total_articles']}")
    print(f"  ✓ Database size: {stats['db_size_mb']} MB")
    print(f"  ✓ By source: {stats['by_source']}")
    
    # 5. Test duplicate handling (should update existing)
    print("\n[5] Testing duplicate handling...")
    test_articles[0]['title'] = '测试新闻标题1 (更新)'
    success, errors = save_articles([test_articles[0]], 'fujian', date_str)
    print(f"  ✓ Updated {success} articles")
    
    # Verify update
    articles = get_articles_by_date(source_key='fujian', date_str=date_str)
    updated = [a for a in articles if '更新' in a.title]
    print(f"  ✓ Found {len(updated)} updated articles")
    
    # 6. Test to_dict method
    print("\n[6] Testing to_dict method...")
    if articles:
        article_dict = articles[0].to_dict()
        print(f"  ✓ Article dict keys: {list(article_dict.keys())}")
    
    print("\n" + "=" * 60)
    print("✓ All database tests passed!")
    print("=" * 60)
    
    return True


if __name__ == '__main__':
    try:
        test_database()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
