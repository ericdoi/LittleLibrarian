from flask import render_template, session, redirect, url_for, escape, request, flash
from main import app
from utilFunctions import *

##### Page Routes ####

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('bookList'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['Username']
        password = request.form['Password']
    
        if checkUserExists(username):
            if checkPassword(username, password):
                session['username'] = username
                session['logged_in'] = True
                flash('You were logged in')
                return redirect(url_for('index'))
            else:
                flash('Incorrect password.')
        else:
            flash('User does not exist. Try again or reset password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/passwordreset', methods=['GET','POST'])
def passwordReset():
    """Display reset password page. If the account doesn't exist, create it."""
    if request.method == 'POST':
        username = request.form['Email']
        if checkUserExists(username):
            doResetPassword(username)
        else:
            createNewUser(username, None, None, username)
        return redirect(url_for('login'))
    return render_template('password_reset.html')

@app.route('/booklist', methods=['GET','POST'])
def bookList():
    """Display all books and allow checkout/return etc."""
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

@app.route('/mybooks', methods=['GET','POST'])
def myBooks():
    """Display and return books currently checked out by the user."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'return' in request.form:
            doBookReturn(request.form['return'])
    
    myBooksQuery = 'SELECT id, title, authorFName, authorLName FROM books WHERE heldBy = ?'
    result = query_db(myBooksQuery, (session['username'],))
    return render_template('my_books.html', books=result)
