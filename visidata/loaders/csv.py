
from visidata import *
import csv

option('csv_dialect', 'excel', 'dialect passed to csv.reader', replay=True)
option('csv_delimiter', ',', 'delimiter passed to csv.reader', replay=True)
option('csv_quotechar', '"', 'quotechar passed to csv.reader', replay=True)
option('csv_skipinitialspace', True, 'skipinitialspace passed to csv.reader', replay=True)
option('csv_escapechar', None, 'escapechar passed to csv.reader', replay=True)
option('safety_first', False, 'sanitize input/output to handle edge cases, with a performance cost', replay=True)

# On Windows, a C-long is always 32-bit. We need this check to avoid OverflowError on 64-bit Windows.
csv.field_size_limit(2**31-1 if sys.platform == 'win32' else sys.maxsize)

options_num_first_rows = 10

def open_csv(p):
    return CsvSheet(p.name, source=p)

def wrappedNext(rdr):
    try:
        return next(rdr)
    except csv.Error as e:
        return ['[csv.Error: %s]' % e]

def removeNulls(fp):
    for line in fp:
        yield line.replace('\0', '')

class CsvSheet(Sheet):
    _rowtype = list
#    _coltype = ColumnItem
    @asyncthread
    def reload(self):
        load_csv(self)

    def newRow(self):
        return [None]*len(self.columns)

def csvoptions():
    return options('csv_')

def load_csv(vs):
    'Convert from CSV, first handling header row specially.'
    with vs.source.open_text() as fp:
        for i in range(options.skip):
            wrappedNext(fp)  # discard initial lines

        if options.safety_first:
            rdr = csv.reader(removeNulls(fp), **csvoptions())
        else:
            rdr = csv.reader(fp, **csvoptions())

        vs.rows = []

        # headers first, to setup columns before adding rows
        headers = [wrappedNext(rdr) for i in range(int(options.header))]

        if headers:
            # columns ideally reflect the max number of fields over all rows
            vs.columns = [ColumnItem(colname, i)
                    for i, colname in enumerate('\\n'.join(x) for x in zip(*headers))]
        else:
            r = wrappedNext(rdr)
            vs.addRow(r)
            ncols = len(vs.rows[0])
            vs.columns = [ColumnItem('', i, width=8) for i in range(ncols)]

        if not vs.columns:
            vs.columns = [ColumnItem(0)]

        vs.recalc()  # make columns usable
        with Progress(total=vs.source.filesize) as prog:
            try:
                samplelen = 0
                for i in range(options_num_first_rows):  # for progress below
                    row = wrappedNext(rdr)
                    vs.addRow(row)
                    samplelen += sum(len(x) for x in row)

                samplelen //= options_num_first_rows  # avg len of first n rows

                while True:
                    vs.addRow(wrappedNext(rdr))
                    prog.addProgress(samplelen)
            except StopIteration:
                pass  # as expected

    vs.recalc()
    return vs


@asyncthread
def save_csv(p, sheet):
    'Save as single CSV file, handling column names as first line.'
    with p.open_text(mode='w') as fp:
        cw = csv.writer(fp, **csvoptions())
        colnames = [col.name for col in sheet.visibleCols]
        if ''.join(colnames):
            cw.writerow(colnames)
        for r in Progress(sheet.rows, 'saving'):
            cw.writerow([col.getDisplayValue(r) for col in sheet.visibleCols])
