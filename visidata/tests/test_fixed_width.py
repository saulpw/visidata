from visidata.loaders.fixed_width import columnize


class TestColumnize:
    def test_basic(self):
        rows = ['name age city', 'Alice 30  NYC ']
        cols = list(columnize(rows))
        assert len(cols) == 3

    def test_data_with_internal_spaces(self):  #2265
        'data values with spaces should not create extra columns'
        rows = [
            'colours shades               counts',
            'red     light                3     ',
            'green   very very very light 5     ',
            'blue    dark                 8     ',
        ]
        cols = list(columnize(rows))
        assert len(cols) == 3, f'Expected 3, got {len(cols)}: {cols}'

        # verify last row extracts correctly
        vals = [rows[2][i:j].strip() if j else rows[2][i:].strip() for i, j in cols]
        assert vals == ['green', 'very very very light', '5']

    def test_empty(self):
        assert list(columnize([])) == []

    def test_single_column(self):
        rows = ['name', 'Alice']
        cols = list(columnize(rows))
        assert len(cols) == 1
        assert cols[0] == (0, 5)
