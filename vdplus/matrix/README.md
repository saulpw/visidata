# Using Matrix chat with VisiData

## Setup

Add this to .visidatarc:

    import vdplus.matrix
    options.matrix_user_id = '@handle:matrix.org'  # replace with your handle/homeserver

Then run:

    vd matrix+https://matrix.org

The first time, it asks for username and password, which should be entered as on the website.
It appends a line to the .visidatarc with the token it receives, so subsequent usages don't require login.

## Commands

- `a` to add (send) a message to the channel of the message the cursor is on.
- `Enter` to push a sheet with all the messages from that channel.


# Links and references

- [Matrix Recorder](https://gitlab.com/argit/matrix-recorder/): Node.js, last updated in 2018
