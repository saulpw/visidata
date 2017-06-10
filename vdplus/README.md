# wsinvaders
Whitespace Invaders: Galactic Conquest ported to VisiData

## Instructions

### Starting a game

The host has to start a server:

    $ ./wsi-server.py

All players then start their clients and login:

    $ ./wsi-client.py http://localhost:8080

(or whatever url works to access the server)

The first time a player name is used, the password is set.
Players join the game if it has not yet started (each server only hosts one game).

Each player presses `ENTER` when they are ready for the game to start.

Press `M` to go to the Map for this game, or `P` for the list of planets.
Any player can press `N` to generate a New map (`Ctrl-R` to Reload the pages).

When the map is all players are ready, the game begins.

### Playing the game

From any sheet:

- `M` opens the planet map
- `P` opens the planet sheet
- `Q` opens the queued deployments sheet (not yet sent to server)
- `D` opens the full deployments sheet
- `E` opens the events sheet
- `Ctrl-S` submits the pending deployments to the server and signals the player is done

On the `P`lanet sheet:
- `m` marks the destination planet
- `f` marks the source planet
- Once both source and destination planet are selected, the player is prompted to input how many ships they wish to deploy and then press `ENTER`

On the `M`ap sheet:
- The colour of the planet name indicates which player currently 'owns' it
- White planets are neutral and currently not in anybody's control
- `SPACE` cycles through `name`, `prod` and `killpct` fields
- `You may also mark and deploy on the map sheet, like your would on the `P`lanet sheet

On the `Q` queued orders sheet:
- `e` to modify an order
- `d` to delete an order

When all players have submitted their moves, the turn is over.  Ships arrive, battles are resolved, and planets produce.  Then the next turn begins.
