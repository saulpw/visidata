# The Hub

The app that sits in front of all the individual VisiData container. But sits
behind the main cluster's load balancer. The Hub accepts HTTP requests and
authenticates users against a DB. It can talk to the Kubernetes API and spin
up individual containers, it can then forward websockets into those created containers.

The main reason for this app is to isolate all managerial tasks into a central place so
that `vd` processes themselves can run in individual containers, thus providing isolation, security and predictable k8s scaling.

## Installation
You will need https://python-poetry.org and https://yarnpkg.com Both are very
likely available through your OS's package manager.

In the `hub/` path `poetry install`    
In the `hub/js` path `yarn install`    

## Developing

### Python API server
The API server is written using the aiohttp async framework. It is a webserver geared specifically towards handling async processes such as those required to support websockets. To run the  API server there is a convenience tool called `adev` (automatically installed with the `poetry install` command above). It does many things, but most importantly it watches for file changes and reloads the server when necessary.

In the `hub/` path run `poetry run adev runserver app.py`

### GoTTY service (optional)
If you need to hack on interaction with in-browser `vd` instances you will also need a running `gotty` service. Installation instructions are [here](https://github.com/yudai/gotty#installation). Then you can run `gotty -p 8181 --ws-origin '.*' -w vd`.

### Frontend
To develop the site's HTML/JS/CSS etc you will need to use `webpack-dev-server`, which will have already been installed with `yarn install` above. It automatically builds and reloads the site when you make changes. In fact it "hot reloads" without even refreshing the browser page. This can sometimes cause oddities when hacking complex JS, so occasionally a normal browser refresh is useful.

It can be run with `webpack-dev-server` or `node_modules/.bin/webpack-dev-server`, depending on your `yarn` installation.
