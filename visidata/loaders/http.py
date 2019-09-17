from visidata import Path, RepeatFile, openSource

content_filetypes = {
    'tab-separated-values': 'tsv'  # thanks @lindner
}


def openurl_http(path, filetype=None):
    import requests

    response = requests.get(path.given, stream=True)

    # if filetype not given, auto-detect with hacky mime-type parse
    if not filetype:
        contenttype = response.headers['content-type']
        subtype = contenttype.split(';')[0].split('/')[-1]
        filetype = content_filetypes.get(subtype, subtype)

    # create resettable iterator over contents
    fp = RepeatFile(iter_lines=response.iter_lines(decode_unicode=True))

    # call open_<filetype> with a usable Path
    return openSource(Path(path.given, fp=fp), filetype=filetype)

openurl_https = openurl_http
