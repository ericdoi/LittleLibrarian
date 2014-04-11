import main

def doTestEmail():
    main.sendMail(['ricekido@gmail.com'], ['ricekido@gmail.com'],['ricekido@gmail.com','edoi@operasolutions.com'], 'Test Subj', 'Hello! Testing.')

if __name__=='__main__':
    doTestEmail()
