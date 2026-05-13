"""Simple text chunker for splitting documents into chunks."""

import logging
import re
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk."""
    index: int
    text: str
    start_pos: int
    end_pos: int


class SimpleChunker:
    """Splits text into chunks based on paragraphs."""

    MIN_CHUNK_LENGTH = 50
    MAX_CHUNK_LENGTH = 500
    MAX_TOTAL_CHUNKS = 20

    def __init__(self, min_length: int = MIN_CHUNK_LENGTH, max_length: int = MAX_CHUNK_LENGTH):
        self.min_length = min_length
        self.max_length = max_length

    def chunk_text(self, text: str) -> List[Chunk]:
        """Split text into chunks."""
        if not text or not text.strip():
            return []

        chunks = []
        paragraphs = self._split_into_paragraphs(text)

        current_chunk = ""
        current_start = 0
        chunk_index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 1 <= self.max_length:
                if current_chunk:
                    current_chunk += "\n" + para
                else:
                    current_chunk = para
                    current_start = para.start_pos if hasattr(para, 'start_pos') else 0
            else:
                if current_chunk and len(current_chunk) >= self.min_length:
                    chunks.append(Chunk(
                        index=chunk_index,
                        text=current_chunk.strip(),
                        start_pos=current_start,
                        end_pos=current_start + len(current_chunk)
                    ))
                    chunk_index += 1

                if len(para) > self.max_length:
                    sub_chunks = self._split_long_paragraph(para, chunk_index)
                    chunks.extend(sub_chunks)
                    chunk_index += len(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = para
                    current_start = para.start_pos if hasattr(para, 'start_pos') else 0

                if len(chunks) >= self.MAX_TOTAL_CHUNKS:
                    logger.warning(f"[SimpleChunker] Reached max chunks limit: {self.MAX_TOTAL_CHUNKS}")
                    break

        if current_chunk and len(current_chunk) >= self.min_length and len(chunks) < self.MAX_TOTAL_CHUNKS:
            chunks.append(Chunk(
                index=chunk_index,
                text=current_chunk.strip(),
                start_pos=current_start,
                end_pos=current_start + len(current_chunk)
            ))

        logger.info(f"[SimpleChunker] Created {len(chunks)} chunks from text")
        return chunks

    def _split_into_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r'\n\s*\n', text)
        return [p for p in paragraphs if p.strip()]

    def _split_long_paragraph(self, text: str, start_index: int) -> list[Chunk]:
        """Split a long paragraph into smaller chunks."""
        chunks = []
        sentences = re.split(r'([.!?])\s+', text)

        current = ""
        idx = start_index

        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")

            if len(current) + len(sentence) <= self.max_length:
                current += " " + sentence if current else sentence
            else:
                if current:
                    chunks.append(Chunk(
                        index=idx,
                        text=current.strip(),
                        start_pos=0,
                        end_pos=len(current)
                    ))
                    idx += 1
                current = sentence

        if current:
            chunks.append(Chunk(
                index=idx,
                text=current.strip(),
                start_pos=0,
                end_pos=len(current)
            ))

        return chunks
