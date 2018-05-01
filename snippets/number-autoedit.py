for i in range(0, 10):
    globalCommand(str(i), 'cursorCol.setValues([cursorRow], editCell(cursorVisibleColIndex, value="%s", i=1))' % i, 'replace cell value with input starting with %s' % i)
