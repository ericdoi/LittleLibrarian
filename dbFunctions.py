from flask import g
from main import app
import sqlite3

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database again at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    """DB query helper function."""
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows

def insert_db(query, values=()):
    """DB insert and commit helper function."""
    cur = get_db().cursor()
    cur.execute(query, values)
    get_db().commit()
    id = cur.lastrowid
    cur.close()
    return id

