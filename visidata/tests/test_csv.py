import visidata
from visidata.loaders.csv import CsvSheet
from visidata.loaders.tsv import TsvSheet


def _load(tmp_path, name, text, cls):
    p = tmp_path / name
    p.write_text(text)
    vs = cls(name, source=visidata.Path(str(p)))
    vs.reload.__wrapped__(vs)
    return vs


def test_csv_skips_blank_lines(tmp_path):
    # #3085: the csv loader must drop blank lines like the tsv loader,
    # rather than keeping a phantom empty row.
    data = 'col\n1\n\n3\n'
    csvs = _load(tmp_path, 'blank.csv', data, CsvSheet)
    tsvs = _load(tmp_path, 'blank.tsv', data, TsvSheet)
    assert len(csvs.rows) == len(tsvs.rows) == 2  # '1' and '3'; blank line gone


def test_csv_keeps_row_of_empty_values(tmp_path):
    # a ',,' line is a real row whose values happen to be empty (not a blank
    # line), so it must be preserved.
    vs = _load(tmp_path, 'empties.csv', 'col,a,b\n1,2,3\n,,\n7,8,9\n', CsvSheet)
    assert len(vs.rows) == 3
