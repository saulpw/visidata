---
eleventyNavigation:
    key: Shell
    order: 10
update: 2022-08-16
version: VisiData v2.9
---

## How to add ZSH Completion

1. Clone the VisiData repo: `git clone https://github.com/saulpw/visidata`
2. `cd visidata`
3. Run the script that will create the list of autocompletes for visidata

~~~
dev/zsh_completion.py
~~~
4. `echo $fpath | grep site-functions` to learn where your zsh site-functions folder is located. (Possible locations `/usr/share/zsh/site-functions`, `/usr/local/share/zsh/site-functions`)
5. Move the visidata compdefs to where zsh can find them: `sudo mv _visidata /path/to/site-functions`
6. `compinit`
7. Check that the autocompletes are configured with `grep -n visidata ~/.zcompdump`
