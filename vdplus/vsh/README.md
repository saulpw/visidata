# vsh

## latest version: v0.2-dev

vsh is a compilation of [VisiData packages](https://visidata.org) that contain interactive terminal user interfaces for classic unix tools.

Includes:
- vls
    - Navigate the filesystem
    - Delete and bulk rename files using classic VisiData commands
    - Press `Enter` on data sources to load them in vd
- vping
    - use like regular `ping`
    - resulting output will be dynamically loaded into a vd TUI
- vtop
    - use like regular `top`
    - resulting output will be dynamically loaded into a vd TUI
    - explore and perform analyses with classic vd commands

## Installing vsh

vsh is located as a module within the [VisiData repo](https://github.com/saulpw/visidata/vsh). It has its own setup.py. Note that installing vsh will also install VisiData.

```
pip3 install -e "git+https://github.com/saulpw/visidata.git@develop#egg=vsh&subdirectory=vsh"
```

### Dependencies
- Python 3.6+
- [VisiData](https://visidata.org/)
- [sh](https://github.com/saulpw/sh)
- mutagen
- psutil

## Running vsh

`vls [<working_dir>]` opens a dir sheet for the directory.

`vping [<domain_name> | <ip_address>]` opens up a sheet with the round-trip time for each ping.

`vtop` opens up a top sheet with information on the current running processes.

## License
All tools that comprise vsh are released under a GPLv3 license.
