"""Document loaders for various file types."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict
import fitz  # PyMuPDF


class LoadedDocument:
    """Container for loaded document data."""

    def __init__(
        self,
        content: str,
        file_path: str,
        file_type: str,
        title: Optional[str] = None,
        metadata: Optional[dict] = None,
        page_contents: Optional[List[Dict[str, any]]] = None
    ):
        self.content = content
        self.file_path = file_path
        self.file_type = file_type
        self.title = title or Path(file_path).stem
        self.metadata = metadata or {}
        # page_contents: [{'page': 1, 'content': '...'}, ...]
        self.page_contents = page_contents or []


class DocumentLoader(ABC):
    """Abstract base class for document loaders."""

    @abstractmethod
    def load(self, file_path: str) -> LoadedDocument:
        """Load a document from the given file path."""
        pass

    @staticmethod
    def detect_file_type(file_path: str) -> str:
        """Detect file type from extension."""
        ext = Path(file_path).suffix.lower()
        return ext.lstrip('.')


class PDFLoader(DocumentLoader):
    """Loader for PDF documents using PyMuPDF."""

    def load(self, file_path: str) -> LoadedDocument:
        """Load text from PDF file with page tracking."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        text_content = []
        page_contents = []
        metadata = {"page_count": 0}

        # Open PDF with PyMuPDF (fitz)
        doc = fitz.open(file_path)
        metadata["page_count"] = len(doc)

        for page_num in range(len(doc)):
            page = doc[page_num]
            # Extract text with better layout preservation
            text = page.get_text("text")

            if text.strip():
                # Store page content with page number
                page_content = f"[Page {page_num + 1}]\n{text}"
                text_content.append(page_content)

                # Track page-specific content for chunking
                page_contents.append({
                    'page': page_num + 1,
                    'content': text,
                    'char_start': sum(len(p) for p in text_content[:-1]),
                    'char_end': sum(len(p) for p in text_content)
                })

        doc.close()
        content = "\n\n".join(text_content)

        return LoadedDocument(
            content=content,
            file_path=str(path.absolute()),
            file_type="pdf",
            metadata=metadata,
            page_contents=page_contents
        )


class MarkdownLoader(DocumentLoader):
    """Loader for Markdown documents."""

    def load(self, file_path: str) -> LoadedDocument:
        """Load text from Markdown file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title from first heading if present
        title = None
        lines = content.split('\n')
        for line in lines:
            if line.startswith('#'):
                title = line.lstrip('#').strip()
                break

        return LoadedDocument(
            content=content,
            file_path=str(path.absolute()),
            file_type="md",
            title=title
        )


class TextLoader(DocumentLoader):
    """Loader for plain text documents."""

    def load(self, file_path: str) -> LoadedDocument:
        """Load text from plain text file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return LoadedDocument(
            content=content,
            file_path=str(path.absolute()),
            file_type=self.detect_file_type(file_path)
        )


class CodeLoader(DocumentLoader):
    """Loader for code files."""

    CODE_EXTENSIONS = {
        'py', 'js', 'ts', 'tsx', 'jsx', 'java', 'cpp', 'c', 'h',
        'hpp', 'cs', 'go', 'rs', 'rb', 'php', 'swift', 'kt', 'scala'
    }

    def load(self, file_path: str) -> LoadedDocument:
        """Load text from code file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Code file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        file_type = self.detect_file_type(file_path)

        return LoadedDocument(
            content=content,
            file_path=str(path.absolute()),
            file_type=file_type,
            metadata={"language": file_type}
        )


class DocumentLoaderFactory:
    """Factory for creating appropriate document loaders."""

    @staticmethod
    def get_loader(file_path: str) -> DocumentLoader:
        """Get appropriate loader for the file type."""
        ext = Path(file_path).suffix.lower().lstrip('.')

        if ext == 'pdf':
            return PDFLoader()
        elif ext in ['md', 'markdown']:
            return MarkdownLoader()
        elif ext in CodeLoader.CODE_EXTENSIONS:
            return CodeLoader()
        elif ext in ['txt', 'text', 'log', 'csv', 'json', 'xml', 'html']:
            return TextLoader()
        else:
            # Default to text loader for unknown types
            return TextLoader()

    @staticmethod
    def is_supported(file_path: str) -> bool:
        """Check if file type is supported."""
        ext = Path(file_path).suffix.lower().lstrip('.')
        supported = (
            ext in ['pdf', 'md', 'markdown', 'txt', 'text', 'log',
                    'csv', 'json', 'xml', 'html']
            or ext in CodeLoader.CODE_EXTENSIONS
        )
        return supported
