# Using VisiData with [Zulip](https://github.com/zulip/zulip) chat (read-only)

## Setup

Get an [API key for Zulip](https://zulip.com/api/api-keys) and add import and options to .visidatarc:

    import vdplus.api.zulip
    options.zulip_api_key='...'
    options.zulip_email='you@example.com'

Install the Python module for zulip:

    pip3 install zulip

## Usage

Launch `vd` with the appropriate site url and the `zulip` filetype:

    vd -f zulip https://recurse.zulipchat.com

## Commands

The opening sheet shows the user's subscribed streams.

- Press `Enter` to open a sheet with the messages in the particular stream.

## Messages Sheet

- Loads continuously starting with most recent until all messages have been read.
- `Ctrl+C` to cancel loading.
- `Enter` to open message in word-wrapped text sheet

### toplevel commands

- `open-zulip-members`: push list of all members
   - `Enter` to open list of messages from that member
- `open-zulip-streams`/`open-zulip-subs`: push list of all/subscribed streams
   - `Enter` to open list of recent messages from that stream
   - `z Enter` to open list of topics
- `open-zulip-msgs`: push list of all messages
- `open-zulip-profile`: push user profile

# Example

- `Enter` to open up a stream
- `+min max` on `timestamp` column to add aggregators for the freq table
- `Shift+F` on `subject` column to get a list of topics
- `=timestamp_max-timestamp_min` to add a column with the timedelta between the earliest message and the latest message on the topic.
- `]` to sort descending to find the conversation that has spanned the longest stretch of time
