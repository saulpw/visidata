from visidata import Path, RepeatFile, options, vd

content_filetypes = {
    'tab-separated-values': 'tsv'  # thanks @lindner
}


def openurl_http(path, filetype=None):
    import requests

    response = requests.get(path.given, stream=True)

    # if filetype not given, auto-detect with hacky mime-type parse
    if not filetype:
        ext = path.suffix[1:].lower()
        openfunc = vd.getGlobals().get(f'open_{ext}')

        if openfunc:
            filetype = ext

        else:
            contenttype = response.headers['content-type']
            subtype = contenttype.split(';')[0].split('/')[-1]
            filetype = content_filetypes.get(subtype, subtype)

    # If no charset is provided by response headers, use the user-specified
    # encoding option (which defaults to UTF-8) and hope for the best.  The
    # alternative is an error because iter_lines() will produce bytes.  We're
    # streaming so can't use response.apparent_encoding.
    if not response.encoding:
        response.encoding = options.encoding

    # create resettable iterator over contents
    fp = RepeatFile(iter_lines=response.iter_lines(decode_unicode=True))

    # call open_<filetype> with a usable Path
    return vd.openSource(Path(path.given, fp=fp), filetype=filetype)

openurl_https = openurl_http
