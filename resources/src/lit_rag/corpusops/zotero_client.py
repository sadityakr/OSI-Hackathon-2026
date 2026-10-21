"""Read-only Zotero client: local API (desktop) or web API (server), same read surface.

Independent of the ``~/.claude/skills/lit`` family — lit-RAG must stay self-contained (portable to
the JGU VM, no dependency on a personal laptop skill or the Obsidian vault), so this is a deliberate
small duplication of the read protocol, not a shared import. It reads exactly what the corpus
pipeline needs: collection tree, item metadata, and the bytes of a PDF attachment.

Two backends, one interface:
    local (default) — the Zotero *desktop app* must be running; served at 127.0.0.1:23119, no key.
        A PDF attachment is read straight off local disk (``~/Zotero/storage/<key>/<filename>``).
    web (``via_web=True``) — api.zotero.org, needs ``ZOTERO_API_KEY``. No desktop app required, so
        this is the only mode that works headless (a server / the JGU VM). A PDF attachment is
        downloaded over HTTP through the ``/items/{key}/file`` endpoint (Zotero redirects imported
        attachments to S3).

Input:
    A group id; for web mode, an API key (env ``ZOTERO_API_KEY`` if not passed explicitly).
Process:
    Paginated GETs (limit 100, start offset) until a short page. Local connection failures raise a
    clear "start Zotero desktop" message; web failures surface the HTTP status.
Output:
    Parsed JSON lists/dicts exactly as the API returns them. ``pdf_bytes()`` returns the attachment's
    raw bytes, or None if the item has no PDF attachment reachable in the current mode (e.g. a
    linked_file path on someone else's machine, unreachable over the web API — abstain, don't guess).
"""

from __future__ import annotations

import os
from pathlib import Path

import requests

LOCAL_BASE = "http://127.0.0.1:23119/api"  # not "localhost": DNS resolution can add ~2s/call
WEB_BASE = "https://api.zotero.org"
PAGE = 100


def _default_storage_dir() -> str:
    return str(Path.home() / "Zotero" / "storage")


class ZoteroClient:
    """Read-only access to one Zotero group library, local or web API."""

    def __init__(
        self,
        group_id: int,
        via_web: bool = False,
        api_key: str | None = None,
        storage_dir: str | None = None,
    ):
        self.group_id = int(group_id)
        self.via_web = via_web
        self._session = requests.Session()
        if via_web:
            key = api_key or os.environ.get("ZOTERO_API_KEY")
            if not key:
                raise RuntimeError("Web-API reads need an API key (ZOTERO_API_KEY).")
            self.base = f"{WEB_BASE}/groups/{self.group_id}"
            self._session.headers.update({"Zotero-API-Key": key, "Zotero-API-Version": "3"})
        else:
            self.base = f"{LOCAL_BASE}/groups/{self.group_id}"
            self.storage_dir = storage_dir or os.environ.get("ZOTERO_STORAGE_DIR") or _default_storage_dir()

    def _get(self, path: str, params: dict | None = None, **kwargs) -> requests.Response:
        try:
            return self._session.get(self.base + path, params=params, timeout=30, **kwargs)
        except requests.exceptions.ConnectionError as exc:
            if not self.via_web:
                raise RuntimeError(
                    "Cannot reach the Zotero local API at 127.0.0.1:23119. "
                    "Start the Zotero desktop app and retry."
                ) from exc
            raise RuntimeError(f"Cannot reach api.zotero.org: {type(exc).__name__}") from exc

    def _get_all(self, path: str, params: dict | None = None) -> list:
        out, start = [], 0
        while True:
            page_params = {"format": "json", "limit": PAGE, "start": start}
            page_params.update(params or {})
            r = self._get(path, page_params)
            r.raise_for_status()
            batch = r.json()
            out.extend(batch)
            if len(batch) < PAGE:
                return out
            start += PAGE

    def collection(self, key: str) -> dict:
        r = self._get(f"/collections/{key}")
        r.raise_for_status()
        return r.json()["data"]

    def subcollections(self, key: str) -> list:
        """Direct child collections of ``key`` (not the whole subtree)."""
        return self._get_all(f"/collections/{key}/collections")

    def collection_items_top(self, key: str) -> list:
        """Top-level items of one collection (no attachments/notes)."""
        return self._get_all(f"/collections/{key}/items/top")

    def children(self, item_key: str) -> list:
        """Child items (attachments, notes) of one item."""
        return self._get_all(f"/items/{item_key}/children")

    def find_pdf_attachment(self, item: dict, children: list) -> dict | None:
        """The first PDF attachment's raw item dict for ``item`` (itself, or among its children)."""
        data = item.get("data", {})
        if data.get("itemType") == "attachment" and data.get("contentType") == "application/pdf":
            return item
        for child in children:
            cdata = child.get("data", {})
            if cdata.get("itemType") == "attachment" and cdata.get("contentType") == "application/pdf":
                return child
        return None

    def pdf_bytes(self, attachment: dict) -> bytes | None:
        """Raw bytes of a PDF attachment (as returned by find_pdf_attachment), or None if unreachable."""
        data = attachment.get("data", {})
        mode = data.get("linkMode", "")
        key = attachment["key"]
        if self.via_web:
            if mode not in ("imported_file", "imported_url"):
                return None  # linked_file points at a path on someone else's machine — abstain
            r = self._get(f"/items/{key}/file", params=None)
            if r.status_code != 200:
                return None
            return r.content
        if mode in ("imported_file", "imported_url") and data.get("filename"):
            p = Path(self.storage_dir) / key / data["filename"]
            return p.read_bytes() if p.is_file() else None
        if mode == "linked_file" and data.get("path"):
            p = Path(str(data["path"]))
            return p.read_bytes() if p.is_file() else None
        return None
