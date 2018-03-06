
from visidata import *

def open_xlsx(p):
    vs = xlsxContents(p)
    return vs


class xlsxContents(Sheet):
    'Load XLSX file (in Excel Open XML format).'
    columns = [
        Column('sheet', getter=lambda col,row: row.source.title),  # xlsx sheet title
        ColumnAttr('name', width=0),  # visidata Sheet name
        ColumnAttr('nRows', type=int),
        ColumnAttr('nCols', type=int),
    ]
    nKeys = 1
    commands = [
        Command(ENTER, 'vd.push(cursorRow)', 'load the entire table into memory')
    ]
    def __init__(self, path):
        super().__init__(path.name, source=path)
        self.workbook = None

    @async
    def reload(self):
        import openpyxl
        self.workbook = openpyxl.load_workbook(self.source.resolve(), data_only=True, read_only=True)
        self.rows = []
        for sheetname in self.workbook.sheetnames:
            vs = xlsxSheet(joinSheetnames(self.name, sheetname), source=self.workbook[sheetname])
            vs.reload()
            self.rows.append(vs)


class xlsxSheet(Sheet):
    @async
    def reload(self):
        worksheet = self.source

        self.columns = []
        self.rows = []
        for row in Progress(worksheet.iter_rows(), worksheet.max_row or 0):
            L = list(cell.value for cell in row)
            for i in range(len(self.columns), len(L)):  # no-op if already done
                self.addColumn(ColumnItem(None, i, width=8))
            self.addRow(L)


class open_xls(Sheet):
    'Load XLS file (in Excel format).'
    commands = [
        Command(ENTER, 'vd.push(cursorRow)', 'load the entire table into memory')
    ]
    columns = [
        Column('sheet', getter=lambda col,row: row.source.name),  # xls sheet name
        ColumnAttr('name', width=0),  # visidata sheet name
        ColumnAttr('nRows', type=int),
        ColumnAttr('nCols', type=int),
    ]
    nKeys = 1
    def __init__(self, path):
        super().__init__(path.name, source=path)
        self.workbook = None

    @async
    def reload(self):
        import xlrd
        self.workbook = xlrd.open_workbook(self.source.resolve())
        self.rows = []
        for sheetname in self.workbook.sheet_names():
            vs = xlsSheet(joinSheetnames(self.name, sheetname), source=self.workbook.sheet_by_name(sheetname))
            vs.reload()
            self.rows.append(vs)


class xlsSheet(Sheet):
    @async
    def reload(self):
        worksheet = self.source
        self.columns = []
        for i in range(worksheet.ncols):
            self.addColumn(ColumnItem(None, i, width=8))

        self.rows = []
        for rownum in Progress(range(worksheet.nrows)):
            self.addRow(list(worksheet.cell(rownum, colnum).value for colnum in range(worksheet.ncols)))
