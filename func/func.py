import os
import dns.resolver
from nic_api.models import TXTRecord
import subprocess
from email.mime.text import MIMEText
import smtplib
import cryptography
from cryptography.fernet import Fernet

class Func:
    def __init__(self):
        pass

    @classmethod
    def checkTXTRecord(self, DNS_SERVER, query_domain, test=False):
        try:
            for server in DNS_SERVER:
                resolver = dns.resolver.Resolver(configure=False)
                resolver.nameservers = [server]
                if test:
                    resolver.resolve(query_domain, 'A')
                    return True
                resolver.resolve(f'_acme-challenge.{query_domain}', 'TXT')
        except Exception as err:
            raise Exception(f'checkTXTRecord: {err}')


    @classmethod
    def mainDomainTail(self, domain):
        try:
            domain = domain.split(".")
            domain = domain[len(domain)-2:]
            tmp = []
            for level in domain:
                if "*" not in level:
                    tmp.append(level)
            domain = '.'.join(tmp)
            if domain:
                return domain
            return False
        except Exception as err:
            raise Exception(f'mainDomainTail: {err}')


    @classmethod
    def NIC_findTXTID(self, data):
        try:
            ids = []
            for record in data:
                # skip all records except TXT
                if type(record) is TXTRecord or dict:
                    # convert TXTRecord type to string
                    record = repr(record)
                    # convert string to dictionary
                    record = eval(record)
                    if "_acme-challenge" in record['name']:
                        ids.append(record['id'])
            return ids
        except Exception as err:
            raise Exception(f'NIC_findTXTID: {err}')


    @classmethod
    def call(self, command):
        try:
            process = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True, universal_newlines=True)
            std_out, std_err = process.communicate()
            return process.returncode, std_out, std_err
        except Exception as err:
            raise Exception(f'call: {err}')


    @classmethod
    def sendEmail(self, SENDER, RECIPIENT, subject, text, test=False, SMTPSERVER='', SMTPPORT='', SMTPUSER='', SMTPPASS=''):
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
            raise Exception(f'sendEmail: {err}')


    @classmethod
    # make domains list like '-d domain1.com -d domain2.com...'
    def makeList(self, ZONE):
        try:
            tmp = []
            for domain in ZONE:
                domain = f'-d {domain}'
                tmp.append(domain)
            data = (' ').join(tmp)
            return data
        except Exception as err:
            raise Exception(f'makeList: {err}')


    @classmethod
    def makeMainDomain(self, ZONE):
        try:
            main_domain = ZONE[0]
            if '*' in main_domain:
                # if main_domain contains wildcard then remove wildcard and dot
                main_domain[2:]
            return main_domain
        except Exception as err:
            raise Exception(f'makeMainDomain: {err}')


    @classmethod
    def acmeRun(self, MAIN_DOMAIN, DOMAIN_LIST, CERTBOT, ADMIN_EMAIL, CONFIG_DIR, AUTH_HOOK, CLEAN_HOOK, test=False, renew=False):
        try:
            #MAIN_DOMAIN = self.makeMainDomain(ZONE)
            #DOMAIN_LIST = self.makeList(ZONE)
            DRY_RUN = ''
            if test:
                DRY_RUN = '--dry-run'
            PARAM = 'certonly'
            if renew:
                PARAM = 'renew --force-renewal'
            code, out, err = self.call(f'{CERTBOT} {PARAM} --agree-tos --email {ADMIN_EMAIL} --config-dir {CONFIG_DIR} --cert-name {MAIN_DOMAIN} --manual --preferred-challenges dns {DRY_RUN} --manual-auth-hook {AUTH_HOOK} --manual-cleanup-hook {CLEAN_HOOK} {DOMAIN_LIST}')
            return code, out, err
        except Exception as err:
            raise Exception(f'acmeRun: {err}')


    @classmethod
    def reloadServer(self, TESTCONFIG, RELOADCONFIG):
        try:
            code, out, err = self.call(TESTCONFIG)
            if code != 0:
                return code, out, err
            code, out, err = self.call(RELOADCONFIG)
            return code, out, err
        except Exception as err:
            raise Exception(f'reloadServer: {err}')


    @classmethod
    def exportCredentials(self, USERNAME, PASSWORD, CLIENTID, CLIENT_SECRET):
        try:
            os.environ['NICUSER'] = USERNAME
            os.environ['NICPASS'] = PASSWORD
            os.environ['NICID'] = CLIENTID
            os.environ['NICSECRET'] = CLIENT_SECRET
        except Exception as err:
            raise Exception(f'exportCredentials: {err}')


    @classmethod
    def destroyCredentials(self):
        try:
            os.environ.clear()
        except Exception as err:
            raise Exception(f'destroyCredentials: {err}')


    @classmethod
    def deactivated(self, LE_LOG):
        try:
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
        except Exception as err:
            raise Exception(f'deactivated: {err}')


    @classmethod
    # uname - username
    # pwd - password
    # cid - client id
    # cs - client secret
    def encrypt(self, ENC_KEY, ENC_DAT, uname, pwd, cid, cs):
        try:
            fernet = Fernet(ENC_KEY.encode())
            string = f'{uname},{pwd},{cid},{cs}'
            encrypted = fernet.encrypt(string.encode())
            with open(ENC_DAT, 'wb') as f:
                f.write(encrypted)
            return True
        except Exception as err:
            raise Exception(f'encrypt: {err}')


    @classmethod
    # return username, password, client_id, client_secret
    def decrypt(self, ENC_KEY, ENC_DAT):
        try:
            with open(ENC_DAT, 'rb') as f:
                data = f.read()
            fernet = Fernet(ENC_KEY.encode())
            decrypted = fernet.decrypt(data)
            d = decrypted.decode().split(',')
            return d[0], d[1], d[2], d[3]
        except Exception as err:
            raise Exception(f'decrypt: {err}')


    @classmethod
    def inputNICCreds(self):
        try:
            username = input('Enter NIC-D: ')
            password = input('Enter password: ')
            client_id = input('Client ID: ')
            client_secret = input('Client secret: ')
            return username, password, client_id, client_secret
        except Exception as err:
            raise Exception(f'inputNICCreds: {err}')