import boto3

from vdtui import *

option('s3_max_viewsize', 1024000, 'download files over this size')


def openurl_s3(purl):
    return S3Sheet(purl.netloc)


class S3BucketSheet(Sheet):
    columns = [
        Column('key', getter=lambda r: r.key, setter=lambda s,c,r,v: s.rename(r, v)),
        ColumnAttr('size'),
        Column('owner', getter=lambda r: r.owner['DisplayName']),
        ColumnAttr('last_modified'),
        ColumnAttr('storage_class'),
    ]
    commands = [
        Command('V', 'dive(cursorRow)', 'view or download this file'),
        Command(ENTER, 'push_pyobj(cursorRow.key, cursorRow.get())', 'view response for get() of this file'),
        Command('d', 'cursorRow.delete(); reload()', 'delete this key from the bucket'),
        Command('gd', 'for r in selectedRows: r.delete(); reload()', 'delete selected keys from the bucket')
    ]

    @async
    def reload(self):
        self.s3 = boto3.resource('s3')
        self.bucket = self.s3.Bucket(self.source)
        self.rows = []
        for obj in self.bucket.objects.all():
            self.addRow(obj)

    def rename(self, row, newname):
        self.s3.Object(self.bucket, v).copy_from(CopySource=r.key)
#        row.delete()
        self.reload()

    def dive(self, row):
        if row.size > options.s3_max_viewsize:
            input('download to: ', value=row.key, type='file')
        else:
            vd().push(TextSheet(row.key, row.get()['Body'].read().decode('utf-8')))


class S3Buckets(Sheet):
    columns = [ColumnAttr('bucket', 'name')]
    commands = [
        Command(ENTER, 'vd.push(S3BucketSheet(cursorRow.name, cursorRow.name))', 'dive into this bucket')
    ]
    def reload(self):
        s3 = boto3.resource('s3')
        self.rows = list(s3.buckets.all())


g_aws_s3 = S3Buckets('s3')
#from pyobj import *
#g_s3 = load_pyobj('s3obj', boto3.resource('s3'))

addGlobals(globals())

