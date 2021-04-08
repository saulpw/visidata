#!/usr/bin/env python3

from visidata import *

subreddit_hidden_attrs='''
name accounts_active accounts_active_is_fuzzed advertiser_category
all_original_content allow_chat_post_creation allow_discovery
allow_galleries allow_images allow_polls allow_predictions
allow_predictions_tournament allow_videogifs allow_videos
banner_background_color banner_background_image banner_img banner_size
can_assign_link_flair can_assign_user_flair collapse_deleted_comments
comment_score_hide_mins community_icon community_reviewed created
created_utc description_html disable_contributor_requests
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
user_sr_theme_enabled videostream_links_count whitelist_status widgets
wiki wiki_enabled wls
'''

post_hidden_attrs='''
all_awardings allow_live_comments approved_at_utc approved_by archived
author_flair_background_color author_flair_css_class author_flair_richtext
author_flair_template_id author_flair_text author_flair_text_color
author_flair_type author_fullname author_patreon_flair author_premium
awarders banned_at_utc banned_by can_gild can_mod_post category clicked
comment_limit comment_sort content_categories contest_mode created_utc
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
treatment_tags upvote_ratio user_reports view_count visited
whitelist_status wls
'''

comment_hidden_attrs='''
all_awardings approved_at_utc approved_by archived associated_award
author_flair_background_color author_flair_css_class author_flair_richtext
author_flair_template_id author_flair_text author_flair_text_color
author_flair_type author_fullname author_patreon_flair author_premium
awarders banned_at_utc banned_by body_html can_gild can_mod_post
collapsed collapsed_because_crowd_control collapsed_reason comment_type
controversiality created_utc distinguished fullname gilded gildings
is_root is_submitter likes link_id locked mod mod_note mod_reason_by
mod_reason_title mod_reports name no_follow num_reports parent_id
permalink removal_reason report_reasons saved score score_hidden
send_replies stickied submission subreddit_id subreddit_name_prefixed
subreddit_type top_awarded_type total_awards_received treatment_tags
user_reports
'''

@VisiData.api
def open_reddit(vd, p):
    'scrape from list of subreddits'
    vd.enable_requests_cache()
    return SubredditSheet(p.name, source=p)


class SubredditSheet(Sheet):
    # source is a text list of subreddits
    rowtype = 'subreddits'  # rowdef: praw.Subreddit
    nKeys=1
    columns = [
        AttrColumn('display_name_prefixed', width=15),
        AttrColumn('active_user_count', type=int),
        AttrColumn('subscribers', type=int),
        AttrColumn('subreddit_type'),
        AttrColumn('title'),
        AttrColumn('description', width=50),
        AttrColumn('url', width=10),
    ] + [AttrColumn(x) for x in subreddit_hidden_attrs.split()]

    def iterload(self):
        import praw

        client_secret = 'LgDZWsSLVuzUYN-IioDJj9mmEYZZ4g'
        client_id = 'qhwpLTENOBt1pQ'
        user_agent = visidata.__version__

        self.reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

        if self.source.given.startswith('/'):
            yield from self.reddit.subreddits.popular(self.source.name[1:])
        else:
            yield self.reddit.subreddit(self.source.name)

    def openRow(self, row):
        return RedditSubmissions(row.display_name_prefixed, source=row)


class RedditSubmissions(Sheet):
    rowtype='reddit posts' # rowdef: praw.Submission
    nKeys=2
    columns = [
        AttrColumn('subreddit', width=0),
        AttrColumn('id', width=0),
        AttrColumn('created', width=11, type=date),
        AttrColumn('author'),
        AttrColumn('ups', width=8, type=int),
        AttrColumn('downs', width=8, type=int),
        AttrColumn('num_comments', width=8, type=int),
        AttrColumn('title', width=50),
        AttrColumn('selftext', width=60),
        AttrColumn('comments', width=0),
        AttrColumn('url', width=0),
    ] + [AttrColumn(x) for x in post_hidden_attrs.split()]

    def iterload(self):
        yield from self.source.top(limit=10000)

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
    ] + [AttrColumn(x) for x in comment_hidden_attrs   .split()]

    def iterload(self):
        yield from self.source

    def openRow(self, row):
        return RedditComments(row.id, source=row.replies)


@SubredditSheet.api
@asyncthread
def search(sheet, q):
    for r in sheet.reddit.subreddits.search(q):
        sheet.addRow(r, index=sheet.cursorRowIndex+1)

SubredditSheet.addCommand('ga', 'add-subreddits-match', 'search(input("add subreddits matching: "))')
RedditSubmissions.addCommand('ga', 'search-submissions', 'addRows(source.search(input("add posts matching: ")), index=cursorRowIndex+1)')
