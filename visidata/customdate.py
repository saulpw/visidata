import time
from visidata import vd, date, Sheet, ColumnsSheet


@Sheet.api
def customdate(sheet, fmtstr):
    'Return date class with strptime parse format fixed to *fmtstr*.'
    class _customdate(date):
        def __new__(cls, *args, **kwargs):
            if len(args) == 1 and isinstance(args[0], str):
                return super().__new__(cls, *time.strptime(args[0], fmtstr)[:6])
            return super().__new__(cls, *args, **kwargs)

    vd.addType(_customdate, '@', '', formatter=lambda fmt,val: val.strftime(fmt or sheet.options.disp_date_fmt))
    _customdate.__name__ = 'customdate(%s)' % fmtstr
    return _customdate


Sheet.addCommand('z@', 'type-customdate', 'cursorCol.type=cursorCol.type=customdate(input("date format: ", type="fmtstr"))', 'set type of current column to custom date format')
ColumnsSheet.addCommand('gz@', 'type-customdate-selected', 'onlySelectedRows.type=customdate(input("date format: ", type="fmtstr"))', 'set type of selected columns to date')
