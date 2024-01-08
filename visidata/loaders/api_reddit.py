'''# RedditSheet

- [:keystrokes]Ctrl+O[/] to open a browser tab to [:code]{sheet.cursorRow.display_name_prefixed}[/]
- [:keystrokes]g Ctrl+O[/] to open browser windows for {sheet.nSelectedRows} selected subreddits

- [:keystrokes]Enter[/] to open sheet with top ~1000 submissions for [:code]{sheet.cursorRow.display_name_prefixed}[/]
- [:keystrokes]g Enter[/] to open sheet with top ~1000 submissions for {sheet.nSelectedRows} selected subreddits

- [:keystrokes]ga[/] to append more subreddits matching input by name or description
'''

import visidata
from visidata import vd, VisiData, Sheet, AttrColumn, asyncthread, ENTER, anytype, date


vd.option('reddit_client_id', '', 'client_id for reddit api')
vd.option('reddit_client_secret', '', 'client_secret for reddit api')
vd.option('reddit_user_agent', visidata.__version__, 'user_agent for reddit api')


@VisiData.api
def open_reddit(vd, p):
    vd.importExternal('praw')
    vd.enable_requests_cache()

    if not vd.options.reddit_client_id:
        return RedditGuide('reddit_guide')

    if p.given.startswith('r/') or p.given.startswith('/r/'):
        return SubredditSheet(p.base_stem, source=p.base_stem.split('+'), search=(p.given[0]=='/'))

    if p.given.startswith('u/') or p.given.startswith('/u/'):
        return RedditorsSheet(p.base_stem, source=p.base_stem.split('+'), search=(p.given[0]=='/'))

    return SubredditSheet(p.base_stem, source=p)

vd.new_reddit = vd.open_reddit

@VisiData.cached_property
def reddit(vd):
    import praw
    return praw.Reddit(check_for_updates=False, **vd.options.getall('reddit_'))


subreddit_hidden_attrs='''
name #accounts_active accounts_active_is_fuzzed advertiser_category
all_original_content allow_chat_post_creation allow_discovery
allow_galleries allow_images allow_polls allow_predictions
allow_predictions_tournament allow_videogifs allow_videos
banner_background_color banner_background_image banner_img banner_size
can_assign_link_flair can_assign_user_flair collapse_deleted_comments
comment_score_hide_mins community_icon community_reviewed @created
@created_utc description_html disable_contributor_requests
display_name display_name_prefixed emoji emojis_custom_size
emojis_enabled filters free_form_reports fullname has_menu_widget
header_img header_size header_title hide_ads icon_img icon_size
is_chat_post_feature_enabled is_crosspostable_subreddit
is_enrolled_in_new_modmail key_color lang link_flair_enabled
link_flair_position mobile_banner_image mod notification_level
original_content_tag_enabled over18 prediction_leaderboard_entry_type
primary_color public_description public_description_html public_traffic
quaran quarantine restrict_commenting restrict_posting show_media
show_media_preview spoilers_enabled submission_type submit_link_label
submit_text submit_text_html submit_text_label suggested_comment_sort
user_can_flair_in_sr user_flair_background_color user_flair_css_class
user_flair_enabled_in_sr user_flair_position user_flair_richtext
user_flair_template_id user_flair_text user_flair_text_color
user_flair_type user_has_favorited user_is_banned user_is_contributor
user_is_moderator user_is_muted user_is_subscriber user_sr_flair_enabled
user_sr_theme_enabled #videostream_links_count whitelist_status widgets
wiki wiki_enabled wls
'''

post_hidden_attrs='''
all_awardings allow_live_comments @approved_at_utc approved_by archived
author_flair_background_color author_flair_css_class author_flair_richtext
author_flair_template_id author_flair_text author_flair_text_color
author_flair_type author_fullname author_patreon_flair author_premium
awarders @banned_at_utc banned_by can_gild can_mod_post category clicked
comment_limit comment_sort content_categories contest_mode @created_utc
discussion_type distinguished domain edited flair fullname gilded
gildings hidden hide_score is_crosspostable is_meta is_original_content
is_reddit_media_domain is_robot_indexable is_self is_video likes
link_flair_background_color link_flair_css_class link_flair_richtext
link_flair_text link_flair_text_color link_flair_type locked media
media_embed media_only mod mod_note mod_reason_by mod_reason_title
mod_reports name no_follow num_crossposts num_duplicates num_reports
over_18 parent_whitelist_status permalink pinned pwls quarantine
removal_reason removed_by removed_by_category report_reasons saved
score secure_media secure_media_embed selftext_html send_replies
shortlink spoiler stickied subreddit_id subreddit_name_prefixed
subreddit_subscribers subreddit_type suggested_sort thumbnail
thumbnail_height thumbnail_width top_awarded_type total_awards_received
treatment_tags upvote_ratio user_reports #view_count visited
whitelist_status wls
'''

comment_hidden_attrs='''
all_awardings @approved_at_utc approved_by archived associated_award
author_flair_background_color author_flair_css_class author_flair_richtext
author_flair_template_id author_flair_text author_flair_text_color
author_flair_type author_fullname author_patreon_flair author_premium
awarders @banned_at_utc banned_by body_html can_gild can_mod_post
collapsed collapsed_because_crowd_control collapsed_reason comment_type
controversiality @created_utc distinguished fullname gilded gildings
is_root is_submitter likes link_id locked mod mod_note mod_reason_by
mod_reason_title mod_reports name no_follow num_reports parent_id
permalink removal_reason report_reasons saved #score #score_hidden
send_replies stickied submission subreddit_id subreddit_name_prefixed
subreddit_type top_awarded_type total_awards_received treatment_tags
user_reports
'''

redditor_hidden_attrs='''
#awardee_karma #awarder_karma @created @created_utc
fullname has_subscribed has_verified_email hide_from_robots icon_img id
is_employee is_friend is_gold is_mod pref_show_snoovatar
snoovatar_img snoovatar_size stream #total_karma verified
subreddit.banner_img subreddit.name subreddit.over_18 subreddit.public_description #subreddit.subscribers subreddit.title
'''

def hiddenCols(hidden_attrs):
    coltypes = { t.icon:t.typetype for t in vd.typemap.values() if not t.icon.isalpha() }
    for attr in hidden_attrs.split():
        coltype = anytype
        if attr[0] in coltypes:
            coltype = coltypes.get(attr[0])
            attr = attr[1:]
        yield AttrColumn(attr, type=coltype, width=0)


class SubredditSheet(Sheet):
    guide = __doc__
    # source is a text list of subreddits
    rowtype = 'subreddits'  # rowdef: praw.Subreddit
    nKeys=1
    search=False
    columns = [
        AttrColumn('display_name_prefixed', width=15),
        AttrColumn('active_user_count', type=int),
        AttrColumn('subscribers', type=int),
        AttrColumn('subreddit_type'),
        AttrColumn('title'),
        AttrColumn('description', width=50),
        AttrColumn('url', width=10),
    ] + list(hiddenCols(subreddit_hidden_attrs))

    def iterload(self):
        for name in self.source:
            name = name.strip()
            if self.search:
                yield from vd.reddit.subreddits.search(name)
            else:
                try:
                    r = vd.reddit.subreddit(name)
                    r.display_name_prefixed
                    yield r
                except Exception as e:
                    vd.exceptionCaught(e)

    def openRow(self, row):
        return RedditSubmissions(row.display_name_prefixed, source=row)

    def openRows(self, rows):
        comboname = '+'.join(row.display_name for row in rows)
        return RedditSubmissions(comboname, source=vd.reddit.subreddit(comboname))


class RedditorsSheet(Sheet):
    # source is a text list of usernames
    rowtype = 'redditors'  # rowdef: praw.Subreddit
    nKeys=1
    columns = [
        AttrColumn('name', width=15),
        AttrColumn('comment_karma', type=int),
        AttrColumn('link_karma', type=int),
        AttrColumn('comments'),
        AttrColumn('submissions'),
    ] + list(hiddenCols(redditor_hidden_attrs))

    def iterload(self):
        for name in self.source:
            if self.search:
                yield from vd.reddit.redditors.popular(name)
            else:
                yield vd.reddit.redditor(name)

    def openRow(self, row):
        return RedditSubmissions(row.fullname, source=row.submissions)

    def openRows(self, rows):
        comboname = '+'.join(row.name for row in rows)
        return RedditSubmissions(comboname, source=vd.reddit.redditor(comboname).submissions)


class RedditSubmissions(Sheet):
    guide = '''# Reddit Submissions

  [:keys]Enter[/] to open sheet with comments for the current post
  [:keys]ga[/] to add posts in this subreddit matching input'''

    # source=ListingGenerator
    rowtype='reddit posts' # rowdef: praw.Submission
    nKeys=2
    columns = [
        AttrColumn('subreddit'),
        AttrColumn('id', width=0),
        AttrColumn('created', width=12, type=date),
        AttrColumn('author'),
        AttrColumn('ups', width=8, type=int),
        AttrColumn('downs', width=8, type=int),
        AttrColumn('num_comments', width=8, type=int),
        AttrColumn('title', width=50),
        AttrColumn('selftext', width=60),
        AttrColumn('url'),
        AttrColumn('comments', width=0),
    ] + list(hiddenCols(post_hidden_attrs))

    def iterload(self):
        kind = 'new' # 'top'
        f = getattr(self.source, kind, None)
        if f:
            yield from f(limit=10000)

    def openRow(self, row):
        return RedditComments(row.id, source=row.comments.list())


class RedditComments(Sheet):
    # source=list of comments
    rowtype='comments' # rowdef: praw.Comment
    nKeys=2
    columns=[
        AttrColumn('subreddit', width=0),
        AttrColumn('id', width=0),
        AttrColumn('ups', width=4, type=int),
        AttrColumn('downs', width=4, type=int),
        AttrColumn('replies', type=list),
        AttrColumn('created', type=date),
        AttrColumn('author'),
        AttrColumn('depth', type=int),
        AttrColumn('body', width=60),
        AttrColumn('edited', width=0),
    ] + list(hiddenCols(comment_hidden_attrs))

    def iterload(self):
        yield from self.source

    def openRow(self, row):
        return RedditComments(row.id, source=row.replies)


class RedditGuide(RedditSubmissions):
    guide = '''# Authenticate Reddit
The Reddit API must be configured before use.

1. Login to Reddit and go to [:underline]https://www.reddit.com/prefs/apps[/].
2. Create a "script" app. (Use "[:underline]http://localhost:8000[/]" for the redirect uri)
3. Add credentials to visidatarc:

    options.reddit_client_id = '...'      # below the description in the upper left
    options.reddit_client_secret = '...'

## Use [:code]reddit[/] filetype for subreddits or users

Multiple may be specified, joined with "+".

    vd r/commandline.reddit
    vd u/gallowboob.reddit
    vd r/rust+golang+python.reddit
    vd u/spez+kn0thing.reddit
'''

@SubredditSheet.api
@asyncthread
def addRowsFromQuery(sheet, q):
    for r in vd.reddit.subreddits.search(q):
        sheet.addRow(r, index=sheet.cursorRowIndex+1)


@RedditSubmissions.api
@asyncthread
def addRowsFromQuery(sheet, q):
    for r in sheet.source.search(q, limit=None):
        sheet.addRow(r, index=sheet.cursorRowIndex+1)


@VisiData.api
def sysopen_subreddits(vd, *subreddits):
    url = "https://www.reddit.com/r/"+"+".join(subreddits)
    vd.launchBrowser(url)


SubredditSheet.addCommand('^O', 'sysopen-subreddit', 'sysopen_subreddits(cursorRow.display_name)', 'open browser window with subreddit')
SubredditSheet.addCommand('g^O', 'sysopen-subreddits', 'sysopen_subreddits(*(row.display_name for row in selectedRows))', 'open browser window with messages from selected subreddits')
SubredditSheet.addCommand('g'+ENTER, 'open-subreddits', 'vd.push(openRows(selectedRows))', 'open sheet with top ~1000 submissions for each selected subreddit')
SubredditSheet.addCommand('ga', 'add-subreddits-match', 'addRowsFromQuery(input("add subreddits matching: "))', 'add subreddits matching input by name or description')
RedditSubmissions.addCommand('ga', 'add-submissions-match', 'addRowsFromQuery(input("add posts matching: "))', 'add posts in this subreddit matching input')

vd.addMenuItems('''
    File > Reddit > open selected subreddits > open-subreddits
    File > Reddit > add > matching subreddits > add-subreddits-match
    File > Reddit > add > matching submissions > add-submissions-match
    File > Reddit > open in browser > subreddit in current row > sysopen-subreddit
    File > Reddit > open in browser > selected subreddits > sysopen-subreddits
''')
