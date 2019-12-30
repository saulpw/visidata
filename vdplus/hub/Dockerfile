FROM python:3.8.0-slim-buster

RUN apt-get update
RUN apt-get install -y curl libpq-dev build-essential

ADD . /app
WORKDIR /app
ENV VD_ENV=production

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
RUN cd api && . $HOME/.poetry/env && poetry install

RUN apt-get install -y nodejs
RUN curl -o- -L https://yarnpkg.com/install.sh | bash
RUN cd spa && $HOME/.yarn/bin/yarn install
RUN cd spa && ./node_modules/.bin/webpack --optimize-minimize --build

RUN apt-get remove --purge -y build-essential
RUN apt autoremove -y && rm -rf /var/lib/apt/lists/*

CMD ["/app/run.sh"]

