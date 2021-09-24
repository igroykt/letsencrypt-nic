import os, sys
from configparser import ConfigParser
import platform
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
WEBSERVERENABLED = config.getboolean('WEBSERVER', 'ENABLED')
TESTCONFIG = config.get('WEBSERVER', 'TEST_CONFIG')
RELOADCONFIG = config.get('WEBSERVER', 'RELOAD_CONFIG')
SMTPENABLED = config.getboolean('SMTP', 'ENABLED')
SMTPSERVER = config.get('SMTP', 'SERVER')
SMTPPORT = int(config.get('SMTP', 'PORT'))
SMTPUSER = config.get('SMTP', 'USERNAME')
SMTPPASS = config.get('SMTP', 'PASSWORD')
SENDER = config.get('SMTP', 'FROM')
RECIPIENT = config.get('SMTP', 'TO').split(',')
SLACKENABLED = config.getboolean('SLACK', 'ENABLED')
SLACKWEBHOOK = config.get('SLACK', 'WEBHOOK')
TELEGRAMENABLED = config.getboolean('TELEGRAM', 'ENABLED')
TELEGRAMTOKEN = config.get('TELEGRAM', 'TOKEN')
TELEGRAMCHATID = config.get('TELEGRAM', 'CHAT_ID')
POSTHOOKENABLED = config.getboolean('POSTHOOK', 'ENABLED')
POSTHOOKSCRIPT = config.get('POSTHOOK', 'SCRIPT')
HOSTNAME = platform.node()
LOG_FILE = config.get('LOG', 'LOG_FILE')
if platform.system() == "Windows":
    AUTH_HOOK = f'{script_dir}/auth.exe'
    CLEAN_HOOK = f'{script_dir}/clean.exe'
else:
    AUTH_HOOK = f'{script_dir}/auth.py'
    CLEAN_HOOK = f'{script_dir}/clean.py'
ENC_KEY = 'XXX'
ENC_DAT = f'{script_dir}/enc.dat'

log.basicConfig(format = '%(levelname)-8s [%(asctime)s] %(filename)s %(lineno)d: %(message)s', filename = f'{script_dir}/{LOG_FILE}', filemode='w')


def notify(subject, msg, test=False):
    if SMTPENABLED:
        try:
            Func.sendEmail(SENDER, RECIPIENT, subject, msg, SMTPSERVER, SMTPPORT, SMTPUSER, SMTPPASS)
        except Exception as err:
            log.error(err)
            sys.exit(err)
    if SLACKENABLED:
        try:
            Func.slackSend(SLACKWEBHOOK, f'{subject} {msg}')
        except Exception as err:
            log.error(err)
            sys.exit(err)
    if TELEGRAMENABLED:
        try:
            Func.telegramSend(TELEGRAMTOKEN, TELEGRAMCHATID, f'{subject} {msg}')
        except Exception as err:
            log.error(err)
            sys.exit(err)


def main():
    parser = argparse.ArgumentParser(description='LetsEncrypt NIC')
    parser.add_argument('-v', dest='verbose', help='verbose output', action='store_true', required=False)
    parser.add_argument('-t', dest='test', help='test (not actual run)', action='store_true', required=False)
    parser.add_argument('-n', dest='new_cert', help='obtain new certificate', action='store_true', required=False)
    parser.add_argument('-a', dest='add_creds', help='add credentials', action='store_true', required=False)
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
            notify(f'[ {HOSTNAME} ] decrypt [ FAILED ]', str(err))
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
            notify(f'[ {HOSTNAME} ] makeList [ FAILED ]', str(err))
            raise SystemExit(err)
        # certbot dry run
        if args.test:
            if args.verbose:
                print('[+] ACME Test: [ START ]')
            log.info('[+] ACME Test: [ START ]')
            try:
                code, out, err = Func.acmeRun(maindomain, domains, CERTBOT, ADMIN_EMAIL, CONFIG_DIR, AUTH_HOOK, CLEAN_HOOK, test=True, new=args.new_cert)
                if code != 0:
                    log.error(err)
                    sys.exit(err)
            except Exception as err:
                log.error(err)
                notify(f'[ {HOSTNAME} ] ACME Test: [ FAILED ]', str(err), test=True)
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
            code, out, err = Func.acmeRun(maindomain, domains, CERTBOT, ADMIN_EMAIL, CONFIG_DIR, AUTH_HOOK, CLEAN_HOOK, new=args.new_cert)
            if code != 0:
                log.error(err)
                sys.exit(err)
        except Exception as err:
            log.error(err)
            notify(f'[ {HOSTNAME} ] ACME Run: [ FAILED ]', str(err))
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
                notify(f'[ {HOSTNAME} ] SERVER Reload [ FAILED ]', str(err))
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
            log.info('[+] POST HOOK Run: [ START]')
            try:
                code, out, err = Func.call(POSTHOOKSCRIPT)
            except Exception as err:
                log.error(err)
                notify(f'[ {HOSTNAME} ] POST HOOK Run [ FAILED ]', str(err))
                raise SystemExit(err)
            if args.verbose:
                print('[+] POST HOOK Run: [ DONE ]')
            log.info('[+] POST HOOK Run: [ DONE ]')
        # complete
        if args.verbose:
            print('-= Program completed! =-')
        log.info('-= Program completed! =-')
        sys.exit(0)
    except KeyboardInterrupt:
        raise SystemExit('\n-= Program terminated... =-')


if __name__ == '__main__':
    main()