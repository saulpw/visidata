FROM visidata

RUN apk add git
RUN pip install git+https://github.com/devottys/darkdraw.git@master
RUN sh -c "echo >>~/.visidatarc import darkdraw"

ENV TERM="xterm-256color"
ENTRYPOINT ["/opt/visidata/bin/vd", "-f", "ddw"]
