"""SQLAlchemy models for article storage."""
import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Article(Base):
    """SQLAlchemy model for storing articles."""

    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(1000), nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.now)

    def to_dict(self) -> dict:
        """Convert article to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'metadata': json.loads(self.metadata) if self.metadata else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
