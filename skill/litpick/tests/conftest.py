"""Test papers built on the fly with PyMuPDF and matplotlib, so the tests need no network and no
LaTeX and run the same on macOS, Windows and Linux."""
from __future__ import annotations

import io

import matplotlib
import numpy as np
import pymupdf
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

LOREM = ("The tunnel barrier is a few layers thick and the current flows across it. "
         "We measure the resistance while sweeping the magnetic field at low temperature. ") * 4


def _plot(vector: bool, panels: int = 1) -> bytes:
    B = np.linspace(-2, 2, 300)
    fig, axs = plt.subplots(1, panels, figsize=(3.2 * panels, 2.3))
    for i, ax in enumerate(np.atleast_1d(axs)):
        ax.plot(B, 100 * np.clip(1 - (np.abs(B) / (0.8 + 0.3 * i)) ** 2, 0, 1))
        ax.set_xlabel("field (T)")
        ax.set_ylabel("TMR (%)")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf" if vector else "png", dpi=150)
    plt.close(fig)
    return buf.getvalue()


def _place_vector(page: pymupdf.Page, rect: pymupdf.Rect, pdf_bytes: bytes) -> None:
    src = pymupdf.open("pdf", pdf_bytes)
    page.show_pdf_page(rect, src, 0)
    src.close()


@pytest.fixture(autouse=True)
def isolated_library(tmp_path, monkeypatch):
    monkeypatch.setenv("LITPICK_HOME", str(tmp_path / "lib"))
    yield tmp_path / "lib"


@pytest.fixture
def aps_pdf(tmp_path):
    """Two columns, 'FIG. 1.' captions under the figures, a full-width figure, a bitmap figure,
    and a body paragraph that STARTS with 'Fig. 2 shows' (must not count as a caption)."""
    doc = pymupdf.open()
    W, H, m, gap = 612, 792, 54, 18
    col = (W - 2 * m - gap) / 2
    left = pymupdf.Rect(m, m, m + col, H - m)
    right = pymupdf.Rect(m + col + gap, m, W - m, H - m)

    p = doc.new_page(width=W, height=H)
    p.insert_textbox(pymupdf.Rect(left.x0, left.y0, left.x1, 300), LOREM + "As shown in Fig. 1(a), the "
                     "resistance drops at the spin-flip field.", fontsize=9)
    _place_vector(p, pymupdf.Rect(left.x0, 310, left.x1, 470), _plot(True))
    p.insert_textbox(pymupdf.Rect(left.x0, 478, left.x1, 520), "FIG. 1. Tunneling magnetoresistance "
                     "versus field at 2 K.", fontsize=8)
    p.insert_textbox(pymupdf.Rect(left.x0, 530, left.x1, H - m), LOREM, fontsize=9)
    p.insert_textbox(pymupdf.Rect(right.x0, right.y0, right.x1, H - m),
                     "Fig. 2 shows the layer dependence. " + LOREM + " Figs. 2 and 3 compare devices.",
                     fontsize=9)

    p = doc.new_page(width=W, height=H)
    _place_vector(p, pymupdf.Rect(m, m, W - m, 260), _plot(True, panels=2))
    p.insert_textbox(pymupdf.Rect(m, 268, W - m, 300), "FIG. 2. Field sweeps for (a) bilayer and (b) "
                     "trilayer barriers.", fontsize=8)
    p.insert_textbox(pymupdf.Rect(left.x0, 320, left.x1, H - m), LOREM * 2, fontsize=9)
    p.insert_image(pymupdf.Rect(right.x0, 320, right.x1, 470), stream=_plot(False))
    p.insert_textbox(pymupdf.Rect(right.x0, 478, right.x1, 520), "FIG. 3. Bitmap figure of a "
                     "temperature series.", fontsize=8)
    p.insert_textbox(pymupdf.Rect(right.x0, 530, right.x1, H - m), LOREM, fontsize=9)

    out = tmp_path / "aps.pdf"
    doc.save(out)
    doc.close()
    return out


@pytest.fixture
def nature_pdf(tmp_path):
    """One column, bold 'Figure 1 |' captions, and a 'Supplementary Figure 1' (label S1)."""
    doc = pymupdf.open()
    W, H, m = 612, 792, 60
    p = doc.new_page(width=W, height=H)
    p.insert_textbox(pymupdf.Rect(m, m, W - m, 200), LOREM + " See Figure 1 for the sweep.", fontsize=10)
    _place_vector(p, pymupdf.Rect(m + 100, 210, W - m - 100, 400), _plot(True))
    p.insert_text((m, 420), "Figure 1 |", fontname="hebo", fontsize=9)
    p.insert_text((m + 48, 420), "Magnetoresistance of the junction.", fontsize=9)
    p = doc.new_page(width=W, height=H)
    _place_vector(p, pymupdf.Rect(m + 100, m, W - m - 100, 250), _plot(True))
    p.insert_text((m, 270), "Supplementary Figure 1:", fontname="hebo", fontsize=9)
    p.insert_text((m + 120, 270), "Raw resistance data.", fontsize=9)
    out = tmp_path / "nature.pdf"
    doc.save(out)
    doc.close()
    return out
