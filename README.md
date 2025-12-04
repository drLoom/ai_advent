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

# Index an EPUB ebook
uv run python main.py index add "book.epub"

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

**Citation Enforcement**

By default, answers include **mandatory citations** in `[Doc#]` format, ensuring every claim is traceable to source documents:

```bash
# With citations (default behavior)
uv run python main.py index ask "What happened in the story?"

# Example output with citations:
# "Santiago caught a large marlin [Doc1]. The old man was 84 days
# without a fish [Doc2], but he remained hopeful [Doc3]."
#
# ✓ Citations present: 3 unique sources cited

# Disable citations for more natural responses
uv run python main.py index ask "What happened in the story?" --no-citations

# The system automatically validates citations and warns if they're missing
# This prevents hallucinations by keeping answers grounded in source documents
```

**Key Features:**
- **Enabled by default**: Every factual claim includes a citation reference
- **Toggle on/off**: Use `--citations` (default) or `--no-citations`
- Citations link back to specific documents with page/chapter numbers
- Automatic validation detects missing citations
- Prevents hallucinations by requiring source grounding
- Works across all languages (tested with English and Russian)

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
- **EPUB**: `.epub`
- **Markdown**: `.md`, `.markdown`
- **Code**: `.py`, `.js`, `.ts`, `.tsx`, `.jsx`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, `.rb`, `.php`, `.swift`, `.kt`, `.scala`
- **Text**: `.txt`, `.log`, `.csv`, `.json`, `.xml`, `.html`

#### How It Works

1. **Document Loading**: Extracts text from various file formats
   - PDF files use PyMuPDF for better text extraction with layout preservation
   - Page numbers are tracked and preserved for PDF documents
   - EPUB files use ebooklib to extract text from chapters
   - Chapter numbers are tracked and preserved for EPUB documents
2. **Smart Chunking**: Intelligently splits text based on document structure
   - **Markdown files (.md)**: Heading-aware chunking that preserves document hierarchy
     - Keeps sections together when possible
     - Creates hierarchical section paths (e.g., "Installation > Dependencies")
     - Better semantic coherence for documentation and structured content
   - **PDF files (.pdf)**: Token-based chunking with page number tracking
   - **EPUB files (.epub)**: Token-based chunking with chapter number tracking
   - **Other files**: Token-based chunking (default 500 tokens with 50 token overlap)
3. **Embedding Generation**: Creates vector embeddings using OpenAI's text-embedding-3-small model
4. **Vector Storage**: Stores embeddings in FAISS index for fast similarity search
5. **Semantic Search**: Retrieves relevant chunks based on query similarity
   - Search results show section titles for markdown documents
   - Search results include page numbers for PDF documents
6. **RAG (Retrieval-Augmented Generation)**: Combines search results with LLM to answer questions based on your documents
   - Source citations show section paths for markdown files (e.g., "Configuration > API Keys")
   - Source citations include page numbers for PDFs (e.g., "Page 5")
   - **Mandatory Citation Enforcement**: All answers include citations in `[Doc#]` format
     - Every factual claim is linked to a source document
     - Automatic validation detects missing citations
     - Prevents hallucinations by requiring source grounding
     - Citations show document title, page/chapter numbers for verification
   - **Optional Reranking**: Second-stage relevance filtering to improve answer quality
     - Uses an LLM to score each chunk's relevance to the specific query (0-1 scale)
     - Filters out irrelevant chunks using a configurable threshold (default: 0.5)
     - Reorders results by actual relevance, not just vector similarity
     - Reduces noise and improves answer accuracy
     - Recommended model: `openai/gpt-4o-mini` (fast and accurate)

### Testing Citation Enforcement

Validate that the citation system is working correctly:

```bash
# Run comprehensive citation tests with citations enabled (default)
uv run python test_citations.py

# Run tests with citations enforced (explicit)
uv run python test_citations.py --citations

# Run tests with citations disabled
uv run python test_citations.py --no-citations

# The test suite will:
# - Test with and without reranking
# - Verify citations are present in all answers (when enabled)
# - Calculate citation rates and averages
# - Provide hallucination analysis
# - Generate detailed comparison reports

# View detailed test report
cat CITATION_TEST_REPORT.md

# View citation modes documentation
cat CITATION_MODES.md
```

**What the test checks:**
- Citation presence in responses (target: 100% when enabled)
- Citation format validation (`[Doc#]` pattern)
- Unique source count per answer
- Comparison of reranking impact on citations
- Manual hallucination detection guidelines
- Impact of citation enforcement on answer quality

### Image Generation CLI

Generate AI images from text prompts with full parameter control and request logging.

#### View Image Commands

```bash
# View all image generation commands
uv run python main.py image --help

# View configuration
uv run python main.py image info
```

#### Generate Images

```bash
# Basic image generation
uv run python main.py image generate "a beautiful sunset over mountains"

# Specify image size
uv run python main.py image generate "cyberpunk city" --size 512x512

# Control quality/steps
uv run python main.py image generate "abstract art" --quality high

# Use seed for reproducibility
uv run python main.py image generate "cat in space" --seed 42

# Save to file
uv run python main.py image generate "futuristic vehicle" --output images/car.png

# Combine parameters
uv run python main.py image generate "dragon in clouds" \
  --size 1024x1024 \
  --quality high \
  --seed 12345 \
  --output dragon.png

# Disable logging
uv run python main.py image generate "landscape" --no-log
```

#### View Generation Logs

```bash
# View last 10 generation requests
uv run python main.py image logs

# View more logs
uv run python main.py image logs --limit 20

# View specific log file
uv run python main.py image logs --file custom_logs.log
```

#### Image Generation Features

- **Model Configuration**: Uses `amazon/nova-2-lite-v1` by default (configurable in `models/models.py`)
- **Parameter Control**:
  - `--prompt`: Text description of the image to generate
  - `--model`: Choose image generation model
  - `--size`: Image dimensions (e.g., `1024x1024`, `512x512`, `768x768`)
  - `--quality`: Quality level (`standard`, `high`) or steps (numeric value)
  - `--seed`: Random seed for reproducible results
  - `--output`: Save image to specified file path
  - `--no-log`: Disable request logging
- **Request Logging**: Automatically logs:
  - Model name used
  - All input parameters (prompt, size, quality, seed)
  - Response latency in milliseconds
  - Cost estimate (if provided by API)
  - Image URL and save location
- **Progress Indicators**: Shows generation progress with spinner
- **Error Handling**: Clear error messages for invalid parameters or API issues

#### Log Format

Each request is logged with:
```
2025-12-03 16:30:45 - image_generation - INFO - Image generation: {
  "timestamp": "2025-12-03T16:30:45",
  "model": "amazon/nova-2-lite-v1",
  "prompt": "a beautiful sunset over mountains",
  "size": "1024x1024",
  "quality": "standard",
  "seed": null,
  "latency_ms": 2543.21,
  "cost_estimate": 0.0023,
  "image_url": "https://..."
}
```

#### Supported Models

The default model is configured in `models/models.py`. You can use any OpenRouter-supported image generation model:
- `amazon/nova-2-lite-v1` (default)
- `flux/schnell`
- `flux/dev`
- `dall-e-3`
- And more via OpenRouter

### HTTP Server (server.py)

Run the HTTP server that accepts POST requests and forwards them to OpenRouter:

```bash
uv run server.py
```
