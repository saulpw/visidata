#!/usr/bin/env python3

import optparse
from visidata import *

option('zulip_backlog', 10000, '# messages to get on load')


command('T', 'vd.push(ZStreamsSheet(z_client))', 'show list of subscribed streams/topics')
#command('gT', 'vd.push(ZStreamsSheet(z_client, True))', 'show list of all streams/topics')
#command('W', 'vd.push(ZMessagesPrivateSheet())', 'show list of subscribed streams/topics')
command('Z', 'vd.push(z_rpc(z_client.get_members(), "members"))', 'push list of members')
command('KEY_F(2)', 'push_pyobj("profile", z_client.get_profile())', 'push the connected user\'s profile')
command('KEY_F(3)', 'vd.push(ZSubscriptions(z_client))', 'push the connected user\'s subscriptions')


def z_rpc(r, result_field_name=None):
    if r['result'] != 'success':
        return load_pyobj(result_field_name + '_error', r)
    elif result_field_name:
        obj = r[result_field_name]
        return load_pyobj(result_field_name, obj)

class ZSubscriptions(Sheet):
    def __init__(self, client):
        super().__init__('subscriptions', client)
        self.columns = [
            ColumnItem('topic', 'name'),
            Column('num_subscribers', type=int, getter=lambda r: len(r['subscribers']))
        ]
        self.command(ENTER, 'vd.push(ZMessagesStreamsSheet(z_client, stream=cursorRow["name"]))', 'push sheet for this stream')

    def reload(self):
        r = self.source.list_subscriptions()
        if r['result'] != 'success':
            push_pyobj('subscriptions_error', r)
            return

        self.rows = r['subscriptions']

class ZStreamsSheet(Sheet):
    def __init__(self, client, all_streams=False):
        super().__init__('streams', client)

    def reload(self):
        r = self.source.get_streams(include_public=True, include_subscribed=True)
        self.rows = r['streams']
        self.columns = DictKeyColumns(self.rows[0])


class ZMessagesStreamsSheet(Sheet):
    def __init__(self, client, **kwargs):
        super().__init__('messages', client)
        self.message_filters = kwargs
        self.columns = [
            ColumnItem('time', 'timestamp', type=date, fmtstr='%H:%M'),
            Column('channel', str, lambda r,vs=self: vs.get_channel_name(r), width=20),
            ColumnItem('sender_name', 'sender_full_name', width=30),
            ColumnItem('message', 'content'),
        ]
        self.command('v', 'vd.push(ZMessagesStreamsSheet(z_client, stream=cursorRow["display_recipient"], topic=cursorRow["subject"]))', 'push sheet of this stream/topic only')
        self.command('gv', 'vd.push(ZMessagesStreamsSheet(z_client, stream=cursorRow["display_recipient"]))', 'push sheet of this stream only (all topics)')
        self.command(ENTER, 'vd.push(TextSheet(get_channel_name(cursorRow), cursorRow["content"]))', 'push text sheet of message content')
        self.command('r', 'reply_message(input(cursorRow["display_recipient"][1]["short_name"]+"> ", "message"), cursorRow)', 'reply to current topic')
        self.command('e', 'update_message(cursorRow["id"], editCell(3, cursorRowIndex))', 'edit message content')

    @async
    def reload(self):
        # kill previous thread
        self.rows = []
        client = self.source
        narrow = list(self.message_filters.items())
        req = {
            'num_before': options.zulip_backlog,
            'num_after': 0,
            'anchor': 1000000000,
            'apply_markdown': False,
            'narrow': narrow
        }


        r = client.call_endpoint(url='messages', method='GET', request=req)
        if r['result'] == 'success':
            for msg in r['messages']:
                self.rows.append(msg)

        self.cursorRowIndex = len(self.rows)

        client.call_on_each_event(lambda event,vs=self: vs.received_message(event['message']) if event['type'] == 'message' else None, ['message'], narrow=narrow)

    def get_channel_name(self, r):
        recp = r['display_recipient']
        if isinstance(recp, list):  # private message
            return '[%s]' % recp[0]['full_name']
        else:
            return '%s:%s' % (recp, r['subject'])

    def update_message(self, msgid, content):
        req = {
            "message_id": msgid,
            "content": content
        }
        z_rpc(self.source.update_message(req))


    def received_message(self, msg):
        self.rows.append(msg)
        if self.cursorRowIndex >= self.nRows-1:
            self.cursorRowIndex = self.nRows-1

    def reply_message(self, msg, row):
        recp = row['display_recipient']
        if isinstance(recp, list):
            for dest in recp:
                self.send_message(msg, row['subject'], dest['email'], 'private')
        else:
            self.send_message(msg, row['subject'], dest, 'stream')

    def send_message(self, msg, subject, dest, msgtype='stream'):
        req = {
            'type': msgtype,
            'content': msg,
            'subject': subject,
            'to': dest,
        }
        r = self.source.send_message(req)

        if r['result'] != 'success':
            push_pyobj('send_message_result', r)


def main():
    import zulip
    parser = optparse.OptionParser()
    parser.add_option_group(zulip.generate_option_group(parser))
    (options, args) = parser.parse_args()
    client = zulip.init_from_options(options)

    setGlobal('z_client', client)
    setGlobal('z_rpc', z_rpc)
    setGlobal('ZStreamsSheet', ZStreamsSheet)
    setGlobal('ZMessagesStreamsSheet', ZMessagesStreamsSheet)
    setGlobal('ZSubscriptions', ZSubscriptions)

    run([ZMessagesStreamsSheet(client)])


main()
