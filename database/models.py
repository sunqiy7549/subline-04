"""Database models for news aggregator."""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Article(Base):
    """Article model for storing news articles."""
    
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)           # e.g., '福建日报'
    source_key = Column(String(20), nullable=False)       # e.g., 'fujian'
    section = Column(String(100))                         # e.g., '01 要闻'
    title = Column(Text, nullable=False)
    title_ko = Column(Text)                               # Korean translation
    link = Column(String(500), nullable=False, unique=True)
    content_preview = Column(Text)                        # First 200 chars
    date = Column(String(10), nullable=False)             # YYYY-MM-DD
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_date', 'date'),
        Index('idx_source', 'source_key'),
        Index('idx_link', 'link'),
    )
    
    def __repr__(self):
        return f"<Article(source='{self.source}', title='{self.title[:30]}...', date='{self.date}')>"
    
    def to_dict(self):
        """Convert article to dictionary for API response."""
        return {
            'id': self.id,
            'source': self.source,
            'source_key': self.source_key,
            'section': self.section,
            'title': self.title,
            'title_ko': self.title_ko,
            'link': self.link,
            'content_preview': self.content_preview,
            'date': self.date,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }
