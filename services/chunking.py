"""Document chunking service with sentence awareness and metadata preservation."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Union
from services.document_loader import ExtractedDocument, DocumentPage
from services.text_processor import TextProcessor
from utils.config import Config


@dataclass
class DocumentChunk:
    """Represents a discrete semantic chunk of text from a document."""
    chunk_id: str
    doc_id: str
    file_name: str
    file_type: str
    page_number: Union[int, str]
    chunk_index: int
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk into dictionary format for storage/display."""
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "page_number": str(self.page_number),
            "chunk_index": self.chunk_index,
            "text": self.text,
            "char_count": self.char_count,
            "word_count": self.word_count,
            **self.metadata,
        }


class ChunkingService:
    """Handles splitting of documents and text into overlapping chunks with metadata."""

    def __init__(
        self,
        chunk_size: int = Config.DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = Config.DEFAULT_CHUNK_OVERLAP,
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly smaller than chunk_size ({chunk_size})."
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: ExtractedDocument) -> List[DocumentChunk]:
        """Chunk an ExtractedDocument while preserving page and source metadata.

        Args:
            document: ExtractedDocument to chunk.

        Returns:
            List of DocumentChunk instances.
        """
        all_chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        for page in document.pages:
            page_text = TextProcessor.clean_text(page.text)
            if not page_text:
                continue

            # Chunk the page text
            page_chunks = self._chunk_text(
                text=page_text,
                doc_id=document.doc_id,
                file_name=document.file_name,
                file_type=document.file_type,
                page_number=page.page_number,
                start_index=global_chunk_idx,
            )

            for chunk in page_chunks:
                # Merge page and document metadata
                chunk.metadata.update(page.metadata)
                chunk.metadata.update({
                    "doc_id": document.doc_id,
                    "file_name": document.file_name,
                    "file_type": document.file_type,
                    "page_number": str(page.page_number),
                })
                all_chunks.append(chunk)
                global_chunk_idx += 1

        # Fallback: if document had text but pages were somehow empty
        if not all_chunks and document.full_text.strip():
            all_chunks = self._chunk_text(
                text=TextProcessor.clean_text(document.full_text),
                doc_id=document.doc_id,
                file_name=document.file_name,
                file_type=document.file_type,
                page_number=1,
                start_index=0,
            )

        return all_chunks

    def _chunk_text(
        self,
        text: str,
        doc_id: str,
        file_name: str,
        file_type: str,
        page_number: Union[int, str],
        start_index: int = 0,
    ) -> List[DocumentChunk]:
        """Split a text block into sentence-aware overlapping chunks."""
        if len(text) <= self.chunk_size:
            chunk_id = f"{doc_id}_c{start_index}"
            return [
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    file_name=file_name,
                    file_type=file_type,
                    page_number=page_number,
                    chunk_index=start_index,
                    text=text,
                    metadata={"page_number": str(page_number), "file_name": file_name},
                )
            ]

        sentences = TextProcessor.segment_sentences(text)
        if not sentences:
            sentences = [text]

        chunks: List[DocumentChunk] = []
        current_sentences: List[str] = []
        current_len = 0
        chunk_idx = start_index

        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_len = len(sentence)

            # If a single sentence exceeds chunk_size, split by characters
            if sentence_len > self.chunk_size:
                if current_sentences:
                    chunk_text = " ".join(current_sentences).strip()
                    if chunk_text:
                        chunks.append(
                            DocumentChunk(
                                chunk_id=f"{doc_id}_c{chunk_idx}",
                                doc_id=doc_id,
                                file_name=file_name,
                                file_type=file_type,
                                page_number=page_number,
                                chunk_index=chunk_idx,
                                text=chunk_text,
                                metadata={"page_number": str(page_number), "file_name": file_name},
                            )
                        )
                        chunk_idx += 1
                        current_sentences = []
                        current_len = 0

                # Subsplit oversized sentence
                sub_chunks = self._split_large_sentence(sentence)
                for sub in sub_chunks:
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{doc_id}_c{chunk_idx}",
                            doc_id=doc_id,
                            file_name=file_name,
                            file_type=file_type,
                            page_number=page_number,
                            chunk_index=chunk_idx,
                            text=sub,
                            metadata={"page_number": str(page_number), "file_name": file_name},
                        )
                    )
                    chunk_idx += 1
                i += 1
                continue

            # Check if adding this sentence exceeds chunk size
            projected_len = current_len + sentence_len + (1 if current_sentences else 0)

            if projected_len <= self.chunk_size:
                current_sentences.append(sentence)
                current_len = projected_len
                i += 1
            else:
                # Flush current chunk
                chunk_text = " ".join(current_sentences).strip()
                if chunk_text:
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{doc_id}_c{chunk_idx}",
                            doc_id=doc_id,
                            file_name=file_name,
                            file_type=file_type,
                            page_number=page_number,
                            chunk_index=chunk_idx,
                            text=chunk_text,
                            metadata={"page_number": str(page_number), "file_name": file_name},
                        )
                    )
                    chunk_idx += 1

                # Calculate overlap: take sentences from end of current_sentences
                overlap_sentences = []
                overlap_len = 0
                for prev_sent in reversed(current_sentences):
                    if overlap_len + len(prev_sent) + 1 <= self.chunk_overlap:
                        overlap_sentences.insert(0, prev_sent)
                        overlap_len += len(prev_sent) + 1
                    else:
                        break

                current_sentences = overlap_sentences
                current_len = sum(len(s) for s in current_sentences) + max(0, len(current_sentences) - 1)
                # Next loop iteration will add sentence i

        # Remaining sentences
        if current_sentences:
            chunk_text = " ".join(current_sentences).strip()
            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{doc_id}_c{chunk_idx}",
                        doc_id=doc_id,
                        file_name=file_name,
                        file_type=file_type,
                        page_number=page_number,
                        chunk_index=chunk_idx,
                        text=chunk_text,
                        metadata={"page_number": str(page_number), "file_name": file_name},
                    )
                )

        return chunks

    def _split_large_sentence(self, text: str) -> List[str]:
        """Split an exceptionally large sentence using word boundaries."""
        words = text.split(" ")
        sub_chunks = []
        cur_words = []
        cur_len = 0

        for word in words:
            if cur_len + len(word) + 1 <= self.chunk_size:
                cur_words.append(word)
                cur_len += len(word) + 1
            else:
                if cur_words:
                    sub_chunks.append(" ".join(cur_words))
                cur_words = [word]
                cur_len = len(word)

        if cur_words:
            sub_chunks.append(" ".join(cur_words))

        return sub_chunks
