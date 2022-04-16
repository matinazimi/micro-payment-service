from mongoengine import *
import mongoengine_goodjson as gj


class Example(gj.Document):
    userId = IntField(required=True)
    scopes = ListField(StringField())
