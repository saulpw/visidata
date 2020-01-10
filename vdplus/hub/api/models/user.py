import secrets
import os
import requests
import logging
import datetime

import peewee as pw
from database import db

GUEST = 'guest'
MAILGUN_DOMAIN = 'mg.tombh.co.uk'
DEFAULT_IDLE_TIMEOUT_GUEST = 5 * 60
DEFAULT_IDLE_TIMEOUT_ACCOUNT = 100 * 60

class BaseModel(pw.Model):
    """A base model that will use our Postgresql database"""
    class Meta:
        database = db

# Note about some of the `null=True` args: the auto migration tool seemed to need them
# when also using `default=...`
class User(BaseModel):
    created = pw.DateTimeField(null=True, default=datetime.datetime.now)
    modified = pw.DateTimeField(null=True, default=datetime.datetime.now)
    email = pw.CharField(unique=True)
    token = pw.CharField()
    current_pod_ip = pw.CharField(null=True)
    current_pod_name = pw.CharField(null=True)
    last_input = pw.DateTimeField(null=True)
    idle_timeout = pw.IntegerField(default=DEFAULT_IDLE_TIMEOUT_GUEST)

    # TODO: regularly delete guest records older than the longest a guest could
    # reasonably keep a session open for.
    is_guest = pw.BooleanField(null=True, default=False)

    def save(self, *args, **kwargs):
        self.modified = datetime.datetime.now()
        return super(User, self).save(*args, **kwargs)

    @staticmethod
    def auth(request, email):
        user = User.get_user(email)
        if email == GUEST:
            token = user.token
        else:
            magic_link = User.magic_link(request, user.token)
            User.send_magic_link_email(email, magic_link)
            token = magic_link
        return token

    @staticmethod
    def get_user(email):
        if email != GUEST:
            user = User.select().where(User.email == email)
            if user.exists():
                return user.get()
        return User.new_user(email)

    @staticmethod
    def new_user(email):
        if email == GUEST:
            user = User.create(email=secrets.token_urlsafe(32), is_guest=True)
        else:
            user = User.create(email=email, idle_timeout=DEFAULT_IDLE_TIMEOUT_ACCOUNT)
        user.generate_token()
        return user

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
            data={"from": "VisiData <noreply@mg.visidata.org>",
                  "to": [email, email],
                  "subject": "Hello",
                  "text": magic_link})
        logging.debug(response)

    def generate_token(self):
        self.token = secrets.token_urlsafe()
        self.save()
        return self.token

