from visidata import vd, VisiData, Sheet, IndexSheet, SequenceSheet, ColumnItem, Path, AttrDict, ColumnAttr, asyncthread


@VisiData.api
def open_gdrive(vd, p):
    return GDriveSheet(p.name)


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
        return discovery.build("drive", "v3", credentials=gsheets_auth('drive.readonly')).files()

    def iterload(self):
        self.results = []
        page_token = None
        while True:
            ret = self.files.list(
                    pageSize=1000,
                    pageToken=page_token,
                    fields="nextPageToken, files(%s)" % ','.join(FILES_FIELDS)
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
