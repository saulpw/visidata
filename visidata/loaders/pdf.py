import io

from visidata import *

def open_pdf(p):
    return PdfSheet(p.name, source=p)

class PdfSheet(TableSheet):
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
