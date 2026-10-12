import hashlib
import io
import re
from pathlib import Path
from typing import Optional
from pypdf import PdfReader
from docx import Document as DocxDocument
import tiktoken

class ChunkData:
    def __init__(
        self,
        text: str,
        chunk_index: int,
        page_number: Optional[int] = None,
        section_heading: Optional[str] = None,
        token_count: int = 0
    ):
        self.text = text.strip()
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.section_heading = section_heading
        self.token_count = token_count

class IngestionService:
    def __init__(self, chunk_size: int = 400, overlap: int = 60):
        self.chunk_size = chunk_size
        self.overlap = overlap
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text, disallowed_special=()))
        return len(text.split())

    def compute_sha256(self, content_bytes: bytes) -> str:
        return hashlib.sha256(content_bytes).hexdigest()

    def parse_pdf(self, file_bytes: bytes) -> list[tuple[int, Optional[str], str]]:
        """Returns list of (page_num, heading, text)"""
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_content = []
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                # Attempt to extract first line or capitalized header as section heading
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                heading = lines[0][:80] if lines else None
                pages_content.append((idx + 1, heading, text))
        return pages_content

    def parse_docx(self, file_bytes: bytes) -> list[tuple[int, Optional[str], str]]:
        doc = DocxDocument(io.BytesIO(file_bytes))
        sections = []
        current_heading = "General"
        current_text = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if p.style and p.style.name and p.style.name.startswith("Heading"):
                if current_text:
                    sections.append((1, current_heading, "\n".join(current_text)))
                    current_text = []
                current_heading = text[:100]
            else:
                current_text.append(text)

        if current_text:
            sections.append((1, current_heading, "\n".join(current_text)))

        return sections if sections else [(1, None, "")]

    def parse_markdown(self, text: str) -> list[tuple[int, Optional[str], str]]:
        lines = text.split("\n")
        sections = []
        current_heading = "Overview"
        current_text = []

        for line in lines:
            header_match = re.match(r"^(#{1,6})\s+(.*)$", line.strip())
            if header_match:
                if current_text:
                    sections.append((1, current_heading, "\n".join(current_text)))
                    current_text = []
                current_heading = header_match.group(2).strip()[:100]
            else:
                current_text.append(line)

        if current_text:
            sections.append((1, current_heading, "\n".join(current_text)))

        return sections if sections else [(1, None, text)]

    def parse_txt(self, text: str) -> list[tuple[int, Optional[str], str]]:
        return [(1, None, text)]

    def chunk_text(
        self,
        sections: list[tuple[int, Optional[str], str]]
    ) -> list[ChunkData]:
        """
        Split document sections into overlapping chunks of ~300-500 tokens
        preserving page numbers and section headings.
        """
        chunks: list[ChunkData] = []
        chunk_idx = 0

        for page_num, heading, raw_text in sections:
            paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [raw_text] if raw_text.strip() else []

            buffer_tokens = []
            buffer_words = []

            for p in paragraphs:
                words = p.split()
                if not words:
                    continue

                for word in words:
                    buffer_words.append(word)
                    # Check token count periodically
                    if len(buffer_words) >= self.chunk_size:
                        chunk_text = " ".join(buffer_words)
                        token_count = self.count_tokens(chunk_text)
                        
                        chunks.append(ChunkData(
                            text=chunk_text,
                            chunk_index=chunk_idx,
                            page_number=page_num,
                            section_heading=heading,
                            token_count=token_count
                        ))
                        chunk_idx += 1
                        
                        # Apply overlap by keeping the trailing words
                        overlap_word_count = min(self.overlap, len(buffer_words) // 2)
                        buffer_words = buffer_words[-overlap_word_count:]

            if buffer_words:
                chunk_text = " ".join(buffer_words)
                token_count = self.count_tokens(chunk_text)
                if token_count > 15:  # Ignore trivial trailing stubs
                    chunks.append(ChunkData(
                        text=chunk_text,
                        chunk_index=chunk_idx,
                        page_number=page_num,
                        section_heading=heading,
                        token_count=token_count
                    ))
                    chunk_idx += 1

        return chunks

    def process_file(
        self,
        filename: str,
        content_bytes: bytes
    ) -> tuple[list[ChunkData], int]:
        """
        Parses and chunks file content according to its extension.
        Returns: (chunks, page_count)
        """
        ext = Path(filename).suffix.lower()
        sections: list[tuple[int, Optional[str], str]] = []
        page_count = 1

        if ext == ".pdf":
            sections = self.parse_pdf(content_bytes)
            page_count = max([s[0] for s in sections], default=1)
        elif ext == ".docx":
            sections = self.parse_docx(content_bytes)
            page_count = 1
        elif ext == ".md":
            text = content_bytes.decode("utf-8", errors="replace")
            sections = self.parse_markdown(text)
            page_count = 1
        elif ext == ".txt":
            text = content_bytes.decode("utf-8", errors="replace")
            sections = self.parse_txt(text)
            page_count = 1
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        chunks = self.chunk_text(sections)
        return chunks, page_count
