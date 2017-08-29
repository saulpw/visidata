import boto3

from vdtui import *

option('s3_max_viewsize', 1024000, 'download files over this size')


def openurl_s3(purl):
    return S3Sheet(purl.netloc)


class S3BucketSheet(Sheet):
    def __init__(self, bucket):
        super().__init__(bucket, bucket)
        self.s3 = boto3.resource('s3')
        self.bucket = None
        self.columns = [
            Column('key', getter=lambda r: r.key, setter=lambda r,v,s=self: s.rename(r, v)),
            ColumnAttr('size'),
            Column('owner', getter=lambda r: r.owner['DisplayName']),
            ColumnAttr('last_modified'),
            ColumnAttr('storage_class'),
        ]
        self.command('V', 'dive(cursorRow)', 'view or download this file')
        self.command(ENTER, 'push_pyobj(cursorRow.key, cursorRow.get())', 'view response for get() of this file')
        self.command('d', 'cursorRow.delete()', 'delete this key from the bucket')

    def rename(self, row, newname):
        self.s3.Object(self.bucket, v).copy_from(CopySource=r.key)
#        row.delete()
        self.reload()

    def dive(self, row):
        if row.size > options.s3_max_viewsize:
            input('download to: ', value=row.key, type='file')
        else:
            vd().push(TextSheet(row.key, row.get()['Body'].read().decode('utf-8')))

    @async
    def reload(self):
        self.bucket = self.s3.Bucket(self.source)
        self.rows = []
        for obj in self.bucket.objects.all():
            self.addRow(obj)


class S3Buckets(Sheet):
    def reload(self):
        self.command(ENTER, 'vd.push(S3BucketSheet(cursorRow.name))', 'dive into this bucket')
        s3 = boto3.resource('s3')
        self.columns = [ColumnAttr('bucket', 'name')]
        self.rows = []
        for x in s3.buckets.all():
            self.addRow(x)


g_aws_s3 = S3Buckets('s3')
#from pyobj import *
#g_s3 = load_pyobj('s3obj', boto3.resource('s3'))

addGlobals(globals())

