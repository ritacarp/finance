import os

class Config(object):
    IEXAPI_KEY = os.environ.get('IEXAPI_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    POSTGRESQL_HOST = os.environ.get('POSTGRESQL_HOST')
    POSTGRESQL_DATABASE = os.environ.get('POSTGRESQL_DATABASE')
    POSTGRESQL_USERNAME = os.environ.get('POSTGRESQL_USERNAME')
    POSTGRESQL_PASSWORD = os.environ.get('POSTGRESQL_PASSWORD')
    POSTGRESQL_PORT = os.environ.get('POSTGRESQL_PORT')