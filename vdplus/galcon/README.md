# Galactic Conquest in VisiData

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

    ./galcon-server.py [-p <port>]

This will output a URL for players to connect to.  All players then start their clients and login:

    vd -f galcon http://your.ip.address:8080

Of course, the given port on `your.ip.address` must be open to all players.

The first time a player name is used, the password is set.
Players join the game if it has not yet started (each server only hosts one game).

Each player presses `Ctrl+S` when they are ready for the game to start.

Press `Alt+M` to go to the Map for this game, or `Alt+P` for the list of planets.
Before the game has started, any player can change `Alt+G`ame options or press `Alt+N` to generate a New map.
`Ctrl+R` will reload the current sheet from data on the server.

When the map and all players are ready, the game begins.

### Playing the game

From any sheet:

- `Alt+M` opens the planet map
- `Alt+P` opens the planet sheet
- `Alt+U` opens the queued deployments sheet (not yet sent to server)
- `Alt+D` opens the full deployments sheet
- `Alt+E` opens the events sheet
- `Alt+Q` allows players to quit the game
- `Ctrl+S` submits the pending deployments to the server and signals the player is done

On the Planets sheet:

- `m` to mark the destination planet for a player's ships
- `f` to indicate the source planet
    - The player is then prompted to specify how many ships they wish to deploy from the source planet to the marked planet
- `gf` to send the provided number of ships from all selected planets to the marked planet

On the Map sheet:

- The colour of the planet indicates which player currently 'owns' it
- White planets are neutral and currently not in anybody's control
- `v` to cycle through `name`, `prod`, `killpct` and `numships` fields
- `m` and `f` to mark and deploy on the map sheet, same as on the Planets sheet

On the Queued Orders sheet:

- `e` to modify an order
- `d` to delete an order

### Using the Dockerfiles

Create an ssh deploy key that has permissions for vdplus. Here, it is called `bluebird_docker`

```
# build the image for the galcon server
sudo docker build --build-arg SSH_PRIVATE_KEY="$(cat bluebird_docker)" -t galcon-server -f Dockerfile.galcon-server .
# run the galcon server
sudo docker run -d -p 7777:8080 --rm galcon-server

# get ip address of where galcon server is running
sudo docker inspect GALCON_SERVER_CONTAINER_NUMBER | jq '.[0].NetworkSettings.IPAddress'

# build the image for the client
sudo docker build --build-arg SSH_PRIVATE_KEY="$(cat bluebird_docker)" -t galcon-client -f Dockerfile.galcon-client .

# for each person that is playing, run the docker client
sudo docker run -e IPADDR="GALCON_SERVER_IP_ADDRESS" -it --rm galcon-client
```
