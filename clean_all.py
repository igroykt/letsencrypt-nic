import os
import sys
from nic_api import DnsApi
from nic_api.models import TXTRecord
from configparser import ConfigParser
import logging

script_dir = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser()
try:
    config.read(script_dir + "/config.ini")
except Exception as err:
    sys.exit(f"Config parse: {err}")

USERNAME = os.getenv('NICUSER')
PASSWORD = os.getenv('NICPASS')
CLIENT_ID = os.getenv('NICID')
CLIENT_SECRET = os.getenv('NICSECRET')
SERVICE_ID = config.get('GENERAL', 'SERVICE_ID')
CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')

LOG_FILE = script_dir + "/clean_all.log"
TOKEN_FILE = script_dir + "/nic_token.json"

if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

logging.basicConfig(format = '%(levelname)-8s [%(asctime)s] %(message)s', level = logging.ERROR, filename = LOG_FILE)

try:
    oauth_config = {
	'APP_LOGIN': CLIENT_ID,
	'APP_PASSWORD': CLIENT_SECRET
    }
except Exception as err:
    logging.error(f"oauth_config error: {err}")

try:
    api = DnsApi(oauth_config)
except Exception as err:
    logging.error(f"DnsApi error: {err}")

if not os.path.exists(TOKEN_FILE):
    open(TOKEN_FILE, 'w').close()

try:
    api.authorize(
	username = USERNAME,
	password = PASSWORD,
	token_filename = TOKEN_FILE
    )
except Exception as err:
    logging.error(f"api.authorize error: {err}")
    os.remove(TOKEN_FILE)
    api.authorize(
	username = USERNAME,
	password = PASSWORD,
	token_filename = TOKEN_FILE
    )

try:
    records = api.records(SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    logging.error(f"api.records error: {err}")
    os.remove(TOKEN_FILE)
    api.authorize(
        username = USERNAME,
        password = PASSWORD,
        token_filename = TOKEN_FILE
    )
    records = api.records(SERVICE_ID, CERTBOT_DOMAIN)

def findTXTID(data):
    ids = []
    for record in data:
        # skip all records except TXT
        if type(record) is TXTRecord:
            # convert TXTRecord type to string
            record = repr(record)
            # convert string to dictionary
            record = eval(record)
            if "_acme-challenge" in record['name']:
                #return record['id']
                ids.append(record['id'])
    return ids

try:
    records_id = findTXTID(records)
except Exception as err:
    logging.error(f"findTXTID error: {err}")

try:
    for id in records_id:
        api.delete_record(id, SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    logging.error(f"api.delete error: {err}")

try:
    api.commit(SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    logging.error(f"api.commit error: {err}")
