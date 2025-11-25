"""Article storage handler using SQLAlchemy ORM with SQLite."""
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, Article, Review


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
                meta_data=json.dumps(metadata) if metadata else None,
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
                article.meta_data = json.dumps(metadata)

            session.commit()
            return True
        finally:
            session.close()

    def save_review(
        self,
        article_id: int,
        review_text: str,
        model_name: str
    ) -> Optional[int]:
        """
        Save LLM review for an article.

        Args:
            article_id: Article ID
            review_text: Review/summary text
            model_name: Name of the LLM model used

        Returns:
            Review ID if saved successfully, None if article doesn't exist
        """
        session = self._get_session()
        try:
            article = session.query(Article).filter(Article.id == article_id).first()
            if not article:
                return None

            review = Review(
                article_id=article_id,
                review_text=review_text,
                model_name=model_name,
                created_at=datetime.now()
            )
            session.add(review)
            session.commit()
            session.refresh(review)
            return review.id
        finally:
            session.close()

    def get_reviews_for_article(self, article_id: int) -> List[dict]:
        """
        Get all reviews for a specific article.

        Args:
            article_id: Article ID

        Returns:
            List of review dictionaries
        """
        session = self._get_session()
        try:
            reviews = session.query(Review).filter(
                Review.article_id == article_id
            ).order_by(Review.created_at.desc()).all()
            return [review.to_dict() for review in reviews]
        finally:
            session.close()

    def get_review(self, review_id: int) -> Optional[dict]:
        """
        Get review by ID.

        Args:
            review_id: Review ID

        Returns:
            Review dictionary or None if not found
        """
        session = self._get_session()
        try:
            review = session.query(Review).filter(Review.id == review_id).first()
            return review.to_dict() if review else None
        finally:
            session.close()

    def delete_review(self, review_id: int) -> bool:
        """
        Delete a review by ID.

        Args:
            review_id: Review ID

        Returns:
            True if deleted successfully, False otherwise
        """
        session = self._get_session()
        try:
            review = session.query(Review).filter(Review.id == review_id).first()
            if review:
                session.delete(review)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_article_with_reviews(self, article_id: int) -> Optional[dict]:
        """
        Get article with all its reviews.

        Args:
            article_id: Article ID

        Returns:
            Dictionary with article and reviews, or None if not found
        """
        session = self._get_session()
        try:
            article = session.query(Article).filter(Article.id == article_id).first()
            if not article:
                return None

            article_dict = article.to_dict()
            reviews = session.query(Review).filter(
                Review.article_id == article_id
            ).order_by(Review.created_at.desc()).all()
            article_dict['reviews'] = [review.to_dict() for review in reviews]

            return article_dict
        finally:
            session.close()
