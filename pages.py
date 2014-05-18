from flask import render_template, session, redirect, url_for, escape, request, flash
from main import app
from utilFunctions import *

##### Page Routes ####

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

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
        elif 'missing' in request.form:
            doBookMissingReport(session['username'], request.form['missing'])
        elif 'claim' in request.form:
            doBookClaim(session['username'], request.form['claim'])
        elif 'return' in request.form:
            doBookReturn(request.form['return'])
        elif 'request' in request.form:
            doBookRequest(session['username'], request.form['request'])
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
    
    myBooksQuery = """SELECT bk.*
                      , julianday(date("now")) -
                        julianday(dateOut) as numDays
                      FROM books bk
                      INNER JOIN checkouts co ON (checkoutId = co.id)
                      WHERE heldBy = ?"""
    result = query_db(myBooksQuery, (session['username'],))
    return render_template('my_books.html', books=result)

@app.route('/missingbooks', methods=['GET','POST'])
def missingBooks():
    """Display and claim books that have been reported as missing."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'claim' in request.form:
            doBookClaim(session['username'], request.form['claim'])
    
    missingBooksQuery = """SELECT bk.*
                           , reportedMissingBy
                           FROM books bk
                           INNER JOIN checkouts co ON (checkoutId = co.id)
                           WHERE heldBy = ?"""
    result = query_db(missingBooksQuery, ("MISSING",))
    return render_template('missing_books.html', books=result)

