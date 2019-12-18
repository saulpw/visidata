FROM python:3.8.0-slim-buster

ADD . /app
WORKDIR /app

RUN apt-get update
RUN apt-get install -y curl build-essential

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
RUN . $HOME/.poetry/env && poetry install

RUN apt-get install -y nodejs
RUN curl -o- -L https://yarnpkg.com/install.sh | bash
RUN cd spa && $HOME/.yarn/bin/yarn install
RUN cd spa && ./node_modules/.bin/webpack --build

RUN apt-get remove --purge -y build-essential
RUN apt autoremove -y

CMD ["/app/run.sh"]

