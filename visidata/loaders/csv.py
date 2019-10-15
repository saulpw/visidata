
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

class CsvSheet(Sheet):
    _rowtype = list  # rowdef: list of values

    def newRow(self):
        return [None]*len(self.columns)

@CsvSheet.api
def iterload(vs):
    'Convert from CSV, first handling header row specially.'
    with vs.source.open_text() as fp:
        for i in range(options.skip):
            wrappedNext(fp)  # discard initial lines

        if options.safety_first:
            rdr = csv.reader(removeNulls(fp), **options('csv_'))
        else:
            rdr = csv.reader(fp, **options('csv_'))

        vs.rows = []

        # headers first, to setup columns before adding rows
        headers = [wrappedNext(rdr) for i in range(int(options.header))]

        vs.columns = []
        if headers:
            # columns ideally reflect the max number of fields over all rows
            for i, colname in enumerate('\\n'.join(x) for x in zip(*headers)):
                vs.addColumn(ColumnItem(colname, i))
        else:
            row = wrappedNext(rdr)
            ncols = len(row)
            for i in range(ncols):
                vs.addColumn(ColumnItem('', i, width=8))
            yield row

        if not vs.columns:
            vs.addColumn(ColumnItem(0))

        with Progress(total=filesize(vs.source)) as prog:
            try:
                samplelen = 0
                for i in range(options_num_first_rows):  # for progress below
                    row = wrappedNext(rdr)
                    yield row
                    samplelen += sum(len(x) for x in row)

                samplelen //= options_num_first_rows  # avg len of first n rows

                while True:
                    yield wrappedNext(rdr)
                    prog.addProgress(samplelen)
            except StopIteration:
                pass  # as expected


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
