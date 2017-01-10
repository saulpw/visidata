## csv/tsv

from visidata import *
import csv
import io

option('csv_dialect', 'excel', 'dialect passed to csv.reader')
option('csv_delimiter', ',', 'delimiter passed to csv.reader')
option('csv_quotechar', '"', 'quotechar passed to csv.reader')

def open_csv(p):
    vs = Sheet(p.name, p)
    vs.contents = getTextContents(p)
    vs.loader = lambda vs=vs: load_csv(vs)
    return vs

def load_csv(vs):
    header_lines = int(options.headerlines)
    if options.csv_dialect == 'sniff':
        headers = self.contents[:1024]
        dialect = csv.Sniffer().sniff(headers)
        status('sniffed csv_dialect as %s' % dialect)
    else:
        dialect = options.csv_dialect

    rdr = csv.reader(io.StringIO(vs.contents, newline=''),
                        dialect=dialect,
                        quotechar=options.csv_quotechar,
                        delimiter=options.csv_delimiter)
    rows = [r for r in rdr]
    if header_lines:
        # columns ideally reflect the max number of fields over all rows
        vs.columns = ArrayNamedColumns('\\n'.join(x) for x in zip(*rows[:header_lines]))
    else:
        vs.columns = ArrayColumns(len(rows[0]))
    vs.rows = rows[header_lines:]
    return vs


def save_csv(sheet, fn):
    with open(fn, 'w', newline='', encoding=options.encoding, encoding_errors=options.encoding_errors) as fp:
        cw = csv.writer(fp, dialect=options.csv_dialect, delimiter=options.csv_delimiter, quotechar=options.csv_quotechar)
        colnames = [col.name for col in sheet.visibleCols]
        if ''.join(colnames):
            cw.writerow(colnames)
        for r in sheet.rows:
            cw.writerow([col.getDisplayValue(r) for col in sheet.visibleCols])
