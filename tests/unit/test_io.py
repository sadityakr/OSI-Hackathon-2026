"""Unit tests for ramanlens.perception.io: header handling, delimiters, axis order, series alignment."""

import numpy as np
import pytest

from ramanlens.perception.io import read_series, read_spectrum


def test_headerless_tab_file_descending_axis(tmp_path):
    p = tmp_path / "s.txt"
    p.write_text("# instrument comment\n300\t5\n200\t3\n100\t1\n")
    s = read_spectrum(p)
    assert np.array_equal(s.x, [100, 200, 300]) and np.array_equal(s.y, [1, 3, 5])
    assert s.meta["header"] is None


def test_header_and_extra_columns_and_duplicates(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("shift;intensity;extra\n100;1;9\n100;3;9\n200;4;9\nEND\n")
    s = read_spectrum(p)
    assert np.array_equal(s.x, [100, 200]) and np.array_equal(s.y, [2, 4])
    assert s.meta["header"] == ["shift", "intensity", "extra"]


def test_read_spectrum_rejects_empty(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("a,b\n")
    with pytest.raises(ValueError):
        read_spectrum(p)


def test_series_interpolates_mismatched_axes(tmp_path):
    p = tmp_path / "ser.csv"
    lines = ["shift_cm1,intensity,angle_deg,config"]
    for cfg, ang, xs in [("parallel", 0, [100, 110, 120, 130]), ("Crossed", 0, [105, 115, 125, 135])]:
        lines += [f"{x},{x},{ang},{cfg}" for x in xs]
    p.write_text("\n".join(lines))
    ser = read_series(p)
    assert set(ser.spectra) == {("parallel", 0.0), ("crossed", 0.0)}
    assert ser.meta["interpolated"] and ser.x[0] >= 105 and ser.x[-1] <= 130
    assert np.allclose(ser.spectra[("crossed", 0.0)], ser.x)
