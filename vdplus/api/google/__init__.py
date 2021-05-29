
from visidata import vd, VisiData, Sheet, IndexSheet, SequenceSheet, ColumnItem, Path, AttrDict, ColumnAttr, asyncthread
from .gsheets import *
from .gdrive import *


def _google_creds_fn():
    from pkg_resources import resource_filename
    return resource_filename('vdplus.api.google', 'google-creds.json')


@VisiData.api
def google_auth(vd, scopes='spreadsheets.readonly'):
    import pickle
    import os.path
    GSHEETS_TOKEN_FILE = Path(vd.options.visidata_dir)/f'google-{scopes}.pickle'
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
            SCOPES = [f'https://www.googleapis.com/auth/{x}' for x in scopes.split()]
            flow = InstalledAppFlow.from_client_secrets_file(_google_creds_fn(), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(GSHEETS_TOKEN_FILE, 'wb') as fp:
            pickle.dump(creds, fp)

    return creds
