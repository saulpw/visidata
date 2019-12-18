# The Hub

The app that sits in front of all the individual VisiData container. But sits
behind the main cluster's load balancer. The Hub accepts HTTP requests and
authenticates users against a DB. It can talk to the Kubernetes API and spin
up individual containers, it can then forward websockets into that container.

The main reason for this app is so that only one `vd` process runs in each
container, thus providing isolation, security and predictable k8s scaling.

## Installation
You will need https://python-poetry.org and https://yarnpkg.com Both are very
likely available through your OS's package manager.

In the `hub/` path `poetry install`
In the `hub/js` path `yarn install`

