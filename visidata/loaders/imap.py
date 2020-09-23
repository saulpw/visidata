from visidata import vd, TableSheet, asyncthread, ColumnItem, Column, ColumnAttr, Progress
from urllib.parse import urlparse


def openurl_imap(p, **kwargs):
    url = urlparse(p.given)
    password = url.password or vd.error('no password given in url') # vd.input("imap password for %s" % user, display=False))
    return ImapSheet(url.hostname, source=url, password=password)


class ImapSheet(TableSheet):
    columns = [
        ColumnItem('message-id'),
        ColumnItem('folder'),
        ColumnItem('Date'),
        ColumnItem('From'),
        ColumnItem('To'),
        ColumnItem('Subject'),
        ColumnAttr('defects'),
        Column('payload', getter=lambda c,r: r.get_payload()),
        Column('content_type', getter=lambda c,r: r.get_content_type()),
    ]
    nKeys = 1

    @asyncthread
    def reload(self):
        import imaplib
        import email.parser

        m = imaplib.IMAP4_SSL(host=self.source.hostname)
        user = self.source.username
        m.login(user, self.password)
        typ, folders = m.list()
        for r in Progress(folders, gerund="downloading"):
            fname = r.decode('utf-8').split()[-1][1:-1]
            try:
                m.select(fname)
                typ, data = m.search(None, 'ALL')
                for num in data[0].split():
                    typ, msgbytes = m.fetch(num, '(RFC822)')
                    if typ != 'OK':
                        vd.warning(typ, msgbytes)
                        continue

                    msg = email.message_from_bytes(msgbytes[0][1])
                    msg['folder'] = fname
                    self.addRow(msg)

                m.close()
            except Exception:
                vd.exceptionCaught()

        m.logout()

    def addRow(self, row, **kwargs):
        if row.is_multipart():
            for p in row.get_payload():
                for hdr in 'message-id folder Date From To Subject'.split():
                    if hdr in row:
                        p[hdr] = row[hdr]
                self.addRow(p, **kwargs)
        else:
            super().addRow(row, **kwargs)
