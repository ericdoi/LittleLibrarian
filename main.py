from flask import Flask, g, render_template, session, redirect, url_for, escape, request, flash
import sqlite3
import config as cfg
import queries
import os

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE = os.path.join(app.root_path, cfg.dbPath),
    DEBUG = True,
    SECRET_KEY = 'dev key',
    USERNAME = 'admin',
    PASSWORD = 'default'
))

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
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('bookList'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['Username']
        session['logged_in'] = True
        flash('You were logged in')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('logged_in', None)
    return redirect(url_for('index'))

def doBookCheckout(username, bookId):
    checkoutQuery = 'UPDATE books SET heldBy = ? WHERE id = ?'
    query_db(checkoutQuery, (username, bookId))
    flash('You got it! (Book #%s)'%(bookId))
    get_db().commit()

def doBookRequest(username, bookId):
    flash('Todo: send an email to request it! (Book #%s)'%(bookId))

def doBookReturn(bookId):
    returnQuery = 'UPDATE books SET heldBy = NULL WHERE id = ?'
    query_db(returnQuery, (bookId,))
    flash('Returned! (Book #%s) Please leave the book in the library.'%(bookId))
    get_db().commit()

# Display all books and allow checkout, request, or return
@app.route('/booklist', methods=['GET','POST'])
def bookList():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'checkout' in request.form:
            doBookCheckout(session['username'], request.form['checkout'])
        elif 'request' in request.form:
            doBookRequest(session['username'], request.form['request'])
        elif 'return' in request.form:
            doBookReturn(request.form['return'])
    allListQuery = 'SELECT id, title, authorFName, authorLName, heldBy FROM books'
    result = query_db(allListQuery)
    return render_template('book_list.html', books=result)


# Display and return books currently checked out
@app.route('/mybooks', methods=['GET','POST'])
def myBooks():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'return' in request.form:
            doBookReturn(request.form['return'])
    
    myBooksQuery = 'SELECT id, title, authorFName, authorLName FROM books WHERE heldBy = ?'
    result = query_db(myBooksQuery, (session['username'],))
    return render_template('my_books.html', books=result)

if __name__ == '__main__':
    app.run(debug=True)
        
