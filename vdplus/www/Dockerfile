FROM alpine:3.16

RUN mkdir /app
WORKDIR /app

RUN mkdir -p /etc/vd \
    && apk update \
    && apk upgrade \
    && apk add --no-cache \
        mandoc \
        nano \
        neovim \
        build-base \
        py3-apache-arrow \
        py3-cachetools \
        py3-greenlet \
        py3-lxml \
        py3-lz4 \
        py3-numpy \
        py3-pandas \
        py3-pip \
        py3-platformdirs \
        py3-protobuf \
        py3-psycopg2 \
        py3-pydantic \
        py3-pymysql \
        py3-regex \
        py3-requests \
        py3-toolz \
        py3-wheel \
        procps \
        go \
        git \
    && git config --global advice.detachedHead false \
    && git clone --depth 1 --branch v2.0.0-alpha.3 https://github.com/yudai/gotty /tmp/gotty \
    && cd /tmp/gotty \
    && go mod init && go get && go mod vendor && go build \
    && strip ./gotty \
    && cp ./gotty /app \
    && rm -r /tmp/gotty /root/go \
    && cd /app \
    && pip install --no-cache-dir -U \
    'git+https://github.com/cpcloud/ibis.git#egg=ibis-framework[clickhouse,duckdb,postgres,mysql,sqlite]' \
    'git+https://github.com/cpcloud/ibis-bigquery.git@unconstrain-pyarrow' \
    'git+https://github.com/saulpw/visidata.git' \
    'git+https://github.com/visidata/vdsql.git' \
    && apk del go git build-base

ENV PORT=9500

ENV TERM=xterm-256color
ENV EDITOR=nvim

COPY ./visidatarc /etc/vd/visidatarc

ENTRYPOINT exec /app/gotty -w -p "$PORT" vd "catalog://" -c /etc/vd/visidatarc
