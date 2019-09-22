'Enter edit mode automatically when typing numeric digits.'

from visidata import Sheet

for i in range(0, 10):
    Sheet.addCommand(str(i), 'autoedit-%s' % i, 'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex, value="%s", i=1))' % i, 'replace cell value with input starting with %s' % i)
