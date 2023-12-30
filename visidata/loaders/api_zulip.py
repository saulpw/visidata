import time

from visidata import vd, VisiData, BaseSheet, Sheet, TextSheet, PyobjSheet
from visidata import ItemColumn, Column, vlen, date, asyncsingle, ENTER, AttrDict

vd.option('zulip_batch_size', -100, 'number of messages to fetch per call (<0 to fetch before anchor)')
vd.option('zulip_anchor', 1000000000, 'message id to start fetching from')
vd.option('zulip_delay_s', 0.00001, 'seconds to wait between calls (0 to stop after first)')
vd.option('zulip_api_key', '', 'Zulip API key')
vd.option('zulip_email', '', 'Email for use with Zulip API key')


@VisiData.api
def open_zulip(vd, p):
    vd.importExternal('zulip')
    import zulip

    if not vd.options.zulip_api_key:
        vd.warning('zulip_api_key must be set first')
        vd.status('Enter your login email and Zulip API key (see _https://zulip.com/api/api-keys_).')
        email = vd.input(f'Login email for {p.given}: ', record=False)
        api_key = vd.input(f'Zulip API key: ', record=False)

        vd.setPersistentOptions(zulip_email=email, zulip_api_key=api_key)

    vd.z_client = zulip.Client(site=p.given, api_key=vd.options.zulip_api_key, email=vd.options.zulip_email)

    return vd.subscribedStreams


VisiData.openhttp_zulip = VisiData.open_zulip


@VisiData.api
def z_rpc(vd, r, result_field_name=None):
    if r['result'] != 'success':
        return PyobjSheet(result_field_name+'_error', source=r)
    elif result_field_name:
        return PyobjSheet(result_field_name, source=r[result_field_name])


@VisiData.lazy_property
def allStreams(vd):
    return ZulipStreamsSheet("all_streams", zulip_func='get_streams', zulip_result_key="streams", zulip_kwargs=dict(include_public=True, include_subscribed=True))


@VisiData.lazy_property
def subscribedStreams(vd):
    return ZulipStreamsSheet("subscriptions", zulip_func='get_subscriptions', zulip_result_key="subscriptions")


@VisiData.lazy_property
def allMessages(vd):
    return ZulipMessagesSheet("all_messages")


@VisiData.api
def parseColumns(vd, fieldlist):
    for cname in fieldlist:
        kwargs = {}
        while not cname[0].isalpha():
            if cname[0] == '#': kwargs['type'] = int
            elif cname[0] == '@': kwargs['type'] = date
            elif cname[0] == '-': kwargs['width'] = 0
            else: break
            cname = cname[1:]
        yield ItemColumn(cname, **kwargs)


class ZulipAPISheet(Sheet):
    zulip_func = None
    zulip_result_key = ''
    zulip_args = []
    zulip_kwargs = {}
    fields = ''

    def iterload(self):
        self.columns = []
        for c in vd.parseColumns(self.fields.split()):
            self.addColumn(c)

        zulip_func = self.zulip_func
        if isinstance(zulip_func, str): # allow later binding for startup perf
            zulip_func = getattr(vd.z_client, zulip_func)
        r = zulip_func(*self.zulip_args, **self.zulip_kwargs)
        if r['result'] != 'success':
            vd.push(PyobjSheet(self.zulip_result_key+'_error', source=r))
            return
        yield from r[self.zulip_result_key]

    def addRow(self, r, **kwargs):
        return super().addRow(AttrDict(r), **kwargs)


class ZulipStreamsSheet(ZulipAPISheet):
    guide = '''# Zulip Streams

- `Enter` to open recent messages from the stream
- `z Enter` to open list of topics from the stream
'''
    rowtype = 'streams'  # rowdef: dict of stream from server
    fields = '-#stream_id name @date_created description -rendered_description -invite_only -is_web_public -stream_post_policy -history_public_to_subscribers -#first_message_id -#message_retention_days -is_announcement_only'

    def openRow(self, r):
        return ZulipMessagesSheet(r.name, filters=dict(stream=r.name))

    def openCell(self, c, r):
        return ZulipTopicsSheet(r.name+'_topics',
                             zulip_func=vd.z_client.get_stream_topics,
                             zulip_args=[r.stream_id],
                             zulip_result_key='topics')


class ZulipTopicsSheet(ZulipAPISheet):
    rowtype = 'topics'  # rowdef: dict of topic from server
    fields='name #max_id'
    def openRow(self, r):
        return ZulipMessagesSheet(f'{r.name}:{r.subject}', filters=dict(stream=r.name, topic=r.subject))


class ZulipMembersSheet(ZulipAPISheet):
    guide = '''# Zulip Members
- `Enter` to open list of messages from this member
'''
    rowtype = 'members'  # rowdef: dict of member from server
    fields = '''-#user_id full_name email timezone @date_joined -#avatar_version -is_admin -is_owner -is_guest -is_bot -#role -is_active -avatar_url -bot_type -#bot_owner_id'''
    def openRow(self, r):
        return ZulipMessagesSheet(r.display_recipient, filters=dict(stream=r.display_recipient))


class ZulipMessagesSheet(Sheet):
    guide = '''# Zulip Messages Sheet
Loads continuously starting with most recent, until all messages have been read.

- `Ctrl+C` to cancel loading.
- `Enter` to open message in word-wrapped text sheet
'''
    rowtype = 'messages'  # rowdef: dict of message from server
#    fields = ''
    columns = [
        ItemColumn('timestamp', type=date, fmtstr='%Y-%m-%d %H:%M'),
        ItemColumn('sender', 'sender_full_name'),
        ItemColumn('sender_email', width=0),
        ItemColumn('recipient', 'display_recipient'),
        ItemColumn('subject'),
        ItemColumn('content'),
        ItemColumn('client', width=0),
        ItemColumn('reactions', type=vlen),
        ItemColumn('submessages', type=vlen),
        ItemColumn('flags', width=0),
    ]
    filters={}

    @asyncsingle # kill previous thread
    def reload(self):
        self.rows = []
        narrow = list(self.filters.items())
        n = self.options.zulip_batch_size
        req = AttrDict(
            num_before = -n if n < 0 else 0,
            num_after = n if n > 0 else 0,
            anchor = self.options.zulip_anchor,
            apply_markdown = False,
            narrow = narrow)

        while True:
            r = vd.z_client.call_endpoint(url='messages', method='GET', request=req)
            if r['result'] == 'success':
                if not r['messages']: break
                for i, msg in enumerate(r['messages']):
                    self.addRow(msg, index=i)
                req['anchor'] = min(msg['id'] for msg in r['messages'])-1
                s = self.options.zulip_delay_s
                if s <= 0:
                    break
                time.sleep(s)

#        vd.status('finished loading, waiting for new messages')
#        vd.z_client.call_on_each_event(self.received_event, ['message'], narrow=narrow)

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
        vd.z_rpc(vd.z_client.update_message(req))

    def openRow(self, r):
        vs = TextSheet(self.get_channel_name(r), source=[r["content"]])
        vs.options.wrap = True
        return vs

    def received_event(self, event):
        if event['type'] == 'message':
            self.addRow(event['message'])

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
        r = vd.z_client.send_message(req)

        if r['result'] != 'success':
            vd.push(PyobjSheet('send_message_result', source=r))


vd.addGlobals({
    'ZulipMembersSheet': ZulipMembersSheet,
    'ZulipStreamsSheet': ZulipStreamsSheet,
    'ZulipAPISheet': ZulipAPISheet,
    'ZulipMessagesSheet': ZulipMessagesSheet,
})

ZulipAPISheet.addCommand('', 'open-zulip-profile', 'vd.push(PyobjSheet("profile", source=z_client.get_profile()))', 'open connected user\'s profile')
ZulipAPISheet.addCommand('', 'open-zulip-members', 'vd.push(ZulipMembersSheet("members", zulip_func=z_client.get_users, zulip_result_key="members"))', 'open list of all members')
ZulipAPISheet.addCommand('', 'open-zulip-streams', 'vd.push(vd.allStreams)', 'open list of all streams')
ZulipAPISheet.addCommand('', 'open-zulip-subs', 'vd.push(vd.subscribedStreams)', 'open list of subscribed streams')
ZulipAPISheet.addCommand('', 'open-zulip-msgs', 'vd.push(vd.allMessages)', 'open list of all messages')

ZulipMessagesSheet.addCommand('', 'reply-zulip-msg', 'reply_message(input(cursorRow["display_recipient"][1]["short_name"]+"> ", "message"), cursorRow)', 'reply to current topic')
ZulipMessagesSheet.addCommand('', 'edit-zulip-msg', 'update_message(cursorRow["id"], editCell(3, cursorRowIndex))', 'edit message content')

vd.addMenuItems('''
File > Zulip > profile > open-zulip-profile
File > Zulip > member list > open-zulip-members
File > Zulip > streams > open-zulip-streams
File > Zulip > subscriptions > open-zulip-subs
File > Zulip > messages > open-zulip-subs
File > Zulip > reply > reply-zulip-msg
File > Zulip > edit message > edit-zulip-msg
''')
