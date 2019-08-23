from visidata import *

content_filetypes = {
    'tab-separated-values': 'tsv'  # thanks @lindner
}


def openurl_http(p, filetype=None):
    import requests
    r = requests.get(p.given, stream=True)
    if not filetype:
        contenttype = r.headers['content-type']
        subtype = contenttype.split(';')[0].split('/')[-1]
        filetype = content_filetypes.get(subtype, subtype)
    return openSource(Path(p.given, fp=RepeatFile(iter_lines=r.iter_lines(decode_unicode=True))), filetype=filetype)

openurl_https = openurl_http
