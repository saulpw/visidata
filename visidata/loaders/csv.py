
from visidata import *
import csv

option('csv_dialect', 'excel', 'dialect passed to csv.reader')
option('csv_delimiter', ',', 'delimiter passed to csv.reader')
option('csv_quotechar', '"', 'quotechar passed to csv.reader')
option('csv_skipinitialspace', True, 'skipinitialspace passed to csv.reader')

csv.field_size_limit(sys.maxsize)

def open_csv(p):
    return CsvSheet(p.name, source=p)

def wrappedNext(rdr):
    try:
        return next(rdr)
    except csv.Error as e:
        return ['[csv.Error: %s]' % e]

class CsvSheet(Sheet):
    @async
    def reload(self):
        load_csv(self)

def load_csv(vs):
    'Convert from CSV, first handling header row specially.'
    with vs.source.open_text() as fp:
        samplelen = min(len(wrappedNext(fp)) for i in range(10))  # for progress only
        fp.seek(0)

        for i in range(options.skip):
            wrappedNext(fp)  # discard initial lines

        rdr = csv.reader(fp,
                         dialect=options.csv_dialect,
                         quotechar=options.csv_quotechar,
                         delimiter=options.csv_delimiter,
                         skipinitialspace=options.csv_skipinitialspace)

        vs.rows = []

        # headers first, to setup columns before adding rows
        headers = [wrappedNext(rdr) for i in range(int(options.header))]

        if headers:
            # columns ideally reflect the max number of fields over all rows
            vs.columns = ArrayNamedColumns('\\n'.join(x) for x in zip(*headers))
        else:
            r = wrappedNext(rdr)
            vs.addRow(wrappedNext(rdr))
            vs.columns = ArrayColumns(len(vs.rows[0]))

        vs.recalc()  # make columns usable
        with Progress(total=vs.source.filesize) as prog:
            try:
                while True:
                    vs.addRow(wrappedNext(rdr))
                    prog.addProgress(samplelen)
            except StopIteration:
                pass

    vs.recalc()
    return vs

@async
def save_csv(sheet, fn):
    'Save as single CSV file, handling column names as first line.'
    with Path(fn).open_text(mode='w') as fp:
        cw = csv.writer(fp, dialect=options.csv_dialect, delimiter=options.csv_delimiter, quotechar=options.csv_quotechar)
        colnames = [col.name for col in sheet.visibleCols]
        if ''.join(colnames):
            cw.writerow(colnames)
        for r in sheet.rows:
            cw.writerow([col.getDisplayValue(r) for col in sheet.visibleCols])
