
from visidata import *

class open_xlsx(Sheet):
    def __init__(self, path):
        super().__init__(path.name, path)
        self.workbook = None
        self.command('^J', 'vd.push(sheet.getSheet(cursorRow))', 'push this sheet')

    @async
    def reload(self):
        import openpyxl
        self.columns = [Column('name')]
        self.workbook = openpyxl.load_workbook(str(self.source), data_only=True, read_only=True)
        self.rows = list(self.workbook.sheetnames)

    def getSheet(self, sheetname):
        worksheet = self.workbook.get_sheet_by_name(sheetname)
        return xlsxSheet(join_sheetnames(self.source, sheetname), worksheet)

class xlsxSheet(Sheet):
    @async
    def reload(self):
        worksheet = self.source
        self.columns = ArrayColumns(worksheet.max_column)
        self.progressTotal = worksheet.max_row
        for row in worksheet.iter_rows():
            self.progressMade += 1
            self.rows.append([cell.value for cell in row])
