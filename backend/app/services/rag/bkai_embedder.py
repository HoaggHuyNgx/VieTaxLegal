"""BKAI ``vietnamese-bi-encoder`` on CPU (comparison model, experiment 4).

Needs the optional extra ``pip install -e ".[local-embed]"`` (sentence-transformers + pyvi); the
imports are lazy so the app, CI and tests never load torch. Input is NFC-normalised and
word-segmented here, identically for documents and queries. The model truncates at 256 tokens, so
use the ``article_s256`` chunk set and the short heading prefix (``short_prefix = True``).
"""

import asyncio
import unicodedata
from collections.abc import Callable
from typing import Any

from app.services.rag.embeddings import EmbeddingBatch

DEFAULT_DIMS = 768


class BkaiEmbedder:
    name = "bkai"
    short_prefix = True

    def __init__(
        self,
        model: str,
        batch_size: int = 16,
        *,
        encoder: Any = None,
        segmenter: Callable[[str], str] | None = None,
    ) -> None:
        self.model, self._batch_size = model, batch_size
        self._encoder, self._segmenter = encoder, segmenter
        self.dims = encoder.get_sentence_embedding_dimension() if encoder else DEFAULT_DIMS

    def _load(self) -> None:
        if self._encoder is None:
            from sentence_transformers import SentenceTransformer

            self._encoder = SentenceTransformer(self.model, device="cpu", trust_remote_code=False)
            self.dims = self._encoder.get_sentence_embedding_dimension()
        if self._segmenter is None:
            from pyvi import ViTokenizer

            self._segmenter = ViTokenizer.tokenize

    def _prepare(self, text: str) -> str:
        assert self._segmenter is not None
        return self._segmenter(unicodedata.normalize("NFC", text))

    def embed_documents(self, texts: list[str]) -> EmbeddingBatch:
        self._load()
        segmented = [self._prepare(text) for text in texts]
        vectors = self._encoder.encode(
            segmented, batch_size=self._batch_size, normalize_embeddings=True
        )
        return EmbeddingBatch(
            [list(map(float, v)) for v in vectors], sum(map(len, map(str.split, segmented)))
        )

    async def aembed_query(self, text: str) -> list[float]:
        batch = await asyncio.to_thread(self.embed_documents, [text])
        return batch.vectors[0]
