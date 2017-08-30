import boto3

from vdtui import *

option('aws_days', 365, 'number of days of statistics to get')

def findValue(L, name):
    for x in L:
        if x['Name'] == name:
            return x['Value']


class CloudWatchMetrics(Sheet):
    columns = [
        ColumnAttr('namespace'),
        ColumnAttr('name'),
    ]
    commands = [
        Command(ENTER, 'push_pyobj(cursorRow.metric_name, load_metric(cursorRow))', '')
    ]

    def load_metric(self, row):
        stats = row.get_statistics(
                    StartTime=datetime.datetime.utcnow() - datetime.timedelta(days=options.aws_days),
                    EndTime=datetime.datetime.utcnow(),
                    Period=3600*24,  # daily
                    Dimensions=row.dimensions,
                    Statistics='Minimum Average Maximum'.split()
                )
        return stats["Datapoints"]

    @async
    def reload(self):
        self.rows = []
        allCols = {}
        for m in boto3.resource('cloudwatch').metrics.all():
            self.addRow(m)
            for i, dim in enumerate(m.dimensions):
                name = dim['Name']
                if name not in allCols:
                    c = Column(name, getter=lambda r,name=name: findValue(r.dimensions, name))
                    self.addColumn(c)
                    allCols[name] = c

#        self.cw.alarms.all()
g_aws_cloudwatch_metrics = CloudWatchMetrics('cloudwatch_metrics')

addGlobals(globals())
