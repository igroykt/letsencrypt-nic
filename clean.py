import os
import sys
import json
import time
from configparser import ConfigParser

from nic_api import DnsApi
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
CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')
VERBOSE = os.getenv('VERBOSE')
TOKEN_FILE = script_dir + os.sep + "nic_token.json"


def main():
    try:
        api = DnsApi(CLIENT_ID, CLIENT_SECRET)
    except Exception as err:
        raise SystemExit(f"DnsApi error: {err}")

    try:
        if VERBOSE:
            print('Authorize API...')
        api.get_token(username = USERNAME, password = PASSWORD)
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
        else:
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


if __name__ == '__main__':
    main()