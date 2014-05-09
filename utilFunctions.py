from flask import g, flash
import config as cfg
from main import app
import hashlib
import string, random
from emailFunctions import *
from dbFunctions import *

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

def doBookReturn(bookId):
    """Update DB to return given book."""
    returnQuery = 'UPDATE books SET heldBy = NULL WHERE id = ?'
    query_db(returnQuery, (bookId,))
    get_db().commit()
    flash('Return has been processed! (Book #%s) Please leave the book in the library.'%(bookId))
