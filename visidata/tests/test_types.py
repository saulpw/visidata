import pytest

from visidata import vd, Column, Sheet


class TestColumnTypeCoercion:
    """Test that Column.getTypedValue handles string-to-numeric edge cases."""

    def _make_col(self, coltype, values):
        "Helper: create a sheet with one column of given type and return (col, rows)."
        sheet = Sheet("test", columns=[Column("testcol", type=coltype)])
        rows = []
        for v in values:
            row = {0: v}
            rows.append(row)
        sheet.rows = rows
        # Use simple dict-based getter
        sheet.columns[0].getter = lambda col, row: row[0]
        return sheet.columns[0], rows

    def test_int_from_int(self):
        col, rows = self._make_col(int, [42])
        assert col.getTypedValue(rows[0]) == 42

    def test_int_from_float(self):
        col, rows = self._make_col(int, [42.7])
        assert col.getTypedValue(rows[0]) == 42

    def test_int_from_clean_string(self):
        col, rows = self._make_col(int, ["42"])
        assert col.getTypedValue(rows[0]) == 42

    def test_int_from_float_string(self):
        # Core bug: int("42.5") raises ValueError in Python
        # Should coerce via float: int(float("42.5")) == 42
        col, rows = self._make_col(int, ["42.5"])
        result = col.getTypedValue(rows[0])
        assert result == 42

    def test_int_from_negative_float_string(self):
        col, rows = self._make_col(int, ["-3.14"])
        result = col.getTypedValue(rows[0])
        assert result == -3

    def test_int_from_string_with_whitespace(self):
        col, rows = self._make_col(int, ["  42  "])
        assert col.getTypedValue(rows[0]) == 42

    def test_float_from_string(self):
        col, rows = self._make_col(float, ["3.14"])
        assert col.getTypedValue(rows[0]) == 3.14

    def test_float_from_int(self):
        col, rows = self._make_col(float, [42])
        assert col.getTypedValue(rows[0]) == 42.0

    def test_float_preserves_behavior(self):
        # float conversion from string should still work as before
        col, rows = self._make_col(float, ["-1.5"])
        assert col.getTypedValue(rows[0]) == -1.5

    def test_str_type_unaffected(self):
        # str columns should not be coerced
        col, rows = self._make_col(str, [42])
        assert col.getTypedValue(rows[0]) == "42"

    def test_coerceVal_int_float_string(self):
        col, _ = self._make_col(int, [])
        assert col._coerceVal("42.5") == 42.5  # returns float for int() to truncate
        assert col._coerceVal("42") == 42.0

    def test_coerceVal_noop_for_float_type(self):
        col, _ = self._make_col(float, [])
        # float type doesn't need coercion, passthrough
        assert col._coerceVal("3.14") == "3.14"

    def test_coerceVal_noop_for_native_int(self):
        col, _ = self._make_col(int, [])
        # Native int doesn't need coercion
        assert col._coerceVal(42) == 42
