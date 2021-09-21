import os, sys
from configparser import ConfigParser
import platform
#from datetime import date
import logging as log
from func import Func
import argparse

try:
    script_dir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser()
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
SLACKENABLED = config.get('SLACK', 'ENABLED')
SLACKWEBHOOK = config.get('SLACK', 'WEBHOOK')
TELEGRAMENABLED = config.get('TELEGRAM', 'ENABLED')
TELEGRAMTOKEN = config.get('TELEGRAM', 'TOKEN')
TELEGRAMCHATID = config.get('TELEGRAM', 'CHAT_ID')
POSTHOOKENABLED = config.get('POSTHOOK', 'ENABLED')
POSTHOOKSCRIPT = config.get('POSTHOOK', 'SCRIPT')
HOSTNAME = platform.node()
LOG_FILE = config.get('LOG', 'LOG_FILE')
if(config.get('LOG', 'LOG_LEVEL') == 'INFO'):
    LOG_LEVEL = log.INFO
if(config.get('LOG', 'LOG_LEVEL') == 'DEBUG'):
    LOG_LEVEL = log.DEBUG
if(config.get('LOG', 'LOG_LEVEL') == 'ERROR'):
    LOG_LEVEL = log.ERROR
if platform.system() == "Windows":
    AUTH_HOOK = f'{script_dir}/auth.exe'
    CLEAN_HOOK = f'{script_dir}/clean.exe'
else:
    AUTH_HOOK = f'python3 {script_dir}/auth.py'
    CLEAN_HOOK = f'python3 {script_dir}/clean.py'
ENC_KEY = '0IFzRIVb4i42OPaovw0RDHNgOiRsKLlyDumAW_xFs0M='
ENC_DAT = f'{script_dir}/enc.dat'

log.basicConfig(format = '%(levelname)-8s [%(asctime)s] %(message)s', level = LOG_LEVEL, filename = f'{script_dir}/{LOG_FILE}', filemode='w')


def notify(subject, msg, test=False):
    if SMTPENABLED:
        Func.sendEmail(SENDER, RECIPIENT, subject, err, SMTPSERVER, SMTPPORT, SMTPUSER, SMTPUSER)
    if SLACKENABLED:
        Func.slackSend(SLACKWEBHOOK, f'{subject} {msg}')
    if TELEGRAMENABLED:
        Func.telegramSend(TELEGRAMTOKEN, TELEGRAMCHATID, f'{subject} {msg}')


def main():
    parser = argparse.ArgumentParser(description='LetsEncrypt NIC')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='print verbose', required=False)
    group.add_argument('-t', '--test', action='store_true', help='dry run', required=False)
    group.add_argument('-n', '--new-cert', action='store_true', help='obtain new certificate', required=False)
    group.add_argument('-a', '--add-creds', action='store_true', help='add credentials', required=False)
    args = parser.parse_args()

    try:
        # save credentials
        if args.add_creds:
            nicuser, nicpass, nic_id, nic_sec = Func.NIC_inputCreds()
            Func.encrypt(ENC_KEY, ENC_DAT, nicuser, nicpass, nic_id, nic_sec)
            print('Credentials encrypted and saved! Exit...')
            sys.exit(0)
        # decrypt
        if args.verbose:
            print('-= LetsEncrypt NIC =-')
        log.info('-= LetsEncrypt NIC =-')
        try:
            USER, PASS, CLIENT_ID, CLIENT_SECRET = Func.decrypt(ENC_KEY, ENC_DAT)
        except Exception as err:
            log.error(err)
            notify(f'[ {HOSTNAME} ] decrypt [ FAILED ]', err)
            raise SystemExit(err)
        # export credentials
        Func.exportCredentials(USER, PASS, CLIENT_ID, CLIENT_SECRET)
        # make domains list
        if args.verbose:
            print('Preparing domain list...')
        log.info('Preparing domain list...')
        try:
            maindomain = Func.makeMainDomain(ZONE)
            domains = Func.makeList(ZONE)
        except Exception as err:
            log.error(err)
            notify(f'[ {HOSTNAME} ] makeList [ FAILED ]', err)
            raise SystemExit(err)
        # certbot dry run
        if args.test:
            if args.verbose:
                print('[+] ACME Test: [ START ]')
            log.info('[+] ACME Test: [ START ]')
            try:
                code, out, err = Func.acmeRun(maindomain, domains, CERTBOT, ADMIN_EMAIL, CONFIG_DIR, AUTH_HOOK, CLEAN_HOOK, test=True, renew=args.new_cert)
            except Exception as err:
                log.error(err)
                notify(f'[ {HOSTNAME} ] ACME Test: [ FAILED ]', err, test=True)
                raise SystemExit(err)
            if args.verbose:
                print('[+] ACME Test: [ DONE ]')
            log.info('[+] ACME Test: [ DONE ]')
            log.info('-= Program completed! =-')
            sys.exit('-= Program completed! =-')
        # certbot run
        if args.verbose:
            print('[+] ACME Run: [ START ]')
        log.info('[+] ACME Run: [ START ]')
        try:
            code, out, err = Func.acmeRun(maindomain, domains, CERTBOT, ADMIN_EMAIL, CONFIG_DIR, AUTH_HOOK, CLEAN_HOOK, renew=args.new_cert)
        except Exception as err:
            log.error(err)
            notify(f'[ {HOSTNAME} ] ACME Run: [ FAILED ]', err)
            raise SystemExit(err)
        if args.verbose:
            print('[+] ACME Run: [ DONE ]')
        log.info('[+] ACME Run: [ DONE ]')
        # reload webserver
        if WEBSERVERENABLED:
            if args.verbose:
                print('[+] SERVER Reload: [ START ]')
            log.info('[+] SERVER Reload: [ START ]')
            try:
                Func.reloadServer(TESTCONFIG, RELOADCONFIG)
            except Exception as err:
                log.error(err)
                notify(f'[ {HOSTNAME} ] SERVER Reload [ FAILED ]', err)
                raise SystemExit(err)
            if args.verbose:
                print('[+] SERVER Reload: [ DONE ]')
            log.info('[+] SERVER Reload: [ DONE ]')
        # destroy credentials
        Func.destroyCredentials()
        # posthook run
        if POSTHOOKENABLED:
            if args.verbose:
                print('[+] POST HOOK Run: [ START]')
            log.error('[+] POST HOOK Run: [ START]')
            try:
                code, out, err = Func.call(POSTHOOKSCRIPT)
            except Exception as err:
                log.error(err)
                notify(f'[ {HOSTNAME} ] POST HOOK Run [ FAILED ]', err)
                raise SystemExit(err)
            if args.verbose:
                print('[+] POST HOOK Run: [ DONE ]')
            log.error('[+] POST HOOK Run: [ DONE ]')
        # complete
        if args.verbose:
            print('-= Program completed! =-')
        log.info('-= Program completed! =-')
        sys.exit('-= Program completed! =-')
    except KeyboardInterrupt:
        raise SystemExit('\n-= Program terminated... =-')


if __name__ == '__main__':
    main()