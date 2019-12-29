import secrets

import peewee as pw
from database import db

class BaseModel(pw.Model):
    """A base model that will use our Postgresql database"""
    class Meta:
        database = db

class User(BaseModel):
    email = pw.CharField(unique=True)
    token = pw.CharField()

    @staticmethod
    def auth(host, email):
        user = User.select().where(User.email == email)

        if user.exists():
            user = user.get()
        else:
            user = User.create(email=email)
        return User.magic_link(host, user.generate_token())

    @staticmethod
    def magic_link(request, token):
        return request.scheme + '://' + request.host + '/magic/' + token

    def generate_token(self):
        self.token = secrets.token_urlsafe()
        self.save()
        return self.token

