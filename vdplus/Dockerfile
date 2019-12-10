FROM python:3.8.0-slim-buster

ENV TERM=xterm-256color

RUN mkdir -p /app/data
RUN mkdir -p /app/bin
WORKDIR /app/data

RUN pip install visidata

# Install GoTTY to expose STDIN/STDOUT over a websocket
RUN apt-get update && apt-get install -y curl wget
RUN cd /app/bin && curl -L https://github.com/yudai/gotty/releases/download/v2.0.0-alpha.3/gotty_2.0.0-alpha.3_linux_amd64.tar.gz | tar -xvzf -

# Download sample data
RUN cd /app/data && \
  curl -LO https://jsvine.github.io/intro-to-visidata/_downloads/83e70cf67e909f3ac177575439e5f3c5/faa-wildlife-strikes.csv && \
  wget --no-parent -A'*.csv' -nd -r https://people.sc.fsu.edu/~jburkardt/data/csv/

RUN rm /app/data/robots.txt.tmp

CMD /app/bin/gotty -w -p 9000 vd /app/data
