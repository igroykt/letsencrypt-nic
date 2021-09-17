#!/usr/local/bin/python3

import pytest

# test auth.py
from auth import checkTXTRecord
result = checkTXTRecord('google.com', test=True)
assert isinstance(result, bool)

# test clean.py
from clean import mainDomainTail
result = mainDomainTail('test.google.com')
assert result == 'google.com'

from clean import findTXTID
result = findTXTID([{'name':'_acme-challenge.google.com', 'id':'google.com'}])
assert result == ['google.com']

# test main.py
from main import *
code, out, err = call('ls')
assert code == 0

#result = sendEmail('test','test message', test=True)
#assert isinstance(result, bool)

result = makeList()
assert result == '-d mydomain.ru -d  *.mydomain.ru -d  mydomain2.ru'

result = makeMainDomain()
assert result == 'mydomain.ru'

result = encrypt('testuser', 'testpass', 'testid', 'testsecret')
assert isinstance(result, bool)

username, password, client_id, client_secret = decrypt()
assert username == 'testuser'