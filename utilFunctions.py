from flask import g, flash
import config as cfg
from main import app
import sqlite3
import hashlib
import string, random
import smtplib
from email.mime.text import MIMEText

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
    """Send an email using the SMTP server in the config file."""
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
    """Create a random alphanumeric password."""
    myrg = random.SystemRandom()
    length = 7
    alphabet = string.letters[0:52] + string.digits
    pw = str().join(myrg.choice(alphabet) for _ in range(length))
    return pw

def setPassword(username, password):
    """Set the given password in the database."""
    passHash = hashlib.md5(password).hexdigest()
    query = 'UPDATE users SET password = ? WHERE username = ?'
    query_db(query, (passHash, username))
    get_db().commit()

def checkPassword(username, password):
    """Test whether the given user, password pair is correct."""
    passHash = hashlib.md5(password).hexdigest()
    query = 'SELECT password FROM users WHERE username = ?'
    result = query_db(query, (username,), one=True)
    return passHash == result['password']

def checkUserExists(username):
    """Check whether given username has an entry in the DB."""
    query = 'SELECT * FROM users WHERE username = ?'
    result = query_db(query, (username,))
    if len(result) > 0:
        return True
    else:
        return False
    
def createNewUser(username, fName, lName, email):
    """Create a new user in the DB."""
    password = getRandomPassword()
    query = 'INSERT INTO users (username, password, fName, lName, email) VALUES (?,?,?,?,?)'
    query_db(query, (username, password, fName, lName, email))
    get_db().commit()
    success = sendPasswordEmail(username, password)
    if success:
        flash('User created! Sent email to %s with password.'%(email))
    else:
        flash('Password email could not be sent. Please notify librarian.')

def doResetPassword(username):
    """Reset password for the given user and send an email."""
    password = getRandomPassword()
    setPassword(username, password)
    success = sendPasswordEmail(username, password)
    if success:
        flash('Sent email to %s with password.'%(username))
    else:
        flash('Password email could not be sent. Please notify librarian.')

def sendCreationEmail(username, password):
    """Send an email for creation of a new user."""
    query = 'SELECT email FROM users WHERE username = ?'
    result = query_db(query, (username,), one=True)
    toEmail = result['email']
    subject = 'Opera SD Library Account Creation'
    message = 'Welcome to the Opera SD Library system!\n\n'
    message += 'Here is your new password for the Opera SD Library application:\n\n'
    message += 'Username: %s\n'%(username)
    message += 'Password: %s\n\n'%(password)
    message += 'Thanks,\nSDOS Librarian'
    success = sendMail([toEmail], [], [], subject, message)
    return success

def sendPasswordEmail(username, password):
    """Send an email for a password reset."""
    query = 'SELECT email FROM users WHERE username = ?'
    result = query_db(query, (username,), one=True)
    toEmail = result['email']
    subject = 'Opera SD Library Password Reset'
    message = 'Hello!\n\n'
    message += 'Someone (hopefully you) has requested a password reset for your account on the Opera SD Library system.\n\n'
    message += 'Your new password: %s\n\n'%(password)
    message += 'Thanks,\nSDOS Librarian'
    success = sendMail([toEmail], [], [], subject, message)
    return success

def doBookCheckout(username, bookId):
    """Update the DB for a book checkout."""
    checkoutQuery = 'UPDATE books SET heldBy = ? WHERE id = ?'
    query_db(checkoutQuery, (username, bookId))
    get_db().commit()
    flash('You got it! (Book #%s)'%(bookId))

def doBookRequest(username, bookId):
    """Send a book request email."""
    success = sendRequestEmail(username, bookId)
    if success:
        flash("Request email sent! (You'll get a copy.)")
    else:
        flash('Request email could not be sent.')

def sendRequestEmail(username, bookId):
    """Send an email for requesting a book from another user."""
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
    """Update DB to return given book."""
    returnQuery = 'UPDATE books SET heldBy = NULL WHERE id = ?'
    query_db(returnQuery, (bookId,))
    get_db().commit()
    flash('Return has been processed! (Book #%s) Please leave the book in the library.'%(bookId))
