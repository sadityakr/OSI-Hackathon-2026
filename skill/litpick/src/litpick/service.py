"""The operations, shared by the MCP server and the command-line tool. Each returns plain dicts."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from . import PARSER_VERSION, library as lib
from .arxiv import ArxivError, download_pdf, fetch_meta, parse_id
from .parse import normalise_label, parse_pdf, render
from .paths import library_home, safe_name


class LitpickError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _summary(con, key: str, status: str) -> dict:
    p = lib.get_paper(con, key)
    figs = lib.figures_of(con, key)
    return {
        "status": status,
        "paper": key,
        "title": p["title"],
        "authors": json.loads(p["authors"] or "[]")[:6],
        "year": p["year"],
        "pages": p["pages"],
        "figures": [{"figure": f["label"], "page": f["page"], "region": f["method"],
                     "caption": f["caption"][:160]} for f in figs],
    }


def _parse_and_store(con, *, key, source, base_id, version, title, authors, year, pdf, origin):
    parsed = parse_pdf(pdf)
    lib.save_paper(
        con, key=key, source=source, base_id=base_id, version=version,
        title=title or parsed.title_guess, authors=authors, year=year, sha256=_sha256(pdf),
        pages=parsed.pages, parser_version=PARSER_VERSION, origin=origin, figures=parsed.figures,
    )


def ingest(ref: str, force: bool = False) -> dict:
    """Open a paper: an arXiv id or URL, or the path of a PDF on this computer.

    Returns at once ('cached') when the paper is already in the library and was parsed by the
    current parser. force=True downloads (arXiv) and parses again.
    """
    ref = ref.strip().strip('"')
    local = Path(ref).expanduser()
    with lib.connect() as con:
        if local.suffix.lower() == ".pdf" and local.is_file():
            sha = _sha256(local)
            key = "local-" + sha[:12]
            row = lib.get_paper(con, key)
            if row and row["parser_version"] == PARSER_VERSION and not force:
                return _summary(con, key, "cached")
            dest = lib.paper_dir(key) / "paper.pdf"
            if local.resolve() != dest.resolve():
                shutil.copyfile(local, dest)
            _parse_and_store(con, key=key, source="local", base_id=None, version=None, title="",
                             authors=[], year=None, pdf=dest, origin=str(local.resolve()))
            return _summary(con, key, "parsed")

        aid = parse_id(ref)
        if aid is None:
            raise LitpickError(f"'{ref}' is neither an arXiv id/URL nor an existing .pdf file")

        if not force:  # answer from the library without touching the network when possible
            row = lib.get_paper(con, aid.full) if aid.version else lib.latest_for_base(con, aid.base)
            if row and row["parser_version"] == PARSER_VERSION:
                return _summary(con, row["key"], "cached")
            if row:  # stored, but by an older parser: parse the PDF we already have
                pdf = lib.paper_dir(row["key"]) / "paper.pdf"
                if pdf.is_file():
                    _parse_and_store(con, key=row["key"], source="arxiv", base_id=row["base_id"],
                                     version=row["version"], title=row["title"],
                                     authors=json.loads(row["authors"] or "[]"), year=row["year"],
                                     pdf=pdf, origin=row["origin"])
                    return _summary(con, row["key"], "reparsed")

        try:
            meta = fetch_meta(aid)
            pdf = lib.paper_dir(meta.full) / "paper.pdf"
            if force or not pdf.is_file():
                download_pdf(meta.full, pdf)
        except ArxivError as e:
            raise LitpickError(str(e)) from e
        _parse_and_store(con, key=meta.full, source="arxiv", base_id=meta.base, version=meta.version,
                         title=meta.title, authors=meta.authors, year=meta.year, pdf=pdf,
                         origin=f"https://arxiv.org/abs/{meta.full}")
        return _summary(con, meta.full, "parsed")


def _need_key(con, ref: str) -> str:
    key = lib.resolve_key(con, ref.strip())
    if not key:
        raise LitpickError(f"'{ref}' is not in the library yet. Open it with ingest first.")
    return key


def list_figures(ref: str) -> dict:
    with lib.connect() as con:
        key = _need_key(con, ref)
        p = lib.get_paper(con, key)
        return {"paper": key, "title": p["title"], "figures": [
            {"figure": f["label"], "page": f["page"], "region": f["method"], "caption": f["caption"],
             "discussed_in": f["mentions"][:4]} for f in lib.figures_of(con, key)]}


def cite_as(paper_row, label: str) -> str:
    authors = json.loads(paper_row["authors"] or "[]")
    fig = f"Fig. {label}" if not label.startswith(("S", "ED")) else (
        f"Fig. {label}" if label.startswith("S") else f"Extended Data Fig. {label[2:]}")
    if paper_row["source"] == "arxiv":
        who = (authors[0].split()[-1] + (" et al." if len(authors) > 1 else "")) if authors else "Anon."
        return f"{who} ({paper_row['year']}), arXiv:{paper_row['key']}, {fig}"
    return f"\"{paper_row['title'] or 'local PDF'}\" (local PDF {paper_row['key']}), {fig}"


def view_figure(ref: str, figure: str) -> tuple[dict, bytes]:
    with lib.connect() as con:
        key = _need_key(con, ref)
        label = normalise_label(figure)
        figs = {f["label"]: f for f in lib.figures_of(con, key)}
        if label not in figs:
            raise LitpickError(f"{key} has no figure '{figure}'. It has: {', '.join(figs) or 'none'}")
        f = figs[label]
        p = lib.get_paper(con, key)
        png = lib.paper_dir(key) / f"fig-{safe_name(label)}.png"
        if not png.is_file():
            png.write_bytes(render(lib.paper_dir(key) / "paper.pdf", f["page"], f["bbox"]))
        info = {"paper": key, "figure": label, "page": f["page"], "caption": f["caption"],
                "region": f["method"], "cite_as": cite_as(p, label), "png": str(png)}
        if f["method"] != "graphics":
            info["note"] = ("region found from the caption position only; it may include text or "
                            "miss part of the figure" if f["method"] == "gap" else
                            "no figure region found; showing the whole page")
        return info, png.read_bytes()


def search_library(query: str, limit: int = 10) -> dict:
    with lib.connect() as con:
        return {"query": query, "results": lib.search(con, query, limit)}


def status() -> dict:
    with lib.connect() as con:
        rows = lib.all_papers(con)
        return {"library": str(library_home()), "parser_version": PARSER_VERSION, "papers": [
            {"paper": r["key"], "title": r["title"], "year": r["year"],
             "figures": con.execute("SELECT COUNT(*) FROM figures WHERE paper_key=?", (r["key"],)).fetchone()[0],
             "parsed_with": r["parser_version"]} for r in rows]}


def forget(ref: str) -> dict:
    with lib.connect() as con:
        key = _need_key(con, ref)
        lib.delete_paper(con, key)
        return {"removed": key}
