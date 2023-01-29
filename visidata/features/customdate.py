import time
from visidata import vd, Sheet, ColumnsSheet
from visidata.type_date import date


@Sheet.api
def customdate(sheet, fmtstr):
    'Return date class with strptime parse format fixed to *fmtstr*.'
    class _customdate(date):
        def __new__(cls, *args, **kwargs):
            if len(args) == 1 and isinstance(args[0], str):
                return super().__new__(cls, *time.strptime(args[0], fmtstr)[:6])
            return super().__new__(cls, *args, **kwargs)

    _customdate.__name__ = 'customdate(%s)' % fmtstr

    vd.addType(_customdate, '@', '', formatter=lambda fmt,val: val.strftime(fmt or sheet.options.disp_date_fmt))
    vd.numericTypes.append(_customdate)
    return _customdate


Sheet.addCommand('z@', 'type-customdate', 'fmt=input("date format: ", type="fmtstr"); cursorCol.type=customdate(fmt); cursorCol.fmtstr=fmt', 'set type of current column to custom date format')
ColumnsSheet.addCommand('gz@', 'type-customdate-selected', 'fmt=input("date format: ", type="fmtstr"); onlySelectedRows.type=customdate(fmt); onlySelectedRows.fmtstr=fmt', 'set type of selected columns to date')

vd.addMenuItems('Column > Type as > custom date format > type-customdate')
