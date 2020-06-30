from visidata import *


def open_xlsx(p):
    return XlsxIndexSheet(p.name, source=p)

open_xls = open_xlsx

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
        for row in Progress(worksheet.iter_rows(), total=worksheet.max_row or 0):
            yield list(wrapply(getattr, cell, 'value') for cell in row)


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


class XlsSheet(SequenceSheet):
    def iterload(self):
        worksheet = self.source
        for rownum in Progress(range(worksheet.nrows)):
            yield list(worksheet.cell(rownum, colnum).value for colnum in range(worksheet.ncols))


@VisiData.api
def save_xlsx(vd, p, *sheets):
    import openpyxl

    wb = openpyxl.Workbook()
    wb.remove_sheet(wb['Sheet'])

    for vs in sheets:
        ws = wb.create_sheet(title=vs.name)

        headers = [col.name for col in vs.visibleCols]
        ws.append(headers)

        for dispvals in vs.iterdispvals(format=False):

            row = []
            for col, v in dispvals.items():
                if col.type == date:
                    v = datetime.datetime.fromtimestamp(int(v.timestamp()))
                elif not isNumeric(col):
                    v = str(v)
                row.append(v)

            ws.append(row)

    wb.active = ws

    wb.save(filename=p)
    status(f'{p} save finished')


@VisiData.api
def save_xls(vd, p, *sheets):
    import xlwt

    wb = xlwt.Workbook()

    for vs in sheets:

        ws1 = wb.add_sheet(vs.name[:32]) # sheet name can not be longer than 32 characters

        for col_i, col in enumerate(vs.visibleCols):
            ws1.write(0, col_i, col.name)

        for r_i, dispvals in enumerate(vs.iterdispvals(format=True)):
            r_i += 1
            for c_i, v in enumerate(dispvals.values()):
                ws1.write(r_i, c_i, v)

    wb.save(p)
    status(f'{p} save finished')
