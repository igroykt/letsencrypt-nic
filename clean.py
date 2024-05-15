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


def create_api_client():
    """Создает и возвращает объект DnsApi."""
    try:
        api = DnsApi(app_login=CLIENT_ID, app_password=CLIENT_SECRET)
        return api
    except Exception as err:
        raise SystemExit(f"DnsApi error: {err}")


def obtain_token(api):
    """Получает токен от DNS API."""
    try:
        if VERBOSE:
            print('Obtain token...')
        api.get_token(username=USERNAME, password=PASSWORD)
    except Exception as err:
        if VERBOSE:
            print(f"api.get_token: {err}")
        raise SystemExit(f"api.get_token: {err}")


def extract_dns_records(api, main_domain):
    """Извлекает все DNS записи для домена."""
    try:
        if VERBOSE:
            print('Extract all DNS records...')
        records = api.records(SERVICE_ID, main_domain)
        return records
    except Exception as err:
        raise SystemExit(f"api.records error: {err}")


def delete_txt_records(api, records, main_domain):
    """Удаляет все TXT записи для домена."""
    try:
        if VERBOSE:
            print('Search for TXT records...')
        records_id = Func.NIC_findTXTID(records)
        for record_id in records_id:
            api.delete_record(record_id, SERVICE_ID, main_domain)
        api.commit(SERVICE_ID, main_domain)
    except Exception as err:
        raise SystemExit(f"api.delete_record error: {err}")


def main():
    api = create_api_client()
    obtain_token(api)

    main_domain = Func.mainDomainTail(CERTBOT_DOMAIN)
    records = extract_dns_records(api, main_domain)
    delete_txt_records(api, records, main_domain)


if __name__ == '__main__':
    main()
