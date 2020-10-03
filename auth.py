import os
import sys
from nic_api import DnsApi
from nic_api.models import TXTRecord
from configparser import ConfigParser
import time
import logging
import dns.resolver

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
TTL = config.get('GENERAL', 'TTL')
SLEEP = int(config.get('GENERAL', 'SLEEP'))
CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')
CERTBOT_VALIDATION = os.getenv('CERTBOT_VALIDATION')

LOG_FILE = script_dir + "/auth.log"
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
    record = TXTRecord(name = f"_acme-challenge.{CERTBOT_DOMAIN}.", txt = CERTBOT_VALIDATION, ttl = TTL)
except Exception as err:
    logging.error(f"TXTRecord error: {err}")
    os.remove(TOKEN_FILE)
    api.authorize(
        username = USERNAME,
        password = PASSWORD,
        token_filename = TOKEN_FILE
    )
    record = TXTRecord(name = f"_acme-challenge.{CERTBOT_DOMAIN}.", txt = CERTBOT_VALIDATION, ttl = TTL)

try:
    api.add_record(record, SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    logging.error(f"api.add_record error: {err}")

try:
    api.commit(SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    logging.error(f"api.commit error: {err}")

resolver = dns.resolver.Resolver(configure = False)
resolver.nameservers = ['8.8.8.8']
while True:
    try:
        time.sleep(SLEEP)
        resolver.resolve(f'_acme-challenge.{CERTBOT_DOMAIN}', 'txt')
        break
    except Exception:
        pass
