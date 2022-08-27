FROM python:3.10.6-slim-bullseye

RUN mkdir /app
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    postgresql-client \
    libpq-dev \
    man

RUN sed -i '/path-exclude \/usr\/share\/man/d' /etc/dpkg/dpkg.cfg.d/docker
RUN sed -i '/path-exclude \/usr\/share\/groff/d' /etc/dpkg/dpkg.cfg.d/docker
RUN apt-get install groff-base --reinstall

RUN pip install -U \
    'git+https://github.com/ibis-project/ibis.git#egg=ibis-framework[clickhouse,duckdb,postgres,mysql,sqlite]' \
    'protobuf==3.20.1' \
    'git+https://github.com/ibis-project/ibis-bigquery.git' \
    'git+https://github.com/saulpw/visidata.git' \
    'git+https://github.com/visidata/vdsql.git'

RUN curl -L https://github.com/yudai/gotty/releases/download/v2.0.0-alpha.3/gotty_2.0.0-alpha.3_linux_amd64.tar.gz | tar -xvzf -

ENV PORT=9999
ENV TERM=xterm-256color

ENTRYPOINT exec /app/gotty -w -p "$PORT" vd "catalog://" -c /etc/vd/visidatarc
