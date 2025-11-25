#!/usr/bin/env python3
"""MCP server for article database storage and retrieval."""
import asyncio
import sys
from pathlib import Path
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

sys.path.insert(0, str(Path(__file__).parent.parent))
from storage import ArticleStorage


app = Server("article-storage")
article_storage = ArticleStorage()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available article storage tools."""
    return [
        Tool(
            name="save_article",
            description="Save article to database",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Article title"
                    },
                    "content": {
                        "type": "string",
                        "description": "Article content"
                    },
                    "url": {
                        "type": "string",
                        "description": "Article URL (optional)"
                    }
                },
                "required": ["title", "content"]
            }
        ),
        Tool(
            name="get_article",
            description="Get article by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "integer",
                        "description": "Article ID"
                    }
                },
                "required": ["article_id"]
            }
        ),
        Tool(
            name="get_article_by_url",
            description="Get article by URL",
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
            name="list_articles",
            description="List all articles (most recent first)",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of articles to return"
                    }
                }
            }
        ),
        Tool(
            name="search_articles",
            description="Search articles by title or content",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Search term"
                    }
                },
                "required": ["search_term"]
            }
        ),
        Tool(
            name="save_review",
            description="Save LLM review for an article",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "integer",
                        "description": "Article ID"
                    },
                    "review_text": {
                        "type": "string",
                        "description": "Review/summary text"
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Name of the LLM model used"
                    }
                },
                "required": ["article_id", "review_text", "model_name"]
            }
        ),
        Tool(
            name="get_article_with_reviews",
            description="Get article with all its reviews",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "integer",
                        "description": "Article ID"
                    }
                },
                "required": ["article_id"]
            }
        ),
        Tool(
            name="delete_article",
            description="Delete article by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "integer",
                        "description": "Article ID to delete"
                    }
                },
                "required": ["article_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute an article storage tool."""

    if name == "save_article":
        title = arguments["title"]
        content = arguments["content"]
        url = arguments.get("url")

        article_id = article_storage.save_article(
            title=title,
            content=content,
            url=url
        )

        output = f"Article saved successfully!\n"
        output += f"ID: {article_id}\n"
        output += f"Title: {title}\n"
        if url:
            output += f"URL: {url}\n"

        return [TextContent(type="text", text=output)]

    elif name == "get_article":
        article_id = arguments["article_id"]
        article = article_storage.get_article(article_id)

        if not article:
            return [TextContent(
                type="text",
                text=f"Article with ID {article_id} not found."
            )]

        output = f"Title: {article['title']}\n"
        output += f"URL: {article.get('url', 'N/A')}\n"
        output += f"Created: {article['created_at']}\n"
        output += f"\nContent:\n{article['content'][:1000]}"
        if len(article['content']) > 1000:
            output += f"\n... (truncated, total length: {len(article['content'])})"

        return [TextContent(type="text", text=output)]

    elif name == "get_article_by_url":
        url = arguments["url"]
        article = article_storage.get_article_by_url(url)

        if not article:
            return [TextContent(
                type="text",
                text=f"Article with URL '{url}' not found."
            )]

        output = f"ID: {article['id']}\n"
        output += f"Title: {article['title']}\n"
        output += f"URL: {article.get('url', 'N/A')}\n"
        output += f"Created: {article['created_at']}\n"
        output += f"\nContent:\n{article['content'][:1000]}"
        if len(article['content']) > 1000:
            output += f"\n... (truncated, total length: {len(article['content'])})"

        return [TextContent(type="text", text=output)]

    elif name == "list_articles":
        limit = arguments.get("limit", 10)
        articles = article_storage.list_articles(limit=limit)

        if not articles:
            return [TextContent(type="text", text="No articles found.")]

        output = f"Found {len(articles)} articles:\n\n"
        for i, article in enumerate(articles, 1):
            output += f"{i}. [{article['id']}] {article['title']}\n"
            if article.get('url'):
                output += f"   URL: {article['url']}\n"
            output += f"   Created: {article['created_at']}\n"
            output += f"   Length: {len(article['content'])} chars\n\n"

        return [TextContent(type="text", text=output)]

    elif name == "search_articles":
        search_term = arguments["search_term"]
        articles = article_storage.search_articles(search_term)

        if not articles:
            return [TextContent(
                type="text",
                text=f"No articles found matching '{search_term}'."
            )]

        output = f"Found {len(articles)} articles matching '{search_term}':\n\n"
        for i, article in enumerate(articles, 1):
            output += f"{i}. [{article['id']}] {article['title']}\n"
            if article.get('url'):
                output += f"   URL: {article['url']}\n"
            output += f"   Created: {article['created_at']}\n\n"

        return [TextContent(type="text", text=output)]

    elif name == "save_review":
        article_id = arguments["article_id"]
        review_text = arguments["review_text"]
        model_name = arguments["model_name"]

        review_id = article_storage.save_review(
            article_id=article_id,
            review_text=review_text,
            model_name=model_name
        )

        if review_id is None:
            return [TextContent(
                type="text",
                text=f"Failed to save review. Article {article_id} not found."
            )]

        output = f"Review saved successfully!\n"
        output += f"Review ID: {review_id}\n"
        output += f"Article ID: {article_id}\n"
        output += f"Model: {model_name}\n"

        return [TextContent(type="text", text=output)]

    elif name == "get_article_with_reviews":
        article_id = arguments["article_id"]
        article = article_storage.get_article_with_reviews(article_id)

        if not article:
            return [TextContent(
                type="text",
                text=f"Article with ID {article_id} not found."
            )]

        output = f"Title: {article['title']}\n"
        output += f"URL: {article.get('url', 'N/A')}\n"
        output += f"Created: {article['created_at']}\n"
        output += f"\nContent:\n{article['content'][:500]}"
        if len(article['content']) > 500:
            output += f"\n... (truncated, total: {len(article['content'])})"

        reviews = article.get('reviews', [])
        output += f"\n\nReviews ({len(reviews)}):\n"
        if reviews:
            for i, review in enumerate(reviews, 1):
                output += f"\n--- Review {i} (by {review['model_name']}) ---\n"
                output += f"{review['review_text']}\n"
                output += f"Created: {review['created_at']}\n"
        else:
            output += "No reviews yet.\n"

        return [TextContent(type="text", text=output)]

    elif name == "delete_article":
        article_id = arguments["article_id"]
        success = article_storage.delete_article(article_id)

        if success:
            return [TextContent(
                type="text",
                text=f"Article {article_id} deleted successfully."
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Article {article_id} not found."
            )]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP article storage server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
