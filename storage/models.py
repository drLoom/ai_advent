"""SQLAlchemy models for article storage."""
import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Article(Base):
    """SQLAlchemy model for storing articles."""

    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(1000), nullable=True)
    meta_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    reviews = relationship("Review", back_populates="article", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert article to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'url': self.url,
            'metadata': json.loads(self.meta_data) if self.meta_data else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Review(Base):
    """SQLAlchemy model for storing LLM reviews of articles."""

    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    review_text = Column(Text, nullable=False)
    model_name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    article = relationship("Article", back_populates="reviews")

    def to_dict(self) -> dict:
        """Convert review to dictionary."""
        return {
            'id': self.id,
            'article_id': self.article_id,
            'review_text': self.review_text,
            'model_name': self.model_name,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Conversation(Base):
    """SQLAlchemy model for storing conversation sessions."""

    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )

    def to_dict(self) -> dict:
        """Convert conversation to dictionary."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': len(self.messages) if self.messages else 0
        }


class Message(Base):
    """SQLAlchemy model for storing individual messages in conversations."""

    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        Integer,
        ForeignKey('conversations.id'),
        nullable=False
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    model_name = Column(String(200), nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    temperature = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    conversation = relationship("Conversation", back_populates="messages")

    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'role': self.role,
            'content': self.content,
            'model_name': self.model_name,
            'prompt_tokens': self.prompt_tokens,
            'completion_tokens': self.completion_tokens,
            'total_tokens': self.total_tokens,
            'temperature': self.temperature,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
