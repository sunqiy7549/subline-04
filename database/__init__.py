"""Database package initialization."""
from database.models import Article, Base
from database.db import (
    init_db,
    get_session,
    save_articles,
    get_articles_by_date,
    cleanup_old_articles,
    get_stats
)

__all__ = [
    'Article',
    'Base',
    'init_db',
    'get_session',
    'save_articles',
    'get_articles_by_date',
    'cleanup_old_articles',
    'get_stats'
]
