"""Text chunking utilities for document indexing."""
import tiktoken
from typing import List, Optional, Dict


class TextChunk:
    """Container for a text chunk with metadata."""

    def __init__(
        self,
        content: str,
        chunk_index: int,
        token_count: int,
        start_char: int,
        end_char: int,
        page_number: int = None
    ):
        self.content = content
        self.chunk_index = chunk_index
        self.token_count = token_count
        self.start_char = start_char
        self.end_char = end_char
        self.page_number = page_number


class TextChunker:
    """Splits text into chunks with configurable size and overlap."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target size of each chunk in tokens
            chunk_overlap: Number of tokens to overlap between chunks
            encoding_name: Tokenizer encoding (cl100k_base for GPT-4)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))

    def _find_page_number(
        self,
        char_position: int,
        page_contents: Optional[List[Dict]] = None
    ) -> Optional[int]:
        """
        Find the page number for a given character position.

        Args:
            char_position: Character position in the document
            page_contents: List of page metadata with char_start and char_end

        Returns:
            Page number or None if not found
        """
        if not page_contents:
            return None

        for page_info in page_contents:
            if page_info['char_start'] <= char_position < page_info['char_end']:
                return page_info['page']

        # If position is beyond all pages, return last page
        if page_contents:
            return page_contents[-1]['page']

        return None

    def chunk_text(
        self,
        text: str,
        page_contents: Optional[List[Dict]] = None
    ) -> List[TextChunk]:
        """
        Split text into chunks with overlap.

        Args:
            text: Text to split
            page_contents: Optional list of page metadata for page number tracking

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        # Encode the entire text to tokens
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)

        # If text is smaller than chunk size, return as single chunk
        if total_tokens <= self.chunk_size:
            page_num = self._find_page_number(0, page_contents) if page_contents else None
            return [
                TextChunk(
                    content=text,
                    chunk_index=0,
                    token_count=total_tokens,
                    start_char=0,
                    end_char=len(text),
                    page_number=page_num
                )
            ]

        chunks = []
        chunk_index = 0
        start_token = 0

        while start_token < total_tokens:
            # Calculate end token for this chunk
            end_token = min(start_token + self.chunk_size, total_tokens)

            # Extract tokens for this chunk
            chunk_tokens = tokens[start_token:end_token]

            # Decode tokens back to text
            chunk_text = self.encoding.decode(chunk_tokens)

            # Calculate character positions (approximate)
            if chunk_index == 0:
                start_char = 0
            else:
                # Find approximate start position in original text
                prev_tokens = tokens[:start_token]
                start_char = len(self.encoding.decode(prev_tokens))

            end_char = start_char + len(chunk_text)

            # Find page number for this chunk
            page_num = self._find_page_number(start_char, page_contents) if page_contents else None

            # Create chunk
            chunks.append(
                TextChunk(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    token_count=len(chunk_tokens),
                    start_char=start_char,
                    end_char=end_char,
                    page_number=page_num
                )
            )

            # Move start position forward, accounting for overlap
            start_token = end_token - self.chunk_overlap
            chunk_index += 1

            # Prevent infinite loop if overlap >= chunk_size
            if end_token >= total_tokens:
                break

        return chunks

    def chunk_text_by_paragraphs(self, text: str) -> List[TextChunk]:
        """
        Split text by paragraphs, respecting chunk size limits.

        This method tries to keep paragraphs together when possible,
        but will split large paragraphs if they exceed chunk size.

        Args:
            text: Text to split

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        # Split into paragraphs
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        char_position = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_tokens = self.count_tokens(para)

            # If single paragraph exceeds chunk size, split it
            if para_tokens > self.chunk_size:
                # First, add any accumulated chunks
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append(
                        TextChunk(
                            content=chunk_text,
                            chunk_index=chunk_index,
                            token_count=current_tokens,
                            start_char=char_position,
                            end_char=char_position + len(chunk_text)
                        )
                    )
                    char_position += len(chunk_text) + 2
                    chunk_index += 1
                    current_chunk = []
                    current_tokens = 0

                # Split large paragraph using token-based chunking
                para_chunks = self.chunk_text(para)
                for pc in para_chunks:
                    pc.chunk_index = chunk_index
                    chunks.append(pc)
                    chunk_index += 1

            # If adding paragraph would exceed chunk size, finalize chunk
            elif current_tokens + para_tokens > self.chunk_size:
                if current_chunk:
                    chunk_text = '\n\n'.join(current_chunk)
                    chunks.append(
                        TextChunk(
                            content=chunk_text,
                            chunk_index=chunk_index,
                            token_count=current_tokens,
                            start_char=char_position,
                            end_char=char_position + len(chunk_text)
                        )
                    )
                    char_position += len(chunk_text) + 2
                    chunk_index += 1

                # Start new chunk with this paragraph
                current_chunk = [para]
                current_tokens = para_tokens

            # Add paragraph to current chunk
            else:
                current_chunk.append(para)
                current_tokens += para_tokens

        # Add remaining chunk
        if current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append(
                TextChunk(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    token_count=current_tokens,
                    start_char=char_position,
                    end_char=char_position + len(chunk_text)
                )
            )

        return chunks
