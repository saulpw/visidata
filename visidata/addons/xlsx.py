
from visidata import *

class open_xlsx(Sheet):
    def __init__(self, path):
        super().__init__(path.name, path)
        import openpyxl
        self.workbook = openpyxl.load_workbook(str(path), data_only=True, read_only=True)

    def reload(self):
        self.rows = list(self.workbook.sheetnames)
        self.columns = [Column('name')]
        self.command('^J', 'vd.push(sheet.getSheet(cursorRow))', 'push this sheet')

    def getSheet(self, sheetname):
        worksheet = self.workbook.get_sheet_by_name(sheetname)
        return xlsxSheet(join_sheetnames(self.source, sheetname), worksheet)

class xlsxSheet(Sheet):
    def reload(self):
        worksheet = self.source
        self.columns = ArrayColumns(worksheet.max_column)
        self.rows = [[cell.value for cell in row] for row in worksheet.iter_rows()]
