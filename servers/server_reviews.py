#!/usr/bin/env python3
"""MCP server for LLM review storage and retrieval."""
import asyncio
import sys
from pathlib import Path
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

sys.path.insert(0, str(Path(__file__).parent.parent))
from storage import ArticleStorage


app = Server("review-storage")
storage = ArticleStorage()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available review management tools."""
    return [
        Tool(
            name="save_review",
            description="Save LLM review for an article",
            inputSchema={
                "type": "object",
                "properties": {
                    "article_id": {
                        "type": "integer",
                        "description": "Article ID to review"
                    },
                    "review_text": {
                        "type": "string",
                        "description": "Review/summary/analysis text"
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Name of the LLM model (e.g., 'gemini-2.5-flash')"
                    }
                },
                "required": ["article_id", "review_text", "model_name"]
            }
        ),
        Tool(
            name="get_review",
            description="Get review by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "review_id": {
                        "type": "integer",
                        "description": "Review ID"
                    }
                },
                "required": ["review_id"]
            }
        ),
        Tool(
            name="get_reviews_for_article",
            description="Get all reviews for a specific article",
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
            name="delete_review",
            description="Delete a review by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "review_id": {
                        "type": "integer",
                        "description": "Review ID to delete"
                    }
                },
                "required": ["review_id"]
            }
        ),
        Tool(
            name="get_article_with_reviews",
            description="Get article along with all its reviews",
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
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a review management tool."""

    if name == "save_review":
        article_id = arguments["article_id"]
        review_text = arguments["review_text"]
        model_name = arguments["model_name"]

        review_id = storage.save_review(
            article_id=article_id,
            review_text=review_text,
            model_name=model_name
        )

        if review_id is None:
            return [TextContent(
                type="text",
                text=f"Error: Article {article_id} not found. Cannot save review."
            )]

        output = f"Review saved successfully!\n"
        output += f"Review ID: {review_id}\n"
        output += f"Article ID: {article_id}\n"
        output += f"Model: {model_name}\n"
        output += f"Review length: {len(review_text)} characters"

        return [TextContent(type="text", text=output)]

    elif name == "get_review":
        review_id = arguments["review_id"]
        review = storage.get_review(review_id)

        if not review:
            return [TextContent(
                type="text",
                text=f"Review {review_id} not found."
            )]

        output = f"Review ID: {review['id']}\n"
        output += f"Article ID: {review['article_id']}\n"
        output += f"Model: {review['model_name']}\n"
        output += f"Created: {review['created_at']}\n"
        output += f"\nReview:\n{review['review_text']}"

        return [TextContent(type="text", text=output)]

    elif name == "get_reviews_for_article":
        article_id = arguments["article_id"]
        reviews = storage.get_reviews_for_article(article_id)

        if not reviews:
            article = storage.get_article(article_id)
            if not article:
                return [TextContent(
                    type="text",
                    text=f"Article {article_id} not found."
                )]
            return [TextContent(
                type="text",
                text=f"No reviews found for article {article_id}."
            )]

        output = f"Found {len(reviews)} review(s) for article {article_id}:\n\n"
        for i, review in enumerate(reviews, 1):
            output += f"--- Review {i} ---\n"
            output += f"ID: {review['id']}\n"
            output += f"Model: {review['model_name']}\n"
            output += f"Created: {review['created_at']}\n"
            output += f"Text: {review['review_text'][:200]}"
            if len(review['review_text']) > 200:
                output += f"... (truncated, total: {len(review['review_text'])})"
            output += "\n\n"

        return [TextContent(type="text", text=output)]

    elif name == "delete_review":
        review_id = arguments["review_id"]
        success = storage.delete_review(review_id)

        if success:
            return [TextContent(
                type="text",
                text=f"Review {review_id} deleted successfully."
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Review {review_id} not found."
            )]

    elif name == "get_article_with_reviews":
        article_id = arguments["article_id"]
        article = storage.get_article_with_reviews(article_id)

        if not article:
            return [TextContent(
                type="text",
                text=f"Article {article_id} not found."
            )]

        output = f"=== Article {article['id']} ===\n"
        output += f"Title: {article['title']}\n"
        output += f"URL: {article.get('url', 'N/A')}\n"
        output += f"Created: {article['created_at']}\n"
        output += f"Content length: {len(article['content'])} characters\n"

        reviews = article.get('reviews', [])
        output += f"\n=== Reviews ({len(reviews)}) ===\n"

        if reviews:
            for i, review in enumerate(reviews, 1):
                output += f"\n--- Review {i} (by {review['model_name']}) ---\n"
                output += f"Review ID: {review['id']}\n"
                output += f"Created: {review['created_at']}\n"
                output += f"\n{review['review_text']}\n"
        else:
            output += "\nNo reviews yet for this article.\n"

        return [TextContent(type="text", text=output)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP review storage server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
