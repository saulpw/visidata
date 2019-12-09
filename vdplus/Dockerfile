FROM python:3.8.0-slim-buster

RUN mkdir /app
WORKDIR /app

RUN pip install visidata

RUN apt-get update && apt-get install -y curl
RUN curl -L https://github.com/yudai/gotty/releases/download/v2.0.0-alpha.3/gotty_2.0.0-alpha.3_linux_amd64.tar.gz | tar -xvzf -

RUN curl -LO https://jsvine.github.io/intro-to-visidata/_downloads/83e70cf67e909f3ac177575439e5f3c5/faa-wildlife-strikes.csv

ENV TERM=xterm-256color

CMD /app/gotty -w -p 9000 vd
