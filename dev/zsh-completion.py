#!/usr/bin/env python
from __future__ import unicode_literals

import os
from os.path import dirname as dirn
import sys
import re

sys.path.insert(0, dirn(dirn((os.path.abspath(__file__)))))
from visidata import vd
from visidata.main import option_aliases

ZSH_COMPLETION_FILE = "_visidata"
ZSH_COMPLETION_TEMPLATE = "dev/zsh-completion.in"
pat_class = re.compile("'(.*)'")
pat_select = re.compile("^\([^)]*\)")


def generate_completion(opt):
    prefix = "--" + opt.name
    shortnames = [key for key, value in option_aliases.items() if value[0] == opt.name]
    if len(shortnames):
        if len(shortnames[0]) == 1:
            shortname = "-" + shortnames[0]
        else:
            shortname = "--" + shortnames[0]
        prefix = "{" + f"{shortname},{prefix}" + "}"
    if isinstance(opt.value, bool):
        completion = ""
    else:
        completion = ":" + pat_class.findall(str(opt.value.__class__))[0]
    if opt.name in ["play", "output", "visidata_dir", "config"]:
        completion += ":_files"
    elif opt.name in ["plugins_url", "motd_url"]:
        completion += ":_urls"
    helpstr = opt.helpstr.replace("[", "\\[").replace("]", "\\]")
    selections = pat_select.findall(helpstr)
    if len(selections):
        completion += f":{selections[0].replace('/', ' ')}"
    # TODO: use `zstyle ':completion:*' extra-verbose true`
    # to control the display of default value
    helpstr = helpstr + f" (default: {opt.value})"
    return f"{prefix}'[{helpstr}]{completion}'"


flags = [generate_completion(vd._options[opt]["default"]) for opt in vd._options]

with open(ZSH_COMPLETION_TEMPLATE) as f:
    template = f.read()

template = template.replace("{{flags}}", " \\\n    ".join(flags))

with open(ZSH_COMPLETION_FILE, "w") as f:
    f.write(template)
