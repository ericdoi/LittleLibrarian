from flask import g, flash
import config as cfg
import smtplib
from email.mime.text import MIMEText
from dbFunctions import *

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
