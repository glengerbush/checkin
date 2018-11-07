import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # General Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lkawf&86T8YUIHI3RWEAOI3SU7Y86tg8oYTt8IGYUUYtf'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

