#!/bin/env python3

import os

import pytest
from func import Func
from unittest.mock import patch, MagicMock
import dns.resolver
import smtplib
from slack_webhook import Slack
import telegram
import hashlib
import json
from cpuinfo import get_cpu_info
import platform


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


def test_sendEmail():
    SENDER = 'test@example.com'
    RECIPIENT = ['recipient@example.com']
    subject = 'Test Subject'
    text = 'Test Body'
    SMTPSERVER = 'smtp.example.com'
    SMTPPORT = 587
    SMTPUSER = 'user'
    SMTPPASS = 'pass'
    
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        result = Func.sendEmail(SENDER, RECIPIENT, subject, text, SMTPSERVER, SMTPPORT, SMTPUSER, SMTPPASS, test=True)
        
        mock_smtp.assert_called_with(SMTPSERVER, SMTPPORT)
        mock_server.ehlo.assert_called_once()
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(SMTPUSER, SMTPPASS)
        mock_server.sendmail.assert_called_once_with(SENDER, RECIPIENT, '\r\n'.join((
            f"From: {SENDER}",
            f"To: {','.join(RECIPIENT)}",
            f"Subject: {subject}",
            "",
            text
        )))
        mock_server.quit.assert_called_once()
        
        assert result is True


def test_slackSend():
    URL = 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX'
    MSG = 'Test message'

    with patch('slack_webhook.Slack') as MockSlack:
        mock_slack_instance = MagicMock()
        mock_slack_instance.post.side_effect = Exception("HTTP Error 404: Not Found")
        MockSlack.return_value = mock_slack_instance

        with pytest.raises(Exception) as excinfo:
            Func.slackSend(URL, MSG)

        assert str(excinfo.value) == "slackSend: HTTP Error 404: Not Found"


def test_telegramSend():
    TOKEN = '123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11'
    CHAT_ID = '123456789'
    MSG = 'Test message'

    with patch('telegram.Bot') as MockBot:
        mock_bot_instance = MagicMock()
        mock_bot_instance.sendMessage.side_effect = Exception("HTTP Error 404: Not Found")
        MockBot.return_value = mock_bot_instance

        with pytest.raises(Exception) as excinfo:
            Func.telegramSend(TOKEN, CHAT_ID, MSG)

        assert str(excinfo.value) == "telegramSend: HTTP Error 404: Not Found"

        MockBot.assert_called_once_with(token=TOKEN)
        mock_bot_instance.sendMessage.assert_called_once_with(chat_id=CHAT_ID, text=MSG)


def test_makeCPUFingerprint():
    mock_cpu_info = "Intel(R) Core(TM) i7-7700HQ CPU @ 2.80GHz"
    expected_fingerprint = hashlib.sha256(mock_cpu_info.encode('utf-8')).hexdigest()
    with patch('cpuinfo.get_cpu_info', return_value=mock_cpu_info):
        cpu_fingerprint = Func.makeCPUFingerprint(test=True)
        cpu_fingerprint = expected_fingerprint = hashlib.sha256(cpu_fingerprint.encode('utf-8')).hexdigest()
        assert isinstance(cpu_fingerprint, str)
        assert cpu_fingerprint == expected_fingerprint


def test_getSystemUUID():
    result = Func.getSystemUUID(test=True)
    assert result == '7B23EFEE-9CF7-5030-8419-5DAE4CF77265'


def test_makeServerFingerprint():
    cpu_fingerprint = "Intel(R) Core(TM) i7-7700HQ CPU @ 2.80GHz"
    system_uuid = "7B23EFEE-9CF7-5030-8419-5DAE4CF77265d"
    expected_combined_fingerprint = hashlib.sha256((cpu_fingerprint + system_uuid).encode('utf-8')).hexdigest()
    with patch.object(Func, 'makeCPUFingerprint', return_value=cpu_fingerprint):
        with patch.object(Func, 'getSystemUUID', return_value=system_uuid):
            combined_fingerprint = Func.makeServerFingerprint(test=True)
            assert combined_fingerprint == expected_combined_fingerprint