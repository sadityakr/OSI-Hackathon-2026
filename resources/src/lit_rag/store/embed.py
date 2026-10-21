"""SciNCL embedder — chunk text → 768-d vectors (M5).

SciNCL (``malteos/scincl``) is a SciBERT-initialised model trained with a citation-graph contrastive
objective: papers that cite each other land near each other in space, which is exactly the neighbour
structure scientific retrieval wants. It is a BERT encoder, so the document embedding is the **[CLS]**
token of the final layer (the SPECTER/SciNCL convention), not mean pooling.

Thin and lazy: ``transformers`` + ``torch`` (already pulled in by Docling) load on first ``encode``,
never at import, so the offline gate stays fast. CPU by default for the prototype; ``device="cuda"``
caps VRAM first, honouring the shared-box rule (same pattern as the parser's formula VLM).
"""

from __future__ import annotations

EMBED_DIM = 768
_MAX_TOKENS = 512  # BERT context window


class SciNCLEmbedder:
    """Lazy-loading SciNCL encoder. ``encode(list[str]) -> list[list[float]]`` (one 768-d vec each)."""

    def __init__(
        self,
        model_name: str = "malteos/scincl",
        device: str = "cpu",
        *,
        batch_size: int = 16,
        vram_fraction: float = 0.4,
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.vram_fraction = vram_fraction
        self._tok = None
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        import torch
        from transformers import AutoModel, AutoTokenizer

        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.set_per_process_memory_fraction(
                self.vram_fraction, 0
            )  # never OOM a co-tenant
        self._tok = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModel.from_pretrained(self.model_name).to(self.device).eval()

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Embed ``texts`` into 768-d SciNCL vectors (CLS pooling), batched, no grad."""
        if not texts:
            return []
        self._load()
        import torch

        out: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            enc = self._tok(
                batch,
                padding=True,
                truncation=True,
                max_length=_MAX_TOKENS,
                return_tensors="pt",
            ).to(self.device)
            with torch.no_grad():
                cls = self._model(**enc).last_hidden_state[:, 0, :]  # [CLS]
            out.extend(cls.cpu().tolist())
        return out
