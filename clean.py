import os, sys
from nic_api import DnsApi
from configparser import ConfigParser
from func import Func
import json
import time

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
CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')
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

    main_domain = Func.mainDomainTail(CERTBOT_DOMAIN)

    try:
        if VERBOSE:
            print('Extract all DNS records...')
        records = api.records(SERVICE_ID, main_domain)
    except Exception as err:
        raise SystemExit(f"api.records error: {err}")

    try:
        if VERBOSE:
            print('Search for TXT records...')
        records_id = Func.NIC_findTXTID(records)
        for id in records_id:
            api.delete_record(id, SERVICE_ID, main_domain)
        api.commit(SERVICE_ID, main_domain)
    except Exception as err:
        raise SystemExit(f"api.delete_record error: {err}")

    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)

if __name__ == '__main__':
    main()