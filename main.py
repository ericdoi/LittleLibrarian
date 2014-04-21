from flask import Flask, g, render_template, session, redirect, url_for, escape, request, flash
import sqlite3
import config as cfg
import os
import hashlib
import string, random
import smtplib
from email.mime.text import MIMEText
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

def after_this_request(func):
    if not hasattr(g, 'call_after_request'):
        g.call_after_request = []
    g.call_after_request.append(func)
    return func

@app.after_request
def per_request_callbacks(response):
    for func in getattr(g, 'call_after_request', ()):
        response = func(response)
    return response

def sendMail(toEmails, ccEmails, bccEmails, subject, message):
 #   try:
    if cfg.emailPwd is not None:
        s = smtplib.SMTP_SSL(cfg.emailHost, 465)
        s.login(cfg.emailSender, cfg.emailPwd)
    else:
        s = smtplib.SMTP(cfg.emailHost)
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = cfg.emailSender
    msg['To'] = ','.join(toEmails)
    msg['CC'] = ','.join(ccEmails)
    allEmails = toEmails + ccEmails + bccEmails
    s.sendmail(cfg.emailSender, allEmails, msg.as_string())
    s.quit()
    return True
#    except:
#        return False

def getRandomPassword():
    myrg = random.SystemRandom()
    length = 7
    alphabet = string.letters[0:52] + string.digits
    pw = str().join(myrg.choice(alphabet) for _ in range(length))
    return pw

def setPassword(username, password):
    passHash = hashlib.md5(password).hexdigest()
    query = 'UPDATE users SET password = ? WHERE username = ?'
    query_db(query, (passHash, username))
    get_db().commit()

def checkPassword(username, password):
    passHash = hashlib.md5(password).hexdigest()
    query = 'SELECT password FROM users WHERE username = ?'
    result = query_db(query, (username,), one=True)
    return passHash == result['password']

def checkUserExists(username):
    query = 'SELECT * FROM users WHERE username = ?'
    result = query_db(query, (username,))
    if len(result) > 0:
        return True
    else:
        return False
    
def createNewUser(username, fName, lName, email):
    password = getRandomPassword()
    query = 'INSERT INTO users (username, password, fName, lName, email) VALUES (?,?,?,?,?)'
    query_db(query, (username, password, fName, lName, email))
    get_db().commit()
    success = sendPasswordEmail(username, password)
    if success:
        flash('Sent email to %s with password'%(email))
    else:
        flash('Password email could not be sent. Please notify librarian.')

def doResetPassword(username):
    password = getRandomPassword()
    setPassword(username, password)
    success = sendPasswordEmail(username, password)
    if success:
        flash('Sent email to %s with password'%(username))
    else:
        flash('Password email could not be sent. Please notify librarian.')

def sendPasswordEmail(username, password):
    query = 'SELECT email FROM users WHERE username = ?'
    result = query_db(query, (username,), one=True)
    toEmail = result['email']
    subject = 'Opera SD Library Password Reset'
    message = 'Hello!\n\n'
    message += 'Here is your new password for the Opera SD Library application:\n\n'
    message += password + '\n\n'
    message += 'Thanks,\nSDOS Librarian'
    success = sendMail([toEmail], [], [], subject, message)
    return success

def doBookCheckout(username, bookId):
    checkoutQuery = 'UPDATE books SET heldBy = ? WHERE id = ?'
    query_db(checkoutQuery, (username, bookId))
    get_db().commit()
    flash('You got it! (Book #%s)'%(bookId))

def doBookRequest(username, bookId):
    success = sendRequestEmail(username, bookId)
    if success:
        flash("Request email sent! (You'll get a copy.)")
    else:
        flash('Request email could not be sent.')

def sendRequestEmail(username, bookId):
    query = 'SELECT email FROM users WHERE username = ?'
    result = query_db(query, (username,), one=True)
    requesterEmail = result['email']
    
    query = 'SELECT books.*, users.email FROM books INNER JOIN users ON heldBy = username WHERE id = ?'
    result = query_db(query, (bookId,), one=True)
    title = result['title']
    authorFName = result['authorFName']
    authorLName = result['authorLName']
    ownerEmail = result['email']

    subject = 'Opera SD Library Book Request'
    message = 'Hello!\n\n'
    message += 'User %s has requested the following book:\n\n'%(username)
    message += '%s, %s:  %s\n\n'%(authorLName, authorFName, title)
    message += 'Please let him/her know once you are finished with the book and have returned it to the library. Or, even better, discuss options for sharing or taking turns if possible.\n\n'
    message += 'Thanks!\nSDOS Librarian'
    success = sendMail([ownerEmail], [requesterEmail], [], subject, message)
    return success

def doBookReturn(bookId):
    returnQuery = 'UPDATE books SET heldBy = NULL WHERE id = ?'
    query_db(returnQuery, (bookId,))
    get_db().commit()
    flash('Return has been processed! (Book #%s) Please leave the book in the library.'%(bookId))


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

# Reset password. If the account doesn't exist, create it.
@app.route('/passwordreset', methods=['GET','POST'])
def passwordReset():
    if request.method == 'POST':
        username = request.form['Email']
        if checkUserExists(username):
            doResetPassword(username)
        else:
            createNewUser(username, None, None, username)
        return redirect(url_for('login'))
    return render_template('password_reset.html')

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
        
