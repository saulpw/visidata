from visidata import vd, VisiData, SequenceSheet, options, stacktrace
from visidata import TypedExceptionWrapper, Progress

vd.option('csv_dialect', 'excel', 'dialect passed to csv.reader', replay=True)
vd.option('csv_delimiter', ',', 'delimiter passed to csv.reader', replay=True)
vd.option('csv_doublequote', True, 'quote-doubling setting passed to csv.reader', replay=True)
vd.option('csv_quotechar', '"', 'quotechar passed to csv.reader', replay=True)
vd.option('csv_quoting', 0, 'quoting style passed to csv.reader and csv.writer', replay=True)
vd.option('csv_skipinitialspace', True, 'skipinitialspace passed to csv.reader', replay=True)
vd.option('csv_escapechar', None, 'escapechar passed to csv.reader', replay=True)
vd.option('csv_lineterminator', '\r\n', 'lineterminator passed to csv.writer', replay=True)
vd.option('safety_first', False, 'sanitize input/output to handle edge cases, with a performance cost', replay=True)


@VisiData.api
def guess_csv(vd, p):
    import csv
    csv.field_size_limit(2**31-1)  #288 Windows has max 32-bit
    try:
        line = next(p.open())
    except StopIteration:
        return
    if ',' in line:
        dialect = csv.Sniffer().sniff(line)
        r = dict(filetype='csv', _likelihood=0)

        for csvopt in dir(dialect):
            if not csvopt.startswith('_'):
                r['csv_'+csvopt] = getattr(dialect, csvopt)

        return r

@VisiData.api
def open_csv(vd, p):
    return CsvSheet(p.base_stem, source=p)

def removeNulls(fp):
    for line in fp:
        yield line.replace('\0', '')

class CsvSheet(SequenceSheet):
    _rowtype = list  # rowdef: list of values

    def iterload(self):
        'Convert from CSV, first handling header row specially.'
        import csv
        csv.field_size_limit(2**31-1)  #288 Windows has max 32-bit

        with self.open_text_source(newline='') as fp:
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
    import csv
    csv.field_size_limit(2**31-1)  #288 Windows has max 32-bit

    with p.open(mode='w', encoding=sheet.options.save_encoding, newline='') as fp:
        cw = csv.writer(fp, **options.getall('csv_'))
        colnames = [col.name for col in sheet.visibleCols]
        if ''.join(colnames):
            cw.writerow(colnames)

        with Progress(gerund='saving', total=sheet.nRows) as prog:
            for dispvals in sheet.iterdispvals(format=True):
                cw.writerow(dispvals.values())
                prog.addProgress(1)

vd.addGlobals({
    'CsvSheet': CsvSheet
})
