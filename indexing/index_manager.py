"""Index manager to orchestrate the document indexing pipeline."""
import json
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from storage.db_storage import ArticleStorage
from storage.models import Document, Chunk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .loaders import DocumentLoaderFactory, LoadedDocument
from .chunker import TextChunker
from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore


class IndexManager:
    """Manages the document indexing pipeline."""

    def __init__(
        self,
        db_path: str = "db/articles.sqlite",
        index_path: str = "indexes/documents.faiss",
        metadata_path: str = "indexes/metadata.json",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize index manager.

        Args:
            db_path: Path to SQLite database
            index_path: Path to FAISS index file
            metadata_path: Path to metadata JSON file
            chunk_size: Size of text chunks in tokens
            chunk_overlap: Overlap between chunks in tokens
            embedding_model: OpenAI embedding model to use
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        from storage.models import Base
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Initialize components
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.embedder = EmbeddingGenerator(model=embedding_model)
        self.vector_store = VectorStore(
            dimension=self.embedder.get_dimension(),
            index_path=index_path,
            metadata_path=metadata_path
        )

    def index_document(
        self,
        file_path: str,
        use_paragraph_chunking: bool = False
    ) -> Optional[int]:
        """
        Index a single document.

        Args:
            file_path: Path to document file
            use_paragraph_chunking: Use paragraph-aware chunking

        Returns:
            Document ID if successful, None otherwise
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")

        # Check if already indexed
        session = self.SessionLocal()
        try:
            existing = session.query(Document).filter(
                Document.file_path == str(path.absolute())
            ).first()

            if existing:
                print(f"Document already indexed: {file_path}")
                return existing.id

            # Load document
            loader = DocumentLoaderFactory.get_loader(file_path)
            loaded_doc = loader.load(file_path)

            # Chunk text based on file type
            if use_paragraph_chunking:
                chunks = self.chunker.chunk_text_by_paragraphs(
                    loaded_doc.content
                )
            elif loaded_doc.file_type in ['md', 'markdown']:
                # Use heading-aware chunking for markdown
                chunks = self.chunker.chunk_markdown_by_headings(
                    loaded_doc.content
                )
            else:
                chunks = self.chunker.chunk_text(
                    loaded_doc.content,
                    page_contents=loaded_doc.page_contents
                )

            if not chunks:
                print(f"No chunks generated for: {file_path}")
                return None

            # Create document record
            doc = Document(
                file_path=str(path.absolute()),
                file_type=loaded_doc.file_type,
                title=loaded_doc.title,
                content=loaded_doc.content,
                meta_data=json.dumps(loaded_doc.metadata),
                indexed_at=datetime.now()
            )
            session.add(doc)
            session.flush()

            # Generate embeddings for all chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedder.generate_embeddings_batch(chunk_texts)

            # Store chunks in database and vector store
            chunk_metadata = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Save chunk to database
                chunk_record = Chunk(
                    document_id=doc.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    embedding_model=self.embedder.model,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    created_at=datetime.now()
                )
                session.add(chunk_record)
                session.flush()

                # Prepare metadata for vector store
                chunk_metadata.append({
                    'chunk_id': chunk_record.id,
                    'document_id': doc.id,
                    'file_path': doc.file_path,
                    'title': doc.title,
                    'chunk_index': chunk.chunk_index,
                    'content': chunk.content[:200],
                    'page_number': chunk.page_number,
                    'section_title': chunk.section_title
                })

            # Add to vector store
            self.vector_store.add_embeddings(embeddings, chunk_metadata)
            self.vector_store.save()

            session.commit()
            return doc.id

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def index_directory(
        self,
        directory: str,
        recursive: bool = True,
        file_types: Optional[List[str]] = None
    ) -> List[int]:
        """
        Index all supported documents in a directory.

        Args:
            directory: Directory path
            recursive: Search recursively
            file_types: List of file extensions to include (None = all)

        Returns:
            List of document IDs
        """
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Invalid directory: {directory}")

        indexed_ids = []
        pattern = '**/*' if recursive else '*'

        for file_path in dir_path.glob(pattern):
            if not file_path.is_file():
                continue

            # Check file type filter
            if file_types:
                ext = file_path.suffix.lower().lstrip('.')
                if ext not in file_types:
                    continue

            # Check if supported
            if not DocumentLoaderFactory.is_supported(str(file_path)):
                continue

            try:
                print(f"Indexing: {file_path}")
                doc_id = self.index_document(str(file_path))
                if doc_id:
                    indexed_ids.append(doc_id)
            except Exception as e:
                print(f"Error indexing {file_path}: {e}")
                continue

        return indexed_ids

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[dict, float]]:
        """
        Search indexed documents.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (result_dict, similarity_score) tuples
        """
        # Generate query embedding
        query_embedding = self.embedder.generate_embedding(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, top_k)

        # Retrieve full content from database for each result
        session = self.SessionLocal()
        try:
            enriched_results = []
            for metadata, score in results:
                chunk_id = metadata.get('chunk_id')
                if chunk_id:
                    # Get full chunk content from database
                    chunk = session.query(Chunk).filter(
                        Chunk.id == chunk_id
                    ).first()
                    if chunk:
                        # Replace truncated content with full content
                        enriched_metadata = metadata.copy()
                        enriched_metadata['content'] = chunk.content
                        enriched_results.append((enriched_metadata, score))
                    else:
                        enriched_results.append((metadata, score))
                else:
                    enriched_results.append((metadata, score))

            return enriched_results
        finally:
            session.close()

    def delete_document(self, document_id: int) -> bool:
        """
        Delete a document and its chunks from the index.

        Args:
            document_id: Document ID to delete

        Returns:
            True if deleted, False otherwise
        """
        session = self.SessionLocal()
        try:
            doc = session.query(Document).filter(
                Document.id == document_id
            ).first()

            if not doc:
                return False

            # Delete from database (cascades to chunks)
            session.delete(doc)
            session.commit()

            # Remove from vector store
            self.vector_store.remove_by_document_id(document_id)
            self.vector_store.save()

            return True

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def list_documents(self, limit: Optional[int] = None) -> List[dict]:
        """
        List all indexed documents.

        Args:
            limit: Maximum number to return

        Returns:
            List of document dictionaries
        """
        session = self.SessionLocal()
        try:
            query = session.query(Document).order_by(
                Document.indexed_at.desc()
            )
            if limit:
                query = query.limit(limit)

            docs = query.all()
            return [doc.to_dict() for doc in docs]

        finally:
            session.close()

    def get_stats(self) -> dict:
        """Get indexing statistics."""
        session = self.SessionLocal()
        try:
            total_docs = session.query(Document).count()
            total_chunks = session.query(Chunk).count()

            vector_stats = self.vector_store.get_stats()

            return {
                "total_documents": total_docs,
                "total_chunks": total_chunks,
                "vector_store": vector_stats,
                "database_path": str(self.db_path.absolute()),
                "database_size_bytes": (
                    self.db_path.stat().st_size
                    if self.db_path.exists() else 0
                )
            }

        finally:
            session.close()

    def reindex_document(self, document_id: int) -> bool:
        """
        Reindex a specific document.

        Args:
            document_id: Document ID to reindex

        Returns:
            True if successful
        """
        session = self.SessionLocal()
        try:
            doc = session.query(Document).filter(
                Document.id == document_id
            ).first()

            if not doc:
                return False

            file_path = doc.file_path

            # Delete old index
            self.delete_document(document_id)

            # Reindex
            new_id = self.index_document(file_path)
            return new_id is not None

        finally:
            session.close()

    def reindex_all(self):
        """Reindex all documents."""
        session = self.SessionLocal()
        try:
            docs = session.query(Document).all()
            file_paths = [doc.file_path for doc in docs]

            # Clear everything
            self.vector_store.clear()

            for doc in docs:
                session.delete(doc)
            session.commit()

            # Reindex all
            for file_path in file_paths:
                try:
                    print(f"Reindexing: {file_path}")
                    self.index_document(file_path)
                except Exception as e:
                    print(f"Error reindexing {file_path}: {e}")

        finally:
            session.close()
