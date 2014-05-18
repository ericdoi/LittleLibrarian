import main

def doTestEmail():
    main.sendMail(['name@email.com'], [],[], 'Test Subj', 'Hello! Testing.')

if __name__=='__main__':
    doTestEmail()
