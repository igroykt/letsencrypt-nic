import os, sys
from nic_api import DnsApi
from nic_api.models import TXTRecord
from configparser import ConfigParser
import time
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
RETRIES = int(config.get('GENERAL', 'RETRIES'))
CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')
CERTBOT_VALIDATION = os.getenv('CERTBOT_VALIDATION')
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

    if not os.path.exists(TOKEN_FILE):
        open(TOKEN_FILE, 'w').close()

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
            print('Authorize API...')
        os.remove(TOKEN_FILE)
        api.authorize(
            username = USERNAME,
            password = PASSWORD,
            token_filename = TOKEN_FILE
        )

    if "*" in CERTBOT_DOMAIN:
        domain = CERTBOT_DOMAIN.split(".")[1:]
        domain = ".".join(domain)
    else:
        domain = CERTBOT_DOMAIN

    domain_object = get_tld(domain, fix_protocol=True, as_object=True)
    main_domain = f"{domain_object.domain}.{domain_object}"

    try:
        if VERBOSE:
            print('Create TXT record...')
        if domain_object.subdomain:
            reg_domain = f"{domain_object.subdomain}"
            query_domain = f"{domain_object.subdomain}.{domain_object.domain}.{domain_object}"
            record = TXTRecord(name = f"_acme-challenge.{reg_domain}", txt = CERTBOT_VALIDATION, ttl = TTL)
        else:
            query_domain = f"{domain_object.domain}.{domain_object}"
            record = TXTRecord(name = "_acme-challenge", txt = CERTBOT_VALIDATION, ttl = TTL)
        api.add_record(record, SERVICE_ID, main_domain)
        api.commit(SERVICE_ID, main_domain)
        if VERBOSE:
            print('All changes are commited!')
    except Exception as err:
        raise SystemExit(f"api.add_record error: {err}")

    i = 1
    while i <= RETRIES:
        try:
            if VERBOSE:
                print('Check TXT record...')
            Func.checkTXTRecord(DNS_SERVER, query_domain)
            break
        except Exception:
            i += 1
            if VERBOSE:
                print(f'Attempt: {i} of {RETRIES} and TXT record not found! Sleep for {SLEEP} seconds...')
            time.sleep(SLEEP)
        finally:
            if i >= RETRIES:
                raise SystemExit(f"resolver.resolve error: Could not find validation TXT record {CERTBOT_DOMAIN}")


if __name__ == '__main__':
    main()