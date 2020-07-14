import os

class Config(object):
    IEXAPI_KEY = os.environ.get('IEXAPI_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
