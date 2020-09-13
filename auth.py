import os
import sys
from nic_api import DnsApi
from nic_api.models import TXTRecord
from configparser import ConfigParser
import ast
import time

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
TTL = config.get('GENERAL', 'TTL')
SLEEP = int(config.get('GENERAL', 'SLEEP'))
CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')
CERTBOT_VALIDATION = os.getenv('CERTBOT_VALIDATION')

oauth_config = {
    'APP_LOGIN': CLIENT_ID,
    'APP_PASSWORD': CLIENT_SECRET
}
try:
    api = DnsApi(oauth_config)
except Exception as err:
    sys.exit(f"OAuth authentication: {err}")

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
    os.remove(TOKEN_FILE)
    api.authorize(
        username = USERNAME,
        password = PASSWORD,
        token_filename = TOKEN_FILE
    )

try:
    print("Creating TXT record...")
    record = TXTRecord(name = f"_acme-challenge.{CERTBOT_DOMAIN}.", txt = CERTBOT_VALIDATION, ttl = TTL)
except Exception:
    os.remove(TOKEN_FILE)
    record = TXTRecord(name = f"_acme-challenge.{CERTBOT_DOMAIN}.", txt = CERTBOT_VALIDATION, ttl = TTL)

api.add_record(record, SERVICE_ID, CERTBOT_DOMAIN)
api.commit(SERVICE_ID, CERTBOT_DOMAIN)

print(f"Sleep for {SLEEP} seconds...")
time.sleep(SLEEP)
print("Done!")
