import os, sys
from nic_api import DnsApi
from nic_api.models import TXTRecord
from configparser import ConfigParser


script_dir = os.path.dirname(os.path.realpath(__file__))


config = ConfigParser()


try:
    config.read(script_dir + "/config.ini")
except Exception as err:
    raise SystemExit(f"Config parse: {err}")


USERNAME = os.getenv('NICUSER')
PASSWORD = os.getenv('NICPASS')
CLIENT_ID = os.getenv('NICID')
CLIENT_SECRET = os.getenv('NICSECRET')
SERVICE_ID = config.get('GENERAL', 'SERVICE_ID')
CERTBOT_DOMAIN = os.getenv('CERTBOT_DOMAIN')
TOKEN_FILE = script_dir + "/nic_token.json"


try:
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
    api.authorize(
	    username = USERNAME,
	    password = PASSWORD,
	    token_filename = TOKEN_FILE
    )
except Exception as err:
    os.remove(TOKEN_FILE)
    api.authorize(
	    username = USERNAME,
	    password = PASSWORD,
	    token_filename = TOKEN_FILE
    )


def mainDomainTail(domain):
    domain = domain.split(".")
    domain = domain[len(domain)-2:]
    tmp = []
    for level in domain:
        if "*" not in level:
            tmp.append(level)
    domain = '.'.join(tmp)
    if domain:
        return domain
    return False


CERTBOT_DOMAIN = mainDomainTail(CERTBOT_DOMAIN)


try:
    records = api.records(SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    raise SystemExit(f"api.records error: {err}")


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
                ids.append(record['id'])
    return ids


try:
    records_id = findTXTID(records)
    for id in records_id:
        api.delete_record(id, SERVICE_ID, CERTBOT_DOMAIN)
    api.commit(SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    raise SystemExit(f"api.delete_record error: {err}")