from visidata import *

class HttpPath(PathFd):
    def __init__(self, url, req):
        from urllib.parse import urlparse
        obj = urlparse(url)
        super().__init__(obj.path, req)
        self.req = req


def openurl_http(p, filetype=None):
    import requests
    r = requests.get(p.url, stream=True)
    return openSource(HttpPath(p.url, r.iter_lines(decode_unicode=True)), filetype=filetype)

openurl_https = openurl_http
