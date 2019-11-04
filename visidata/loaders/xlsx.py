from visidata import *


class XlsxIndexSheet(IndexSheet):
    'Load XLSX file (in Excel Open XML format).'
    rowtype = 'sheets'  # rowdef: xlsxSheet
    columns = [
        Column('sheet', getter=lambda col,row: row.source.title),  # xlsx sheet title
        ColumnAttr('name', width=0),  # visidata Sheet name
        ColumnAttr('nRows', type=int),
        ColumnAttr('nCols', type=int),
    ]
    nKeys = 1

    def iterload(self):
        import openpyxl
        self.workbook = openpyxl.load_workbook(str(self.source), data_only=True, read_only=True)
        for sheetname in self.workbook.sheetnames:
            vs = XlsxSheet(joinSheetnames(self.name, sheetname), source=self.workbook[sheetname])
            vs.reload()
            yield vs


class XlsxSheet(SequenceSheet):
    def iterload(self):
        worksheet = self.source
        rows = worksheet.iter_rows()
        for r in Progress(rows, total=worksheet.max_row or 0):
            yield list(wrapply(getattr, cell, 'value') for cell in r)

class XlsIndexSheet(IndexSheet):
    'Load XLS file (in Excel format).'
    rowtype = 'sheets'  # rowdef: xlsSheet
    columns = [
        Column('sheet', getter=lambda col,row: row.source.name),  # xls sheet name
        ColumnAttr('name', width=0),  # visidata sheet name
        ColumnAttr('nRows', type=int),
        ColumnAttr('nCols', type=int),
    ]
    nKeys = 1
    def iterload(self):
        import xlrd
        self.workbook = xlrd.open_workbook(str(self.source))
        for sheetname in self.workbook.sheet_names():
            vs = XlsSheet(joinSheetnames(self.name, sheetname), source=self.workbook.sheet_by_name(sheetname))
            vs.reload()
            yield vs


class XlsSheet(Sheet):
    def iterload(self):
        worksheet = self.source
        self.columns = []
        if options.header:
            hdrs = [list(worksheet.cell(rownum, colnum).value for colnum in range(worksheet.ncols))
                        for rownum in range(options.header)]
            colnames = ['\\n'.join(str(hdr[i]) for i in range(len(hdr))) for hdr in zip(*hdrs)]
        else:
            colnames = ['']*worksheet.ncols

        for i, colname in enumerate(colnames):
            self.addColumn(ColumnItem(colname, i))

        for rownum in Progress(range(options.header, worksheet.nrows)):
            yield list(worksheet.cell(rownum, colnum).value for colnum in range(worksheet.ncols))


vd.filetype('xlsx', XlsxIndexSheet)
vd.filetype('xls', XlsIndexSheet)
