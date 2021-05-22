# vdgalcon

Galactic Conquest on VisiData

Take over the galaxy with your warship fleet!
Starting with only one planet and 10 ships, you compete with any number of enemies for the most planets and thus galactic glory.

At first, most planets are inhabited by savages with only a few spaceships for battle.
Some planets have better pilots, and ships from those planets have a higher kill rate in battle.

To capture a planet, you need to send a strong enough fleet.  Deploy ships from your planets and conquer the galaxy!

Galactic Conquest (or "galcon" as it is sometimes called) is turn-based.
When all players have submitted their moves, the turn is over.
Ships arrive, battles are resolved, and planets produce more ships.
Then the next turn begins.

## Instructions

### Starting a game

The host has to start a server:

    $ ./vdgalcon-server.py [-p <port>]

All players then start their clients and login:

    $ ./vdgalcon.py http://localhost:8080

(or whatever URL the server prints on startup)

The first time a player name is used, the password is set.
Players join the game if it has not yet started (each server only hosts one game).

Each player presses `Ctrl+S` when they are ready for the game to start.

Press `Alt+m` to go to the Map for this game, or `Alt+p` for the list of planets.
Before the game has started, any player can change `Alt+g`ame options or press `Alt+n` to generate a New map.
`Ctrl+R` will reload the current sheet from data on the server).

When the map and all players are ready, the game begins.

### Playing the game

From any sheet:

- `Alt+m` opens the planet map
- `Alt+p` opens the planet sheet
- `Alt+u` opens the queued deployments sheet (not yet sent to server)
- `Alt+d` opens the full deployments sheet
- `Alt+e` opens the events sheet
- `Alt+q` allows players to quit the game
- `Ctrl+S` submits the pending deployments to the server and signals the player is done

On the Planets sheet:
- `m` marks the destination planet for a player's ships
- `f` indicates the source planet
- The player is then prompted to specify how many ships they wish to deploy from the source planet to the marked planet
- `gf` sends the provided number of ships from all selected planets to the marked planet

On the Map sheet:
- The colour of the planet name indicates which player currently 'owns' it
- White planets are neutral and currently not in anybody's control
- `SPACE` cycles through `name`, `prod`, `killpct` and `numships` fields
- You may also mark and deploy on the map sheet, like you would on the `P`lanet sheet

On the Queued Orders sheet:
- `e` to modify an order
- `d` to delete an order

vdgalcon is a VisiData app. [VisiData commands](https://visidata.org/docs) such as column sorting and searching are also available.
