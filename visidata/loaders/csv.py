
from visidata import *
import csv

option('csv_dialect', 'excel', 'dialect passed to csv.reader', replay=True)
option('csv_delimiter', ',', 'delimiter passed to csv.reader', replay=True)
option('csv_quotechar', '"', 'quotechar passed to csv.reader', replay=True)
option('csv_skipinitialspace', True, 'skipinitialspace passed to csv.reader', replay=True)
option('csv_escapechar', None, 'escapechar passed to csv.reader', replay=True)
option('safety_first', False, 'sanitize input/output to handle edge cases, with a performance cost', replay=True)

csv.field_size_limit(2**31-1) # Windows has max 32-bit

options_num_first_rows = 10

def wrappedNext(rdr):
    try:
        return next(rdr)
    except csv.Error as e:
        return ['[csv.Error: %s]' % e]

def removeNulls(fp):
    for line in fp:
        yield line.replace('\0', '')


class CsvSheet(SequenceSheet):
    _rowtype = list  # rowdef: list of values

    def newRow(self):
        return [None]*len(self.columns)

    def iterload(self):
        'Convert from CSV, first handling header row specially.'
        with self.source.open_text() as fp:
            if options.safety_first:
                rdr = csv.reader(removeNulls(fp), **options('csv_'))
            else:
                rdr = csv.reader(fp, **options('csv_'))

            yield from rdr


@Sheet.api
def save_csv(sheet, p):
    'Save as single CSV file, handling column names as first line.'
    with p.open_text(mode='w') as fp:
        cw = csv.writer(fp, **options('csv_'))
        colnames = [col.name for col in sheet.visibleCols]
        if ''.join(colnames):
            cw.writerow(colnames)
        for r in Progress(sheet.rows, 'saving'):
            cw.writerow([col.getDisplayValue(r) for col in sheet.visibleCols])

vd.filetype('csv', CsvSheet)
