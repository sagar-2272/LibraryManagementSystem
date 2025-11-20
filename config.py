import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'library-management-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///library.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False