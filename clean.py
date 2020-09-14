import os
import sys
from nic_api import DnsApi
from nic_api.models import TXTRecord
from configparser import ConfigParser
import logging

config = ConfigParser()
try:
    config.read('config.ini')
except Exception as err:
    sys.exit(f"Config parse: {err}")

USERNAME = os.getenv('NICUSER')
PASSWORD = os.getenv('NICPASS')
CLIENT_ID = os.getenv('NICID')
CLIENT_SECRET = os.getenv('NICSECRET')
TOKEN_FILE = config.get('GENERAL', 'TOKEN_FILE')
SERVICE_ID = config.get('GENERAL', 'SERVICE_ID')
LOG_FILE = config.get('GENERAL', 'LOG_FILE')
CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')

logging.basicConfig(format = '%(levelname)-8s [%(asctime)s] %(message)s', level = logging.ERROR, filename = LOG_FILE)

try:
	oauth_config = {
    		'APP_LOGIN': CLIENT_ID,
    		'APP_PASSWORD': CLIENT_SECRET
	}
except Exception as err:
	logging.error(f"clean.py - oauth_config error: {err}")

try:
    api = DnsApi(oauth_config)
except Exception as err:
    logging.error(f"clean.py - DnsApi error: {err}")

if not os.path.exists(TOKEN_FILE):
    open(TOKEN_FILE, 'w').close()

try:
	api.authorize(
        	username = USERNAME,
        	password = PASSWORD,
        	token_filename = TOKEN_FILE
    	)
except Exception as err:
    	print(f"API authorize: {err}")
    	print(f"Token refresh...")
	logging.error(f"clean.py - api.authorize error: {err}")
    	os.remove(TOKEN_FILE)
    	api.authorize(
        	username = USERNAME,
        	password = PASSWORD,
        	token_filename = TOKEN_FILE
    	)

try:
    	print("Retrieving DNS records...")
    	records = api.records(SERVICE_ID, CERTBOT_DOMAIN)
except Exception:
	logging.error(f"clean.py - api.records error: {err}")
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
            if f"_acme-challenge" in record['name']:
                ids.append(record['id'])
    return ids

print("Searching TXT record ID...")
record_id = findTXTID(records)
for id in record_id:
	try:
    		api.delete_record(id, SERVICE_ID, CERTBOT_DOMAIN)
	except Exception as err:
		logging.error(f"clean.py - api.delete error: {err}")

try:
	api.commit(SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
	logging.error(f"clean.py - api.commit error: {err}")

print("Done!")