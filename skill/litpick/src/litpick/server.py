"""The litpick MCP server (stdio). Started by the plugin as `litpick-serve`.

Nothing here may print to stdout: stdout carries the MCP protocol. Logs go to stderr.
Slow work (download, parse, render) runs in a worker thread so the server stays responsive.
"""
from __future__ import annotations

import json
import logging
import sys

import anyio
try:  # MCP Python SDK 2.x renamed FastMCP to MCPServer; the API used here is the same in both
    from mcp.server.mcpserver import Image, MCPServer as _Server
except ImportError:  # SDK 1.x
    from mcp.server.fastmcp import FastMCP as _Server, Image

from . import service

logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format="litpick: %(message)s")

mcp = _Server(
    "litpick",
    instructions=(
        "litpick opens arXiv papers or local PDFs and shows their figures. It does not search for "
        "papers: get an arXiv id from a literature search tool first. Flow: ingest_paper -> "
        "list_figures -> view_figure. search_library searches captions of papers already opened, "
        "offline. Cite a figure with the cite_as string view_figure returns."
    ),
)


def _err(e: Exception) -> str:
    return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
async def ingest_paper(paper: str, force: bool = False) -> str:
    """Open a paper and find its figures. `paper` is an arXiv id ('2407.13230', '2407.13230v2'),
    an arXiv URL, or the full path of a PDF on this computer. Returns at once if already in the
    library ('cached'); a new arXiv paper takes from a few seconds to a minute.
    force=True downloads and parses again."""
    try:
        return json.dumps(await anyio.to_thread.run_sync(service.ingest, paper, force))
    except Exception as e:
        return _err(e)


@mcp.tool()
async def list_figures(paper: str) -> str:
    """Captions of every figure in an opened paper, with the paragraphs that discuss each one.
    Use it to pick the figure that matches what you need before viewing it."""
    try:
        return json.dumps(await anyio.to_thread.run_sync(service.list_figures, paper))
    except Exception as e:
        return _err(e)


@mcp.tool()
async def view_figure(paper: str, figure: str) -> list:
    """The image of one figure, by its printed number: '2', 'Fig. 2', 'S1', 'Extended Data Fig. 3'.
    Returns its caption and a citation string (cite_as) followed by the PNG."""
    try:
        info, png = await anyio.to_thread.run_sync(service.view_figure, paper, figure)
    except Exception as e:
        return [_err(e)]
    return [json.dumps(info), Image(data=png, format="png")]


@mcp.tool()
async def search_library(query: str, limit: int = 10) -> str:
    """Search the captions and discussing paragraphs of papers already in the library (offline)."""
    try:
        return json.dumps(await anyio.to_thread.run_sync(service.search_library, query, limit))
    except Exception as e:
        return _err(e)


@mcp.tool()
async def library_status() -> str:
    """Where the library is and which papers it holds."""
    try:
        return json.dumps(await anyio.to_thread.run_sync(service.status))
    except Exception as e:
        return _err(e)


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
