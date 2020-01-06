FROM python:3.8.0-slim-buster

ENV TERM=xterm-256color

WORKDIR /app

RUN apt-get update && apt-get install -y curl libgeos-dev git man procps parallel

RUN mkdir -p /app/data /app/bin /app/src
ARG VD_SRC=/app/src/visidata

# Install VisiData
RUN git clone --depth 1 --branch develop https://github.com/saulpw/visidata.git $VD_SRC
RUN pip3 install $VD_SRC
ADD requirements.txt $VD_SRC
RUN pip install -r $VD_SRC/requirements.txt
ADD visidatarc /root/.visidatarc

# Install GoTTY to expose STDIN/STDOUT over a websocket
RUN cd /app/bin && curl -L https://github.com/yudai/gotty/releases/download/v2.0.0-alpha.3/gotty_2.0.0-alpha.3_linux_amd64.tar.gz | tar -xvzf -

# Install s3cmd to sync user account filesystems
RUN pip3 install s3cmd
ADD s3cfg /app/.s3cfg
ADD account-fs-sync.sh /app/bin

RUN apt-get -y install tmux
ADD tmux.conf /app/.tmux.conf

RUN useradd -m -d /app vd
ADD vd.sh /app/bin

RUN mkdir /app/log

ADD run.sh /app/bin
CMD /app/bin/run.sh
