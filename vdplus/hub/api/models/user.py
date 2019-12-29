import secrets
import os
import requests
import logging

import peewee as pw
from database import db

MAILGUN_DOMAIN = 'mg.tombh.co.uk'

class BaseModel(pw.Model):
    """A base model that will use our Postgresql database"""
    class Meta:
        database = db

class User(BaseModel):
    email = pw.CharField(unique=True)
    token = pw.CharField()

    @staticmethod
    def auth(request, email):
        user = User.select().where(User.email == email)

        if user.exists():
            user = user.get()
        else:
            user = User.create(email=email)

        token = user.generate_token()
        magic_link = User.magic_link(request, token)
        User.send_magic_link_email(email, magic_link)
        return magic_link

    @staticmethod
    def magic_link(request, token):
        return request.scheme + '://' + request.host + '/magic/' + token

    @staticmethod
    def send_magic_link_email(email, magic_link):
        if os.getenv("VD_ENV") == "dev" or os.getenv("CI") == "true":
            return
        logging.debug("Sending Mailgun email to " + email)
        response = requests.post(
            "https://api.mailgun.net/v3/" + MAILGUN_DOMAIN + "/messages",
            auth=("api", os.getenv("MAILGUN_API_KEY")),
            data={"from": "VisiData <noreply@visidata.org>",
                  "to": [email, email],
                  "subject": "Hello",
                  "text": magic_link})
        logging.debug(response)

    def generate_token(self):
        self.token = secrets.token_urlsafe()
        self.save()
        return self.token

