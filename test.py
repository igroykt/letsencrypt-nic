#!/bin/env python3

import os

import pytest
from func import Func
from unittest.mock import patch, MagicMock
import dns.resolver

'''
def test_checkTXTRecord():
    result = Func.checkTXTRecord(['8.8.8.8'], 'google.com', test=True)
    assert isinstance(result, bool)
'''


def test_checkTXTRecord():
    def mock_resolve(domain, record_type):
        if domain == 'google.com' and record_type == 'A':
            # After 9 wrong answers, we return a correct one
            mock_resolve.counter += 1
            if mock_resolve.counter >= 10:
                return MagicMock()
            else:
                raise dns.resolver.NoAnswer
        elif domain == '_acme-challenge.google.com' and record_type == 'TXT':
            # After 9 wrong answers, we return a correct one
            mock_resolve.counter += 1
            if mock_resolve.counter >= 10:
                return MagicMock()
            else:
                raise dns.resolver.NoAnswer
        else:
            raise dns.resolver.NoAnswer
    
    mock_resolve.counter = 0

    with patch('dns.resolver.Resolver.resolve', side_effect=mock_resolve):
        result = Func.checkTXTRecord(['8.8.8.8'], 'google.com', test=True)
        assert isinstance(result, bool)
        assert result is True
        assert mock_resolve.counter == 10


def test_mainDomainTail():
    result = Func.mainDomainTail('top.level.mydomain.ru')
    assert result == 'mydomain.ru'

def test_NIC_findTXTID():
    result = Func.NIC_findTXTID([{'name':'_acme-challenge.google.com', 'id':'google.com'}])
    assert result == ['google.com']

def test_call():
    code, out, err = Func.call('ls')
    assert code == 0

def test_makeList():
    result = Func.makeList(['mydomain.ru', '*.mydomain.ru', 'mydomain2.ru'])
    assert result == '-d mydomain.ru -d *.mydomain.ru -d mydomain2.ru'

def test_makeMainDomain():
    result = Func.makeMainDomain(['mydomain.ru', '*.mydomain.ru', 'mydomain2.ru'])
    assert result == 'mydomain.ru'

ENC_KEY = '0IFzRIVb4i42OPaovw0RDHNgOiRsKLlyDumAW_xFs0M='
script_dir = os.path.dirname(os.path.realpath(__file__))
ENC_DAT = f'{script_dir}/test_enc.dat'

def test_encrypt():
    result = Func.encrypt(ENC_KEY, ENC_DAT, 'testuser', 'testpass', 'testid', 'testsecret')
    assert isinstance(result, bool)

def test_decrypt():
    username, password, client_id, client_secret = Func.decrypt(ENC_KEY, ENC_DAT)
    assert username == 'testuser'
