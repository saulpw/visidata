#### Google Sheets; requires credentials to be setup already

import functools

@functools.lru_cache()
def google_sheets():
    """Log in to Google Sheets and retrieve spreadsheets object.

    Fail on missing or invalid login credentials.
    """
    import httplib2
    import os

    from apiclient import discovery
    from oauth2client.file import Storage

    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    credential_path = os.path.join(credential_dir, 'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials:
        status('Credentials required')
    elif credentials.invalid:
        status('No or Invalid credentials')
    else:
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
        service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)

        return service.spreadsheets()

def open_gspreadsheet(p):
    """Open Google Sheets spreadsheet, given its name."""
    sheets = google_sheets()
    sheet_md = sheets.get(spreadsheetId=p.name).execute()
    vs = Sheet(sheet_md['properties']['title'], p)
    vs.columns = [Column('title', lambda_eval('properties.title')),
                  Column('rowCount', lambda_eval('properties.gridProperties.rowCount')),
                  Column('columnCount', lambda_eval('properties.gridProperties.columnCount'))]
    vs.rows = sheet_md['sheets']
    vs.command(Key.ENTER, 'cursorRow')
    return vs

def open_gsheet(p):
    """Open Google Sheets spreadsheet, given its name."""
    sheets = google_sheets()
    sheet = sheets.values().get(spreadsheetId=p.name).execute()
    push_pyobj(p.name, sheet, p)
#    vs = Sheet(sheet_md['properties']['title'], p)
#    vs.columns = [Column('title', lambda_eval('properties.title')),
#                  Column('rowCount', lambda_eval('properties.gridProperties.rowCount')),
#                  Column('columnCount', lambda_eval('properties.gridProperties.columnCount'))]
#    vs.rows = sheet_md['sheets']
#    vs.command(Key.ENTER, 'cursorRow')
#    return vs

