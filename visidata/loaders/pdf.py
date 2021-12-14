import io

from visidata import VisiData, vd, options, TableSheet, ColumnItem, IndexSheet
from visidata.loaders._pandas import PandasSheet

vd.option('pdf_tables', False, 'parse PDF for tables instead of pages of text', replay=True)

@VisiData.api
def open_pdf(vd, p):
    if vd.options.pdf_tables:
        return TabulaSheet(p.name, source=p)
    return PdfMinerSheet(p.name, source=p)


class PdfMinerSheet(TableSheet):
    rowtype='pages' # rowdef: [pdfminer.LTPage, pageid, text]
    columns=[
        ColumnItem('pdfpage', 0, width=0),
        ColumnItem('pagenum', 1, type=int),
        ColumnItem('contents', 2),
    ]
    def iterload(self):
        import pdfminer.high_level
        from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
        from pdfminer.converter import TextConverter, PDFPageAggregator
        from pdfminer.layout import LAParams
        from pdfminer.pdfpage import PDFPage

        with self.source.open_bytes() as fp:
            for page in PDFPage.get_pages(fp):
                with io.StringIO() as output_string:
                    newrsrcmgr = PDFResourceManager()
                    txtconv = TextConverter(newrsrcmgr, output_string, codec=options.encoding, laparams=LAParams())
                    interpreter = PDFPageInterpreter(newrsrcmgr, txtconv)
                    interpreter.process_page(page)
                    yield [page, page.pageid, output_string.getvalue()]


class TabulaSheet(IndexSheet):
    def iterload(self):
        import tabula
        for i, t in enumerate(tabula.read_pdf(self.source, pages='all', multiple_tables=True)):
            yield PandasSheet(self.source.name, i, source=t)
