from flask import g, flash
import config as cfg
import smtplib
from email.mime.text import MIMEText
from dbFunctions import *

siteName = 'LittleLibrarian'

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
    subject = '%s Account Creation'%(siteName)
    message = 'Welcome to the %s system!\n\n'%(siteName)
    message += 'Here is your new password for the %s application:\n\n'%(siteName)
    message += 'Username: %s\n'%(username)
    message += 'Password: %s\n\n'%(password)
    message += 'Thanks,\nYour Librarian'
    success = sendMail([toEmail], [], [], subject, message)
    return success

def sendPasswordEmail(username, password):
    """Send an email for a password reset."""
    query = 'SELECT email FROM users WHERE username = ?'
    result = query_db(query, (username,), one=True)
    toEmail = result['email']
    subject = '%s Password Reset'%(siteName)
    message = 'Hello!\n\n'
    message += 'Someone (hopefully you) has requested a password reset for your account on the %s system.\n\n'%(siteName)
    message += 'Your new password: %s\n\n'%(password)
    message += 'Thanks,\nYour Librarian'
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

    subject = '%s Book Request'%(siteName)
    message = 'Hello!\n\n'
    message += 'User %s has requested the following book:\n\n'%(username)
    message += '%s, %s:  %s\n\n'%(authorLName, authorFName, title)
    message += 'Please let him/her know once you are finished with the book and have returned it to the library. Or, even better, discuss options for sharing or taking turns if possible.\n\n'
    message += 'Thanks!\nYour Librarian'
    success = sendMail([ownerEmail], [requesterEmail], [], subject, message)
    return success

def sendMissingEmail(fromUser, bookId):
    """Send an email to the librarian to report a missing book."""
    query = 'SELECT email FROM users WHERE username = ?'
    result = query_db(query, (fromUser,), one=True)
    requesterEmail = result['email']
    
    query = 'SELECT * FROM books WHERE id = ?'
    result = query_db(query, (bookId,), one=True)
    title = result['title']
    authorFName = result['authorFName']
    authorLName = result['authorLName']

    subject = '%s Missing Report'(siteName)
    message = 'Hello!\n\n'
    message += 'Thanks for reporting the following book as missing:\n\n'
    message += '%s, %s:  %s\n\n'%(authorLName, authorFName, title)
    message += 'If a user claims the book, you will receive an email notification. Or, if I find the book, I will let you know.\n\n'
    message += 'Thanks!\nYour Librarian'
    success = sendMail([requesterEmail], [cfg.emailSender], [], subject, message)
    return success

def sendFoundEmail(claimUser, bookId):
    """Send an email to the reporter if a missing book is claimed."""
    #query = 'SELECT email FROM users WHERE username = ?'
    #result = query_db(query, (claimUser,), one=True)
    #claimEmail = result['email']
    
    query = 'SELECT books.*, users.email FROM books INNER JOIN users ON reportedMissingBy = username WHERE id = ?'
    result = query_db(query, (bookId,), one=True)
    if result is None:
        return False

    title = result['title']
    authorFName = result['authorFName']
    authorLName = result['authorLName']
    reporterUser = result['reportedMissingBy']
    reporterEmail = result['email']

    if reporterUser == claimUser:
        return False # No point in notifying

    subject = '%s Found Book Notification'%(siteName)
    message = 'Hello!\n\n'
    message += 'The following book, which you reported as missing, has been claimed by user %s:\n\n'%(claimUser)
    message += '%s, %s:  %s\n\n'%(authorLName, authorFName, title)
    message += 'If you are still interested in the book, please check the status on the website. If it has not been returned yet, you can use the website to send a request email.\n\n'
    message += 'Thanks!\nYour Librarian'
    success = sendMail([reporterEmail], [], [], subject, message)
    return success
