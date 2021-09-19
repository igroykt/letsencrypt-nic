#!/usr/local/bin/python3

import os
import pytest
from func import Func

result = Func.checkTXTRecord(['8.8.8.8'], 'google.com', test=True)
assert isinstance(result, bool)

result = Func.mainDomainTail('test.google.com')
assert result == 'google.com'

result = Func.NIC_findTXTID([{'name':'_acme-challenge.google.com', 'id':'google.com'}])
assert result == ['google.com']

code, out, err = Func.call('ls')
assert code == 0

'''
result = Func.sendEmail(
    'robot@mydomain.ru',
    ['admin@mydomain.ru', 'security@mydomain.ru'],
    'test',
    'test message',
    test=True,
    'smtp.gmail.com',
    '587',
    'xxx',
    'yyy'
)
assert isinstance(result, bool)
'''

result = Func.makeList(['mydomain.ru', '*.mydomain.ru', 'mydomain2.ru'])
assert result == '-d mydomain.ru -d *.mydomain.ru -d mydomain2.ru'

result = Func.makeMainDomain(['mydomain.ru', '*.mydomain.ru', 'mydomain2.ru'])
assert result == 'mydomain.ru'

ENC_KEY = '0IFzRIVb4i42OPaovw0RDHNgOiRsKLlyDumAW_xFs0M='
script_dir = os.path.dirname(os.path.realpath(__file__))
ENC_DAT = f'{script_dir}/enc.dat'
result = Func.encrypt(ENC_KEY, ENC_DAT, 'testuser', 'testpass', 'testid', 'testsecret')
assert isinstance(result, bool)

username, password, client_id, client_secret = Func.decrypt(ENC_KEY, ENC_DAT)
assert username == 'testuser'

result = Func.mainDomainTail('top.level.mydomain.ru')
assert result == 'mydomain.ru'