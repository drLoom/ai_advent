"""Article scraper for web pages using HTTP GET."""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Article:
    """Represents a scraped article."""
    title: str
    url: str
    excerpt: Optional[str] = None
    date: Optional[str] = None
    content: Optional[str] = None


class ArticleScraper:
    """Scrapes articles from web pages."""

    def __init__(self, headers: Optional[Dict[str, str]] = None):
        """Initialize scraper with optional custom headers."""
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def fetch_page(self, url: str) -> str:
        """Fetch page content via HTTP GET."""
        logger.info(f"Fetching page: {url}")
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        logger.info(f"Fetched {len(response.content)} bytes")
        return response.text

    def scrape_adexchanger_technology(self, limit: int = 10) -> List[Article]:
        """Scrape top N articles from AdExchanger technology section."""
        url = "https://www.adexchanger.com/technology/"
        html = self.fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')

        articles = []
        seen_titles = set()
        seen_urls = set()

        # Try multiple selectors to find articles
        # Common WordPress article selectors
        article_selectors = [
            'article',
            '.post',
            '.entry',
            'div[class*="post"]',
            'div[class*="article"]',
        ]

        for selector in article_selectors:
            article_elements = soup.select(selector)
            if article_elements:
                logger.info(f"Found {len(article_elements)} articles using selector: {selector}")
                break

        if not article_elements:
            logger.warning("No articles found with standard selectors")
            return articles

        for element in article_elements:
            if len(articles) >= limit:
                break

            article = self._parse_article_element(element)
            if article and article.title:
                # Deduplicate by title and URL
                if article.title in seen_titles:
                    logger.debug(f"Skipping duplicate title: {article.title[:60]}...")
                    continue
                if article.url and article.url in seen_urls:
                    logger.debug(f"Skipping duplicate URL: {article.url}")
                    continue

                articles.append(article)
                seen_titles.add(article.title)
                if article.url:
                    seen_urls.add(article.url)
                logger.info(f"Scraped: {article.title[:60]}...")

        logger.info(f"Scraped {len(articles)} unique articles")
        return articles

    def _parse_article_element(self, element) -> Optional[Article]:
        """Parse an article element to extract metadata."""
        try:
            # Try to find title
            title = None
            title_selectors = ['h2', 'h3', 'h1', '.entry-title', '.post-title']
            for selector in title_selectors:
                title_elem = element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break

            if not title:
                return None

            # Try to find URL
            url = None
            link = element.select_one('a[href]')
            if link:
                url = link.get('href')
                # Make relative URLs absolute
                if url and not url.startswith('http'):
                    url = f"https://www.adexchanger.com{url}"

            # Try to find excerpt
            excerpt = None
            excerpt_selectors = ['.excerpt', '.entry-excerpt', '.post-excerpt', 'p']
            for selector in excerpt_selectors:
                excerpt_elem = element.select_one(selector)
                if excerpt_elem:
                    excerpt = excerpt_elem.get_text(strip=True)
                    if len(excerpt) > 50:  # Only use if substantial
                        break

            # Try to find date
            date = None
            date_selectors = ['time', '.date', '.post-date', '.entry-date']
            for selector in date_selectors:
                date_elem = element.select_one(selector)
                if date_elem:
                    date = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    break

            return Article(
                title=title,
                url=url or "",
                excerpt=excerpt,
                date=date
            )

        except Exception as e:
            logger.error(f"Error parsing article element: {e}")
            return None

    def fetch_article_content(self, url: str) -> Optional[str]:
        """Fetch full article content from URL."""
        try:
            html = self.fetch_page(url)
            soup = BeautifulSoup(html, 'html.parser')

            # Try to find main content
            content_selectors = [
                'article .entry-content',
                '.post-content',
                '.article-content',
                'article',
                '.content'
            ]

            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Extract paragraphs
                    paragraphs = content_elem.find_all('p')
                    content = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                    if len(content) > 200:
                        logger.info(f"Extracted {len(content)} chars of content")
                        return content

            logger.warning(f"Could not extract content from {url}")
            return None

        except Exception as e:
            logger.error(f"Error fetching article content: {e}")
            return None
