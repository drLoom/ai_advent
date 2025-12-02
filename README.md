## Requirements

- Python 3.10 or higher
- OpenRouter API key (for HTTP server)

## Installation

1. **Clone or navigate to the project directory**

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

3. **Set up your API keys:**

   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

   Then edit `.env` and add your API keys:
   ```

   # For HTTP server (server.py)
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   ```

   Get your API keys from:
   - OpenRouter: https://openrouter.ai/keys

## Usage

### Document Indexing CLI

The CLI provides powerful document indexing and semantic search capabilities using embeddings.

#### View All Commands

```bash
uv run python main.py --help
uv run python main.py index --help
```

#### Available Commands

**Add Documents to Index**
```bash
# Index a PDF document
uv run python main.py index add "document.pdf"

# Index a markdown file
uv run python main.py index add README.md

# Index a Python file
uv run python main.py index add script.py
```

**Index a Directory**
```bash
# Index all supported files in current directory (recursive)
uv run python main.py index add . --recursive

# Index only specific file types
uv run python main.py index add ./docs --file-types pdf,md,txt

# Non-recursive indexing
uv run python main.py index add ./folder --no-recursive

# Custom chunk size
uv run python main.py index add ./data --chunk-size 1000 --chunk-overlap 100
```

**Search Indexed Documents**
```bash
# Basic search
uv run python main.py index search "How do I install dependencies?"

# Search with more results
uv run python main.py index search "What is the revenue?" --top-k 10
```

**Ask Questions (RAG - Retrieval-Augmented Generation)**
```bash
# Ask a question and get an AI-generated answer based on your documents
uv run python main.py index ask "What was NVIDIA's fourth quarter revenue?"

# Use more context chunks for better answers
uv run python main.py index ask "Explain the key findings" --top-k 10

# Use a different model
uv run python main.py index ask "What was NVIDIA's fourth quarter revenue" --model "openai/gpt-4"

# Use reranking to improve answer quality (filters irrelevant results)
uv run python main.py index ask "What are the performance improvements?" --rerank --threshold 0.6

# Customize reranking model (recommended: gpt-4o-mini for better results)
uv run python main.py index ask "How to install?" --rerank --rerank-model "openai/gpt-4o-mini" --threshold 0.5

# Hide source citations
uv run python main.py index ask "What are the highlights?" --no-sources
```

**List Indexed Documents**
```bash
# List all documents
uv run python main.py index list-docs

# Limit results
uv run python main.py index list-docs --limit 20
```

**View Statistics**
```bash
uv run python main.py index stats
```

**Delete Documents**
```bash
# Delete specific document by ID
uv run python main.py index delete <doc_id>
```

**Reindex Documents**
```bash
# Reindex specific document
uv run python main.py index reindex --doc-id <doc_id>

# Reindex all documents
uv run python main.py index reindex --all
```

**Compare Search Results (with and without Reranking)**
```bash
# Compare initial search results vs reranked results side-by-side
uv run python main.py index ranking "What are the new features?"

# Adjust relevance threshold to filter more aggressively
uv run python main.py index ranking "How does it work?" --threshold 0.7

# Use different reranking model
uv run python main.py index ranking "Performance tips" --rerank-model "openai/gpt-4o-mini"
```

#### Supported File Types

- **PDF**: `.pdf`
- **Markdown**: `.md`, `.markdown`
- **Code**: `.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, `.rb`, `.php`, `.swift`, `.kt`, `.scala`
- **Text**: `.txt`, `.log`, `.csv`, `.json`, `.xml`, `.html`

#### How It Works

1. **Document Loading**: Extracts text from various file formats
   - PDF files use PyMuPDF for better text extraction with layout preservation
   - Page numbers are tracked and preserved for PDF documents
2. **Smart Chunking**: Intelligently splits text based on document structure
   - **Markdown files (.md)**: Heading-aware chunking that preserves document hierarchy
     - Keeps sections together when possible
     - Creates hierarchical section paths (e.g., "Installation > Dependencies")
     - Better semantic coherence for documentation and structured content
   - **PDF files (.pdf)**: Token-based chunking with page number tracking
   - **Other files**: Token-based chunking (default 500 tokens with 50 token overlap)
3. **Embedding Generation**: Creates vector embeddings using OpenAI's text-embedding-3-small model
4. **Vector Storage**: Stores embeddings in FAISS index for fast similarity search
5. **Semantic Search**: Retrieves relevant chunks based on query similarity
   - Search results show section titles for markdown documents
   - Search results include page numbers for PDF documents
6. **RAG (Retrieval-Augmented Generation)**: Combines search results with LLM to answer questions based on your documents
   - Source citations show section paths for markdown files (e.g., "Configuration > API Keys")
   - Source citations include page numbers for PDFs (e.g., "Page 5")
   - **Optional Reranking**: Second-stage relevance filtering to improve answer quality
     - Uses an LLM to score each chunk's relevance to the specific query (0-1 scale)
     - Filters out irrelevant chunks using a configurable threshold (default: 0.5)
     - Reorders results by actual relevance, not just vector similarity
     - Reduces noise and improves answer accuracy
     - Recommended model: `openai/gpt-4o-mini` (fast and accurate)

### HTTP Server (server.py)

Run the HTTP server that accepts POST requests and forwards them to OpenRouter:

```bash
uv run server.py
```
