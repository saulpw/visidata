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

def removeNulls(fp):
    for line in fp:
        yield line.replace('\0', '')

class CsvSheet(SequenceSheet):
    _rowtype = list  # rowdef: list of values

    def iterload(self):
        'Convert from CSV, first handling header row specially.'
        with self.source.open_text(encoding=self.options.encoding) as fp:
            if options.safety_first:
                rdr = csv.reader(removeNulls(fp), **options.getall('csv_'))
            else:
                rdr = csv.reader(fp, **options.getall('csv_'))

            while True:
                try:
                    yield next(rdr)
                except csv.Error as e:
                    e.stacktrace=stacktrace()
                    yield [TypedExceptionWrapper(None, exception=e)]
                except StopIteration:
                    return


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
