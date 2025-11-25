#!/usr/bin/env python3
"""MCP server for news parsing and article extraction."""
import asyncio
from urllib.parse import urljoin
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import httpx
from bs4 import BeautifulSoup
from lxml import html
from storage.article_storage import StoreToTxt


app = Server("news-parser")

# Initialize article storage
article_storage = StoreToTxt()


def fetch_article_content(url: str) -> dict:
    """Fetch and extract clean article content from URL."""
    try:
        response = httpx.get(url, timeout=10.0, follow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Try to find article content
        article = None
        for tag in ['article', 'main', 'div[class*="content"]']:
            article = soup.find(tag)
            if article:
                break

        if not article:
            article = soup.find('body')

        # Extract title
        title = ""
        title_tag = soup.find('h1') or soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()

        # Extract text
        paragraphs = article.find_all('p') if article else []
        content = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

        return {
            "title": title,
            "url": url,
            "content": content[:5000],  # Limit to 5000 chars
            "length": len(content)
        }
    except Exception as e:
        return {"error": str(e)}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available news parsing tools."""
    return [
        Tool(
            name="fetch_article",
            description="Fetch and extract clean article content from URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Article URL"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="fetch_multiple_articles",
            description="Scrape article links from category/listing page",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Category or listing page URL (e.g., https://www.adexchanger.com/technology/)"
                    },
                    "max_articles": {
                        "type": "integer",
                        "description": "Maximum number of articles to list (default: 10)"
                    }
                },
                "required": ["url"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a news parsing tool."""
    if name == "fetch_article":
        url = arguments["url"]
        result = fetch_article_content(url)

        if "error" in result:
            return [TextContent(type="text", text=f"Error: {result['error']}")]

        # Save article to disk
        try:
            saved_path = article_storage.save_article(
                title=result['title'],
                content=result['content'],
                url=result['url'],
                metadata={'length': result['length']}
            )

            output = f"Title: {result['title']}\n"
            output += f"URL: {result['url']}\n"
            output += f"Saved to: {saved_path}\n"
            output += f"Length: {result['length']} characters\n\n"
            output += f"Content:\n{result['content']}"
        except Exception as e:
            # If saving fails, still return the content but note the error
            output = f"Title: {result['title']}\n"
            output += f"URL: {result['url']}\n"
            output += f"Warning: Failed to save article - {str(e)}\n"
            output += f"Length: {result['length']} characters\n\n"
            output += f"Content:\n{result['content']}"

        return [TextContent(type="text", text=output)]

    elif name == "fetch_multiple_articles":
        url = arguments["url"]
        max_articles = arguments.get("max_articles", 10)

        try:
            # Fetch the listing page
            response = httpx.get(url, timeout=10.0, follow_redirects=True)
            response.raise_for_status()

            # Parse with lxml to use XPath
            tree = html.fromstring(response.text)

            # Use XPath to find all links with class 'link-post'
            article_links = []
            link_elements = tree.xpath('//a[@class="link-post"]')

            for link in link_elements[:max_articles]:
                href = link.get('href', '')
                # Make absolute URL if relative
                if href.startswith('/'):
                    href = urljoin(url, href)

                # Get the text content as title
                title = link.text_content().strip()

                if href and title:
                    article_links.append({
                        'title': title,
                        'url': href
                    })

            # Format output
            output = f"Found {len(article_links)} articles from {url}:\n\n"
            for i, article in enumerate(article_links, 1):
                output += f"{i}. {article['title']}\n"
                output += f"   URL: {article['url']}\n\n"

            return [TextContent(type="text", text=output)]

        except Exception as e:
            return [TextContent(type="text", text=f"Error scraping articles: {str(e)}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP news parsing server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
