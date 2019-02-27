for i in range(0, 10):
    globalCommand(str(i), 'cursorCol.setValues([cursorRow], edit(cursorCol, cursorRow, value="%s", i=1))' % i, 'replace cell value with input starting with %s' % i)
