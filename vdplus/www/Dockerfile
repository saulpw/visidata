FROM alpine:3.16

RUN mkdir /app
WORKDIR /app

RUN apk update \
    && apk upgrade \
    && apk add --no-cache \
        mandoc \
        py3-apache-arrow \
        py3-greenlet \
        py3-lz4 \
        py3-numpy \
        py3-pandas \
        py3-pip \
        py3-protobuf \
        py3-psycopg2 \
        py3-pydantic \
        py3-pymysql \
        py3-regex \
        py3-toolz \
        py3-cachetools \
        py3-platformdirs \
        py3-wheel \
        procps

# RUN sed -i '/path-exclude \/usr\/share\/man/d' /etc/dpkg/dpkg.cfg.d/docker
# RUN sed -i '/path-exclude \/usr\/share\/groff/d' /etc/dpkg/dpkg.cfg.d/docker
# RUN apt-get install groff-base --reinstall

RUN apk add --no-cache go git \
    && git clone --depth 1 --branch v2.0.0-alpha.3 https://github.com/yudai/gotty g \
    && cd g \
    && go mod init \
    && go get \
    && go mod vendor \
    && go build \
    && cp ./gotty /app \
    && cd .. \
    && rm -r g \
    && pip install --no-warn-conflicts -U \
    'git+https://github.com/ibis-project/ibis.git#egg=ibis-framework[clickhouse,duckdb,postgres,mysql,sqlite]' \
    'git+https://github.com/cpcloud/ibis-bigquery.git@unconstrain-pyarrow' \
    'git+https://github.com/saulpw/visidata.git' \
    'git+https://github.com/visidata/vdsql.git' \
    && apk del go git

ENV PORT=9999
ENV TERM=xterm-256color

ENTRYPOINT exec /app/gotty -w -p "$PORT" vd "catalog://" -c /etc/vd/visidatarc
