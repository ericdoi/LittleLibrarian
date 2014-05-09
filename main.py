from flask import Flask
import config as cfg
import os
import pdb

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE = os.path.join(app.root_path, cfg.dbPath),
    DEBUG = True,
    SECRET_KEY = 'dev key',
    USERNAME = 'admin',
    PASSWORD = 'default'
))

from pages import *

if __name__ == '__main__':
    app.run(debug=True)
        
