FROM python:3.8-alpine

RUN pip install requests python-dateutil wcwidth

RUN mkdir -p /opt/visidata
WORKDIR /opt/visidata
COPY . ./
RUN sh -c 'yes | pip install -vvv .'

ENV TERM="xterm-256color"
ENTRYPOINT bin/vd
