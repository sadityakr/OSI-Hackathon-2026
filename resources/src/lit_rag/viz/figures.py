"""Inline figure thumbnails into the graph as data URIs — the I/O half of "pull the figures".

``build_graph`` is pure and only carries a *relative* ``image`` path on figure/table nodes (e.g.
``figures/fig1.png``). This module — called by the CLI, which knows the parsed dir — resolves each
path, downscales it to a bounded thumbnail, and rewrites ``node["image"]`` to a self-contained
``data:image/webp;base64,…`` URI. That keeps the artifact a single portable file (same principle as
the vendored ``force-graph`` bundle): open it anywhere, no companion image folder needed.

Why thumbnails, not the raw PNGs: a paper's figures total many MB (a thesis, tens); a bounded WEBP
thumbnail is ~1-2 orders smaller and still crisp for both plots and line-art at graph/inspector zoom.
Precision-first about failure: a missing/broken image drops the ``image`` field rather than aborting.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

# defaults tuned for "readable in the inspector, cheap on the wire"
_MAX_PX = 720  # longest side of the inlined thumbnail
_QUALITY = 80  # WEBP quality (good for both photographs and axis-label line-art)


def _thumbnail_data_uri(path: Path, max_px: int, quality: int) -> str | None:
    """Downscale ``path`` to <= ``max_px`` on its longest side; return a WEBP data URI (or None)."""
    from io import BytesIO

    from PIL import Image

    try:
        with Image.open(path) as im:
            im.load()
            if im.mode not in ("RGB", "RGBA", "L"):
                im = im.convert("RGB")
            w, h = im.size
            if max(w, h) > max_px:
                scale = max_px / max(w, h)
                im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))))
            buf = BytesIO()
            # flatten alpha onto white so WEBP thumbnails don't go black on transparent PNGs
            if im.mode == "RGBA":
                bg = Image.new("RGB", im.size, (255, 255, 255))
                bg.paste(im, mask=im.split()[-1])
                im = bg
            im.save(buf, format="WEBP", quality=quality, method=4)
            return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
    except (OSError, ValueError):
        return None  # unreadable/corrupt image — drop it, never abort the render


def embed_figures(
    graph: dict[str, Any],
    base_dir: Path | str,
    *,
    max_px: int = _MAX_PX,
    quality: int = _QUALITY,
) -> int:
    """Rewrite every node's relative ``image`` path (in place) to an inlined thumbnail data URI.

    ``base_dir`` is the parsed output dir the paths are relative to. Returns the number of images
    successfully inlined; nodes whose image is missing/unreadable have their ``image`` field removed.
    """
    base = Path(base_dir)
    inlined = 0
    for node in graph.get("nodes", []):
        rel = node.get("image")
        if not rel:
            continue
        uri = _thumbnail_data_uri(base / rel, max_px, quality)
        if uri:
            node["image"] = uri
            inlined += 1
        else:
            node.pop("image", None)  # keep the node, just without a broken image
    return inlined
