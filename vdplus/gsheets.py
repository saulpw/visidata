import re

from visidata import vd, VisiData, Sheet, IndexSheet, SequenceSheet, ColumnItem, Path, AttrDict

@VisiData.api
def open_gdrive(vd, p):
    return GDriveSheet(p.name)

@VisiData.api
def open_gsheets(vd, p):
    m = re.search(r'([A-z0-9_]{44})', p.given)
    if m:
        return GSheetsIndex(p.name, source=m.groups()[0])


def gsheets_auth(scopes='spreadsheets drive'):
    import pickle
    import os.path

    GSHEETS_TOKEN_FILE = Path(vd.options.visidata_dir)/'gsheets-token.pickle'
    GSHEETS_CREDS = Path(vd.options.visidata_dir)/'gsheets-creds.json'
    creds = None
    if os.path.exists(GSHEETS_TOKEN_FILE):
        with open(GSHEETS_TOKEN_FILE, 'rb') as fp:
            creds = pickle.load(fp)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            SCOPES = [f'https://www.googleapis.com/auth/{x}.readonly' for x in scopes.split()]
            flow = InstalledAppFlow.from_client_secrets_file(GSHEETS_CREDS, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(GSHEETS_TOKEN_FILE, 'wb') as fp:
            pickle.dump(creds, fp)

    return creds

FILES_FIELDS_VISIBLE='''name size modifiedTime mimeType description owners'''.split()
FILES_FIELDS='''
id name size modifiedTime mimeType description owners
starred properties spaces version webContentLink webViewLink sharingUser lastModifyingUser shared
ownedByMe originalFilename md5Checksum size quotaBytesUsed headRevisionId imageMediaMetadata videoMediaMetadata parents
exportLinks contentRestrictions contentHints
'''.split()

class GDriveSheet(Sheet):
    rowtype='files'  # rowdef: AttrDict of result from Google Drive files.list API
    columns = [
            ColumnItem(x, width=None if x in FILES_FIELDS_VISIBLE else 0) for x in FILES_FIELDS
    ]
    @property
    def files(self):
        from googleapiclient import discovery
        return discovery.build("drive", "v3", credentials=gsheets_auth('drive')).files()

    def iterload(self):
        self.results = []
        page_token = None
        while True:
            ret = self.files.list(
                    pageSize=1000,
                    pageToken=page_token,
                    fields="nextPageToken, files(%s)" % ', '.join(FILES_FIELDS)
                    ).execute()

            self.results.append(ret)

            for r in ret.get('files', []):
                yield AttrDict(r)

            page_token = ret.get('nextPageToken', None)
            if not page_token:
                break

    def openRow(self, r):
        if r.mimeType == 'application/vnd.google-apps.spreadsheet':
            return GSheet(r.name, source=r.id)
        return vd.openSource(r.webContentLink)


class GSheetsIndex(IndexSheet):
    @property
    def spreadsheets(self):
        from googleapiclient import discovery
        return discovery.build("sheets", "v4", credentials=gsheets_auth('spreadsheets')).spreadsheets()

    def iterload(self):
        googlesheet = self.spreadsheets.get(spreadsheetId=self.source).execute()
        vd.status(googlesheet['properties']['title'])

        for gsheet in googlesheet['sheets']:
            yield AttrDict(gsheet)

    def openRow(self, r):
        return GSheet(r.properties.title, source=self.source, spreadsheets=self.spreadsheets)


class GSheet(SequenceSheet):
    '.source is gsheet id; .name is sheet name'
    def iterload(self):
        result = self.spreadsheets.values().get(spreadsheetId=self.source, range=self.name).execute()
        yield from result.get('values', [])
