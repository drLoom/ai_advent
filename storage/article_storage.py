"""Article storage handler for saving fetched articles to disk."""
import os
import re
from pathlib import Path
from typing import Optional
from datetime import datetime


class StoreToTxt:
    """Handles storing article content to text files."""

    def __init__(self, base_dir: str = "tmp"):
        """
        Initialize article storage handler.

        Args:
            base_dir: Base directory for storing articles (default: "tmp")
        """
        self.base_dir = Path(base_dir)
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Create storage directory if it doesn't exist."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, title: str) -> str:
        """
        Sanitize article title to create a valid filename.

        Args:
            title: Article title

        Returns:
            Sanitized filename
        """
        # Remove or replace invalid filename characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
        # Replace spaces and multiple underscores with single underscore
        sanitized = re.sub(r'[\s_]+', '_', sanitized)
        # Limit filename length
        max_length = 200
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        # Remove trailing dots and underscores
        sanitized = sanitized.strip('._')
        # Ensure filename is not empty
        if not sanitized:
            sanitized = f"article_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return sanitized

    def save_article(
        self,
        title: str,
        content: str,
        url: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Save article content to a text file.

        Args:
            title: Article title (used for filename)
            content: Article content
            url: Article URL (optional)
            metadata: Additional metadata to include (optional)

        Returns:
            Path to the saved file
        """
        filename = self._sanitize_filename(title) + ".txt"
        filepath = self.base_dir / filename

        # Prepare file content
        file_content = []

        # Add title
        file_content.append("=" * 80)
        file_content.append(f"TITLE: {title}")
        file_content.append("=" * 80)
        file_content.append("")

        # Add URL if provided
        if url:
            file_content.append(f"URL: {url}")
            file_content.append("")

        # Add metadata if provided
        if metadata:
            file_content.append("METADATA:")
            for key, value in metadata.items():
                file_content.append(f"  {key}: {value}")
            file_content.append("")

        # Add timestamp
        file_content.append(f"Saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        file_content.append("")
        file_content.append("-" * 80)
        file_content.append("")

        # Add content
        file_content.append(content)

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(file_content))

        return str(filepath)

    def list_articles(self) -> list[str]:
        """
        List all stored articles.

        Returns:
            List of article filenames
        """
        if not self.base_dir.exists():
            return []

        return sorted([
            f.name for f in self.base_dir.glob("*.txt")
        ])

    def read_article(self, filename: str) -> Optional[str]:
        """
        Read article content from file.

        Args:
            filename: Name of the file to read

        Returns:
            File content or None if file doesn't exist
        """
        filepath = self.base_dir / filename
        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def delete_article(self, filename: str) -> bool:
        """
        Delete an article file.

        Args:
            filename: Name of the file to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        filepath = self.base_dir / filename
        if not filepath.exists():
            return False

        try:
            filepath.unlink()
            return True
        except Exception:
            return False

    def get_storage_stats(self) -> dict:
        """
        Get statistics about stored articles.

        Returns:
            Dictionary with storage statistics
        """
        if not self.base_dir.exists():
            return {
                "total_articles": 0,
                "total_size_bytes": 0,
                "storage_path": str(self.base_dir)
            }

        articles = list(self.base_dir.glob("*.txt"))
        total_size = sum(f.stat().st_size for f in articles)

        return {
            "total_articles": len(articles),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "storage_path": str(self.base_dir.absolute())
        }
