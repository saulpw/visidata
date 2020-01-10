# The Hub

The app that sits in front of all the individual VisiData containers. But sits
behind the main cluster's load balancer. The Hub accepts HTTP requests and
authenticates users against a DB. It can talk to the Kubernetes API and spin
up individual containers, it can then forward websockets into those created containers.

The main reason for this app is to isolate all managerial tasks into a central place so
that `vd` processes themselves can run in individual containers, thus providing isolation, security and predictable k8s scaling.

## Installation
You will need https://python-poetry.org and https://yarnpkg.com Both are very
likely available through your OS's package manager.

In the `hub/api` path `poetry install`    
In the `hub/spa` path `yarn install`    

## Developing

### Python API server
The API server is written using the [aiohttp](https://github.com/aio-libs/aiohttp) async framework. It is a webserver geared specifically towards handling async processes such as those required to support websockets. To run the  API server there is a convenience tool called `adev` (automatically installed with the `poetry install` command above). It does many things, but most importantly it watches for file changes and reloads the server when necessary.

First copy the `.env.sample` to `.env` and add the secrets you'll need (you might not need
them all depending on what you're developing).

Then setup the Postgres database: `createdb vdwww`. And run the migrations:
`poetry run pw_migrate migrate`. If you are modifying the database you can auto generate
migrations with: `poetry run pw_migrate create some_descriptive_name --auto --auto-source models`

In the `hub/api` path run `poetry run adev runserver app`

### GoTTY service (optional)
If you need to hack on interaction with in-browser `vd` instances you will also need a running `gotty` service. Installation instructions are [here](https://github.com/yudai/gotty#installation). Then you can run `gotty -p 9000 --ws-origin '.*' -w vd`.

### Frontend
The frontend is a Single Page Application (SPA) using https://mithril.js.org/

To develop the site's HTML/JS/CSS etc you will need to use `webpack-dev-server`, which will have already been installed with `yarn install` above. It automatically builds and reloads the site when you make changes. In fact for CSS/SCSS it "hot reloads" without even refreshing the browser page. This can sometimes cause oddities when hacking complex styles, so occasionally a normal browser refresh is useful.

It can be run with `webpack-dev-server` or `node_modules/.bin/webpack-dev-server`, depending on your `yarn` installation.

## Running tests
Currently there are only end-to-end integration tests. These are run inside a real browser against the fully-functioning site using [TestCafe](https://devexpress.github.io/testcafe/). To run them locally you will need to have the frontend SPA, API server and GoTTY service running. In the `hub/` path run something like: `VD_PORT=8080 spa/node_modules/.bin/testcafe firefox:headless test/integration`, where `VD_PORT` is the port for `webpack-dev-server` and the `firefox` or `chrome` is the name of your preferred browser. You can also remove the `:headless` to watch the tests being run in realtime.
