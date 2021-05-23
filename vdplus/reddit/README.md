# Using the Reddit API

## Setup Reddit OAUTH credentials to use the API

1. Login to Reddit and go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps):

2. Create a "script" app.  You can use `http://localhost:8000` for the redirect uri.

3. Store credentials in visidatarc:

    options.reddit_client_id = '...'      # below the description in the upper left
    options.reddit_client_secret = '...'

## Use 'reddit' filetype for subreddits or users

    vd r/commandline.reddit
    vd u/gallowboob.reddit
    vd r/neovim -f reddit

Multiple may be specified, joined with `+`:

    vd r/rust+golang+python.reddit
    vd u/spez+kn0thing.reddit

## Commands available from Reddit Sheets

### SubredditSheet

- `Ctrl+O` (`sysopen-subreddit`): open browser window with subreddit
- `g Ctrl+O` (`sysopen-subreddits`): open browser windows with all selected subreddits
- `ENTER` (`dive-row`): open sheet with top ~1000 submissions for that subreddit
- `g ENTER` (`open-subreddits`): open sheet with top ~1000 submissions for each selected subreddit
- `ga` (`add-subreddits-match`): add subreddits matching input by name or description

### SubmissionsSheet

- `ENTER` (`dive-row`): open sheet with comments for this post
- `ga` (`add-submissions-match`): add posts in this subreddit matching input
