#!/bin/bash

pip install -e .
mkdir -p .vscode
cp .devcontainer/launch.json .vscode/launch.json
cp .devcontainer/settings.json .vscode/settings.json
