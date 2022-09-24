import csv

from visidata import vd, VisiData, SequenceSheet, options, stacktrace
from visidata import TypedExceptionWrapper, Progress

vd.option('csv_dialect', 'excel', 'dialect passed to csv.reader', replay=True)
vd.option('csv_delimiter', ',', 'delimiter passed to csv.reader', replay=True)
vd.option('csv_quotechar', '"', 'quotechar passed to csv.reader', replay=True)
vd.option('csv_skipinitialspace', True, 'skipinitialspace passed to csv.reader', replay=True)
vd.option('csv_escapechar', None, 'escapechar passed to csv.reader', replay=True)
vd.option('csv_lineterminator', '\r\n', 'lineterminator passed to csv.writer', replay=True)
vd.option('safety_first', False, 'sanitize input/output to handle edge cases, with a performance cost', replay=True)

csv.field_size_limit(2**31-1) # Windows has max 32-bit

options_num_first_rows = 10

@VisiData.api
def open_csv(vd, p):
    return CsvSheet(p.name, source=p)

def remove_nulls(fp):
    for line in fp:
        yield line.replace('\0', '')

class CsvSheet(SequenceSheet):
    _rowtype = list  # rowdef: list of values
    _proposed_delimiter = None
    _delimiter = None

    def iterload(self):
        'Convert from CSV, first handling header row specially.'
        reader_options = options.getall('csv_')
        if self._delimiter is not None:
            reader_options["delimiter"] = self._delimiter

        with self.source.open_text(encoding=self.options.encoding) as fp:
            if options.safety_first:
                rdr = csv.reader(self._suggest_dialect(remove_nulls(fp)), **reader_options)
            else:
                rdr = csv.reader(self._suggest_dialect(fp), **reader_options)

            while True:
                try:
                    yield next(rdr)
                except csv.Error as e:
                    e.stacktrace=stacktrace()
                    yield [TypedExceptionWrapper(None, exception=e)]
                except StopIteration:
                    return

    def reload_with_proper_encoding(self):
        self._delimiter = self._proposed_delimiter
        self.reload()

    def _suggest_dialect(self, lines):
        chunk = ""
        for line in lines:
            if chunk is None:
                yield line
                continue

            chunk += "\n" + line
            if len(chunk) > 1024 * 1024:
                self._suggest_dialect_based_on_chunk(chunk[1:])
                chunk = None

            yield line

        if chunk is not None and len(chunk) > 0:
            self._suggest_dialect_based_on_chunk(chunk[1:])

    def _suggest_dialect_based_on_chunk(self, chunk):
        proposed_dialect = csv.Sniffer().sniff(chunk)
        actual_delimiter = self._delimiter if self._delimiter is not None else options.csv_delimiter

        # EU CSV delimiter is different from US.
        # As quoted from https://en.wikipedia.org/wiki/Comma-separated_values
        # "Semicolons are often used instead of commas in many European locales in order to use the comma as the decimal separator and, possibly, the period as a decimal grouping character."
        if proposed_dialect.delimiter == actual_delimiter:
            return

        self._proposed_delimiter = proposed_dialect.delimiter
        self.addCommand('z^R', 'reload-csv-with-proper-dialect', 'sheet.reload_with_proper_encoding()')
        vd.warning("Probably you CSV file is loaded incorrectly because the delimiter is wrong. Press z CRTL-r to reload with proper delimeter.")

@VisiData.api
def save_csv(vd, p, sheet):
    'Save as single CSV file, handling column names as first line.'
    with p.open_text(mode='w', encoding=sheet.options.encoding, newline='') as fp:
        cw = csv.writer(fp, **options.getall('csv_'))
        colnames = [col.name for col in sheet.visibleCols]
        if ''.join(colnames):
            cw.writerow(colnames)

        with Progress(gerund='saving'):
            for dispvals in sheet.iterdispvals(format=True):
                cw.writerow(dispvals.values())

vd.addGlobals({
    'CsvSheet': CsvSheet
})
