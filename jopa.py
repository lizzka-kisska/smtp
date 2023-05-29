with open('configuration/config.txt') as f:
    data = f.read().split('\n')
    mails = data[0].split(', ')
    TO = ''
    for mail in mails:
        TO += mail + ','
    print(TO)


