import os, sys
from nic_api import DnsApi
from nic_api.models import TXTRecord
from configparser import ConfigParser
import time
from tld import get_tld
from func import Func
import json

try:
    if getattr(sys, 'frozen', False):
        script_dir = os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.realpath(__file__))
    config = ConfigParser()
    config.read(script_dir + os.sep + "config.ini")
except Exception as err:
    raise SystemExit(f"Config parse: {err}")

USERNAME = os.getenv('NICUSER')
PASSWORD = os.getenv('NICPASS')
CLIENT_ID = os.getenv('NICID')
CLIENT_SECRET = os.getenv('NICSECRET')
SERVICE_ID = config.get('GENERAL', 'SERVICE_ID')
DNS_SERVER = config.get('GENERAL', 'DNS_SERVER').split(',')
TTL = config.get('GENERAL', 'TTL')
SLEEP = int(config.get('GENERAL', 'SLEEP'))
CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')
CERTBOT_VALIDATION = os.getenv('CERTBOT_VALIDATION')
CERTBOT_REMAINING = int(os.getenv('CERTBOT_REMAINING_CHALLENGES'))
VERBOSE = os.getenv('VERBOSE')
TOKEN_FILE = script_dir + os.sep + "nic_token.json"

def main():
    try:
        if VERBOSE:
            print('Configuring OAuth...')
        oauth_config = {
            'APP_LOGIN': CLIENT_ID,
            'APP_PASSWORD': CLIENT_SECRET
        }
    except Exception as err:
        raise SystemExit(f"oauth_config error: {err}")

    try:
        api = DnsApi(oauth_config)
    except Exception as err:
        raise SystemExit(f"DnsApi error: {err}")

    if os.path.exists(TOKEN_FILE):
        mtime = os.path.getmtime(TOKEN_FILE)
        with open(TOKEN_FILE, 'r') as file:
            content = json.load(file)
            expires_in = int(content['expires_in'])
        if mtime + expires_in <= time.time():
            if VERBOSE:
                print('Token expired. Refreshing...')
            os.remove(TOKEN_FILE)

    try:
        if VERBOSE:
            print('Authorize API...')
        api.authorize(
            username = USERNAME,
            password = PASSWORD,
            token_filename = TOKEN_FILE
        )
    except Exception as err:
        if VERBOSE:
            print(f"api.authorize: {err}")
        raise SystemExit(f"api.authorize: {err}")

    if "*" in CERTBOT_DOMAIN:
        domain = CERTBOT_DOMAIN.split(".")[1:]
        domain = ".".join(domain)
    else:
        domain = CERTBOT_DOMAIN

    domain_object = get_tld(domain, fix_protocol=True, as_object=True)
    main_domain = f"{domain_object.domain}.{domain_object}"

    try:
        if domain_object.subdomain:
            reg_domain = f"{domain_object.subdomain}"
            query_domain = f"{domain_object.subdomain}.{domain_object.domain}.{domain_object}"
            record = TXTRecord(name = f"_acme-challenge.{reg_domain}", txt = CERTBOT_VALIDATION, ttl = TTL)
        else:
            query_domain = f"{domain_object.domain}.{domain_object}"
            record = TXTRecord(name = "_acme-challenge", txt = CERTBOT_VALIDATION, ttl = TTL)
        api.add_record(record, SERVICE_ID, main_domain)
        api.commit(SERVICE_ID, main_domain)
    except Exception as err:
        raise SystemExit(f"api.add_record error: {err}")

    if VERBOSE:
        verb = True
    while True:
        rdata = Func.checkTXTRecord(DNS_SERVER, query_domain, verbose=verb)
        if rdata:
            break
        time.sleep(10)
    if CERTBOT_REMAINING == 0:
        if VERBOSE:
            print(f'Sleep for {SLEEP} seconds...')
        time.sleep(SLEEP)

if __name__ == '__main__':
    main()