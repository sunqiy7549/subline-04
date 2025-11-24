"""Database initialization and helper functions."""
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
from database.models import Base, Article

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'news.db')
DB_URL = f'sqlite:///{DB_PATH}'

# Create engine and session factory
engine = None
Session = None


def init_db():
    """Initialize database and create tables if they don't exist."""
    global engine, Session
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Create engine
    engine = create_engine(DB_URL, echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session factory
    Session = scoped_session(sessionmaker(bind=engine))
    
    print(f"✓ Database initialized at {DB_PATH}")
    return engine


def get_session():
    """Get a database session."""
    if Session is None:
        init_db()
    return Session()


def save_articles(articles_data, source_key, date_str):
    """
    Save multiple articles to database.
    
    Args:
        articles_data: List of article dicts from crawler
        source_key: Source identifier (e.g., 'fujian')
        date_str: Date string in YYYY-MM-DD format
    
    Returns:
        Tuple of (success_count, error_count)
    """
    session = get_session()
    success_count = 0
    error_count = 0
    
    try:
        for article_data in articles_data:
            try:
                # Check if article already exists
                existing = session.query(Article).filter_by(link=article_data['link']).first()
                
                if existing:
                    # Update existing article
                    existing.title = article_data.get('title', existing.title)
                    existing.title_ko = article_data.get('title_ko', existing.title_ko)
                    existing.section = article_data.get('section', existing.section)
                    existing.content_preview = article_data.get('content_preview', existing.content_preview)
                    existing.last_updated = datetime.utcnow()
                else:
                    # Create new article
                    article = Article(
                        source=article_data.get('source', ''),
                        source_key=source_key,
                        section=article_data.get('section', ''),
                        title=article_data['title'],
                        title_ko=article_data.get('title_ko', ''),
                        link=article_data['link'],
                        content_preview=article_data.get('content_preview', ''),
                        date=date_str
                    )
                    session.add(article)
                
                success_count += 1
                
            except IntegrityError:
                session.rollback()
                error_count += 1
                continue
        
        session.commit()
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error saving articles: {e}")
        raise
    finally:
        session.close()
    
    return success_count, error_count


def get_articles_by_date(source_key=None, date_str=None):
    """
    Retrieve articles from database.
    
    Args:
        source_key: Optional source filter (e.g., 'fujian')
        date_str: Optional date filter in YYYY-MM-DD format
    
    Returns:
        List of Article objects
    """
    session = get_session()
    
    try:
        query = session.query(Article)
        
        if source_key:
            query = query.filter(Article.source_key == source_key)
        
        if date_str:
            query = query.filter(Article.date == date_str)
        
        # Order by date desc, then by source
        query = query.order_by(Article.date.desc(), Article.source_key)
        
        articles = query.all()
        return articles
        
    finally:
        session.close()


def cleanup_old_articles(days=7):
    """
    Delete articles older than specified days.
    
    Args:
        days: Number of days to retain (default: 7)
    
    Returns:
        Number of articles deleted
    """
    session = get_session()
    
    try:
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        deleted = session.query(Article).filter(Article.date < cutoff_date).delete()
        session.commit()
        
        print(f"✓ Cleaned up {deleted} articles older than {cutoff_date}")
        return deleted
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error cleaning up articles: {e}")
        raise
    finally:
        session.close()


def get_stats():
    """Get database statistics."""
    session = get_session()
    
    try:
        total = session.query(Article).count()
        
        # Count by source
        by_source = {}
        for source_key in ['fujian', 'hainan', 'nanfang', 'guangzhou', 'guangxi']:
            count = session.query(Article).filter(Article.source_key == source_key).count()
            by_source[source_key] = count
        
        # Database file size
        db_size = os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0
        db_size_mb = db_size / (1024 * 1024)
        
        return {
            'total_articles': total,
            'by_source': by_source,
            'db_size_mb': round(db_size_mb, 2)
        }
        
    finally:
        session.close()
