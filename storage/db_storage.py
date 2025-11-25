"""Article storage handler using SQLAlchemy ORM with SQLite."""
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, Article


class ArticleStorage:
    """Handles storing articles using SQLAlchemy ORM with SQLite."""

    def __init__(self, db_path: str = "db/articles.sqlite"):
        """
        Initialize article storage with SQLite database.

        Args:
            db_path: Path to SQLite database file (default: "db/articles.sqlite")
        """
        self.db_path = Path(db_path)
        self._ensure_directory_exists()

        # Create SQLAlchemy engine and session
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _ensure_directory_exists(self) -> None:
        """Create database directory if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def save_article(
        self,
        title: str,
        content: str,
        url: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> int:
        """
        Save article to database.

        Args:
            title: Article title
            content: Article content
            url: Article URL (optional)
            metadata: Additional metadata to include (optional)

        Returns:
            ID of the saved article
        """
        session = self._get_session()
        try:
            article = Article(
                title=title,
                content=content,
                url=url,
                metadata=json.dumps(metadata) if metadata else None,
                created_at=datetime.now()
            )
            session.add(article)
            session.commit()
            session.refresh(article)
            return article.id
        finally:
            session.close()

    def get_article(self, article_id: int) -> Optional[dict]:
        """
        Get article by ID.

        Args:
            article_id: Article ID

        Returns:
            Article dictionary or None if not found
        """
        session = self._get_session()
        try:
            article = session.query(Article).filter(Article.id == article_id).first()
            return article.to_dict() if article else None
        finally:
            session.close()

    def get_article_by_url(self, url: str) -> Optional[dict]:
        """
        Get article by URL.

        Args:
            url: Article URL

        Returns:
            Article dictionary or None if not found
        """
        session = self._get_session()
        try:
            article = session.query(Article).filter(Article.url == url).first()
            return article.to_dict() if article else None
        finally:
            session.close()

    def list_articles(self, limit: Optional[int] = None) -> List[dict]:
        """
        List all stored articles.

        Args:
            limit: Maximum number of articles to return (optional)

        Returns:
            List of article dictionaries
        """
        session = self._get_session()
        try:
            query = session.query(Article).order_by(Article.created_at.desc())
            if limit:
                query = query.limit(limit)
            articles = query.all()
            return [article.to_dict() for article in articles]
        finally:
            session.close()

    def search_articles(self, search_term: str) -> List[dict]:
        """
        Search articles by title or content.

        Args:
            search_term: Term to search for

        Returns:
            List of matching article dictionaries
        """
        session = self._get_session()
        try:
            articles = session.query(Article).filter(
                (Article.title.contains(search_term)) |
                (Article.content.contains(search_term))
            ).order_by(Article.created_at.desc()).all()
            return [article.to_dict() for article in articles]
        finally:
            session.close()

    def delete_article(self, article_id: int) -> bool:
        """
        Delete an article by ID.

        Args:
            article_id: Article ID

        Returns:
            True if deleted successfully, False otherwise
        """
        session = self._get_session()
        try:
            article = session.query(Article).filter(Article.id == article_id).first()
            if article:
                session.delete(article)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_storage_stats(self) -> dict:
        """
        Get statistics about stored articles.

        Returns:
            Dictionary with storage statistics
        """
        session = self._get_session()
        try:
            total_articles = session.query(Article).count()

            # Get database file size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "total_articles": total_articles,
                "total_size_bytes": db_size,
                "total_size_mb": round(db_size / (1024 * 1024), 2),
                "storage_path": str(self.db_path.absolute())
            }
        finally:
            session.close()

    def update_article(
        self,
        article_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        url: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Update an existing article.

        Args:
            article_id: Article ID
            title: New title (optional)
            content: New content (optional)
            url: New URL (optional)
            metadata: New metadata (optional)

        Returns:
            True if updated successfully, False otherwise
        """
        session = self._get_session()
        try:
            article = session.query(Article).filter(Article.id == article_id).first()
            if not article:
                return False

            if title is not None:
                article.title = title
            if content is not None:
                article.content = content
            if url is not None:
                article.url = url
            if metadata is not None:
                article.metadata = json.dumps(metadata)

            session.commit()
            return True
        finally:
            session.close()
