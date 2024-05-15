import os
import sys
from configparser import ConfigParser
import time
import json

from nic_api import DnsApi
from nic_api.models import TXTRecord
from tld import get_tld
from func import Func

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


def obtain_token(api):
    """Obtains a token from the DNS API."""
    if VERBOSE:
        print('Obtain token...')
    api.get_token(username=USERNAME, password=PASSWORD)


def process_domain(certbot_domain):
    """Processes the domain to extract the main domain and query domain."""
    if "*" in certbot_domain:
        domain = certbot_domain.split(".")[1:]
        domain = ".".join(domain)
    else:
        domain = certbot_domain

    domain_object = get_tld(domain, fix_protocol=True, as_object=True)
    main_domain = f"{domain_object.domain}.{domain_object}"
    
    if domain_object.subdomain:
        reg_domain = f"{domain_object.subdomain}"
        query_domain = f"{domain_object.subdomain}.{domain_object.domain}.{domain_object}"
        record = TXTRecord(name=f"_acme-challenge.{reg_domain}", txt=CERTBOT_VALIDATION, ttl=TTL)
    else:
        query_domain = f"{domain_object.domain}.{domain_object}"
        record = TXTRecord(name="_acme-challenge", txt=CERTBOT_VALIDATION, ttl=TTL)
    
    return main_domain, query_domain, record


def add_dns_record(api, record, main_domain):
    """Adds a DNS TXT record and commits the changes."""
    api.add_record(record, SERVICE_ID, main_domain)
    api.commit(SERVICE_ID, main_domain)


def check_txt_record(query_domain):
    """Checks for the presence of the DNS TXT record."""
    while True:
        rdata = Func.checkTXTRecord(DNS_SERVER, query_domain, test=False, verbose=VERBOSE)
        if rdata:
            break
        time.sleep(10)


def main():
    try:
        api = DnsApi(app_login=CLIENT_ID, app_password=CLIENT_SECRET)
    except Exception as err:
        raise SystemExit(f"DnsApi error: {err}")

    try:
        obtain_token(api)
    except Exception as err:
        if VERBOSE:
            print(f"api.get_token: {err}")
        raise SystemExit(f"api.get_token: {err}")

    try:
        main_domain, query_domain, record = process_domain(CERTBOT_DOMAIN)
        add_dns_record(api, record, main_domain)
    except Exception as err:
        raise SystemExit(f"api.add_record error: {err}")

    check_txt_record(query_domain)

    if CERTBOT_REMAINING == 0:
        if VERBOSE:
            print(f'Sleep for {SLEEP} seconds...')
        time.sleep(SLEEP)


if __name__ == '__main__':
    main()

