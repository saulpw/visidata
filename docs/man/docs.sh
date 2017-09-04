./parse_options.py
groff -mandoc -Thtml vdtui.1 > vdtui-man.html
./parse_options.py vd
groff -mandoc -Thtml vd.1 > vd-man.html
