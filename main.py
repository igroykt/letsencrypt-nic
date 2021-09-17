import os, sys
from configparser import ConfigParser
import platform
import subprocess
from email.mime.text import MIMEText
import smtplib
from datetime import date
import logging
import cryptography
from cryptography.fernet import Fernet

script_dir = os.path.dirname(os.path.realpath(__file__))
config = ConfigParser()
try:
    config.read(script_dir + '/config.ini')
except Exception as err:
    raise SystemExit(f'Config parse: {err}')

ZONE = config.get('GENERAL', 'ZONE').split(',')
ADMIN_EMAIL = config.get('GENERAL', 'ADMIN_EMAIL')
CONFIG_DIR = config.get('GENERAL', 'LE_CONFIG_DIR')
CERTBOT = config.get('GENERAL', 'CERTBOT')
LELOG = config.get('GENERAL', 'LE_LOG')
WEBSERVERENABLED = config.get('WEBSERVER', 'ENABLED')
TESTCONFIG = config.get('WEBSERVER', 'TEST_CONFIG')
RELOADCONFIG = config.get('WEBSERVER', 'RELOAD_CONFIG')
SMTPENABLED = config.get('SMTP', 'ENABLED')
SMTPSERVER = config.get('SMTP', 'SERVER')
SMTPPORT = config.get('SMTP', 'PORT')
SMTPUSER = config.get('SMTP', 'USERNAME')
SMTPPASS = config.get('SMTP', 'PASSWORD')
SENDER = config.get('SMTP', 'FROM')
RECIPIENT = config.get('SMTP', 'TO').split(',')
POSTHOOKENABLED = config.get('POSTHOOK', 'ENABLED')
POSTHOOKSCRIPT = config.get('POSTHOOK', 'SCRIPT')
HOSTNAME = platform.node()
LOG_FILE = config.get('LOG', 'LOG_FILE')
if(config.get('LOG', 'LOG_LEVEL') == 'INFO'):
    LOG_LEVEL = logging.INFO
if(config.get('LOG', 'LOG_LEVEL') == 'DEBUG'):
    LOG_LEVEL = logging.DEBUG
if(config.get('LOG', 'LOG_LEVEL') == 'ERROR'):
    LOG_LEVEL = logging.ERROR
if platform.system() == "Windows":
    AUTH_HOOK = f'{script_dir}/auth.exe'
    CLEAN_HOOK = f'{script_dir}/clean.exe'
else:
    AUTH_HOOK = f'{script_dir}/auth'
    CLEAN_HOOK = f'{script_dir}/clean'
ENC_KEY = 'XXX'

logging.basicConfig(format = '%(levelname)-8s [%(asctime)s] %(message)s', level = LOG_LEVEL, filename = f'{script_dir}/{LOG_FILE}')

def call(command):
	process = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True, universal_newlines=True)
	std_out, std_err = process.communicate()
	return process.returncode, std_out, std_err


def sendEmail(subject, text, test=False):
    try:
        RECIPIENT_LIST = ','.join(RECIPIENT)
        BODY = "\r\n".join((
            "From: %s" % SENDER,
            "To: %s" % RECIPIENT_LIST,
            "Subject: %s" % subject,
            "",
            text
        ))
        server = smtplib.SMTP(SMTPSERVER, SMTPPORT)
        # if SMTPPASS not empty then use smtp authentication with tls
        if len(SMTPPASS) > 0:
            server.ehlo()
            server.starttls()
            server.login(SMTPUSER, SMTPPASS)
        server.sendmail(SENDER, RECIPIENT, BODY)
        server.quit()
        if test:
            return True
    except Exception as err:
        raise SystemExit(err)


# make domains list like '-d domain1.com -d domain2.com...'
def makeList():
    tmp = []
    for domain in ZONE:
        domain = f'-d {domain}'
        tmp.append(domain)
    data = (' ').join(tmp)
    return data


def makeMainDomain():
    main_domain = ZONE[0]
    if '*' in main_domain:
        # if main_domain contains wildcard then remove wildcard and dot
        main_domain[2:]
    return main_domain


def acmeRun(test=False, renew=False):
    MAIN_DOMAIN = makeMainDomain()
    DOMAIN_LIST = makeList()
    DRY_RUN = ''
    if test:
        DRY_RUN = '--dry-run'
    PARAM = 'certonly'
    if renew:
        PARAM = 'renew --force-renewal'
    code, out, err = call(f'{CERTBOT} {PARAM} --agree-tos --email {ADMIN_EMAIL} --config-dir {CONFIG_DIR} --cert-name {MAIN_DOMAIN} --manual --preferred-challenges dns {DRY_RUN} --manual-auth-hook {AUTH_HOOK} --manual-cleanup-hook {CLEAN_HOOK} {DOMAIN_LIST}')
    return code, out, err


def reloadServer():
    code, out, err = call(TESTCONFIG)
    if code != 0:
        return code, out, err
    code, out, err = call(RELOADCONFIG)
    return code, out, err


def exportCredentials(USERNAME, PASSWORD, CLIENTID, CLIENT_SECRET):
    os.environ['NICUSER'] = USERNAME
    os.environ['NICPASS'] = PASSWORD
    os.environ['NICID'] = CLIENTID
    os.environ[NICSECRET] = CLIENT_SECRET


def destroyCredentials():
    os.environ.clear()


def deactivated():
    today = date.today()
    # current date for search in log
    c_date = str(today.strftime("%Y-%m-%d"))
    # string for search in log
    s_str = 'deactivated'
    with open(LE_LOG) as f:
        dump = f.readlines()
    if line in dump:
        if c_date in line and s_str in line:
            return True
    return False


def encrypt(uname, pwd, cid, cs):
    fernet = Fernet(ENC_KEY)
    encrypted = fernet.encrypt(f'{uname},{pwd},{cid},{cs}')
    with open(f'{script_dir}/enc.key', 'wb') as f:
        f.write(encrypted)


def decrypt():
    with open(f'{script_dir}/enc.key', 'rb') as f:
        data = f.read()
    fernet = Fernet(ENC_KEY)
    decrypted = fernet.decrypt(data)
    d = decrypted.split(',')
    return d[0], d[1], d[2], d[3]


def main():
    logging.info('-= LetsEncrypt NIC =-')


if __name__ == '__main__':
    main()