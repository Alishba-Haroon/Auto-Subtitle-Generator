# __init__.py for Flask app
from flask import Flask

def create_app():
    app = Flask(__name__)
    return app
