from visidata import *

content_filetypes = {
    'tab-separated-values': 'tsv'  # thanks @lindner
}


class HttpPath(PathFd):
    def __init__(self, url, req):
        from urllib.parse import urlparse
        obj = urlparse(url)
        super().__init__(obj.path, req)
        self.req = req


def openurl_http(p, filetype=None):
    import requests
    r = requests.get(p.url, stream=True)
    if not filetype:
        contenttype = r.headers['content-type']
        subtype = contenttype.split(';')[0].split('/')[-1]
        filetype = content_filetypes.get(subtype, subtype)
    return openSource(HttpPath(p.url, r.iter_lines(decode_unicode=True)), filetype=filetype)

openurl_https = openurl_http
