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
        procps \
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
        go \
        git \
    && git config --global advice.detachedHead false \
    && git clone --depth 1 --branch v2.0.0-alpha.3 https://github.com/yudai/gotty /tmp/gotty \
    && cd /tmp/gotty \
    && go mod init && go get && go mod vendor && go build \
    && cp ./gotty /app \
    && cd /app \
    && rm -r /tmp/gotty /root/go \
    && pip install --no-cache-dir -U \
    'git+https://github.com/ibis-project/ibis.git@adb620e559dc0892959f58c44923d19461ec2e5b#egg=ibis-framework[clickhouse,duckdb,postgres,mysql,sqlite]' \
    'git+https://github.com/cpcloud/ibis-bigquery.git@unconstrain-pyarrow' \
    'git+https://github.com/saulpw/visidata.git@3ffb5ea4c002bee1dc57f612209507f5d8a53a87' \
    'git+https://github.com/cpcloud/vdsql.git@ea3e789a9a21171decff6c7af9940297899445c1' \
    && apk del go git

COPY ./visidatarc /etc/vd/visidatarc

ENV PORT=9500
ENV TERM=xterm-256color
ENV EDITOR=nvim

ENTRYPOINT exec /app/gotty -w -p "$PORT" vd "catalog://" -c /etc/vd/visidatarc
