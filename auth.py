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

def domainTail(domain):
    domain = domain.split(".")
    domain = domain[:len(domain)-2]
    tmp = []
    for level in domain:
        if "*" not in level:
            tmp.append(level)
    domain = '.'.join(tmp)
    if domain:
        return domain
    return False

try:
    if len(CERTBOT_DOMAIN.split(".")) > 2:
        domain_tail = domainTail(CERTBOT_DOMAIN)
        record = TXTRecord(name = f"_acme-challenge.{domain_tail}", txt = CERTBOT_VALIDATION, ttl = TTL)
    else:
        record = TXTRecord(name = "_acme-challenge", txt = CERTBOT_VALIDATION, ttl = TTL)
except Exception as err:
    logging.error(f"TXTRecord error: {err}")
    os.remove(TOKEN_FILE)
    api.authorize(
        username = USERNAME,
        password = PASSWORD,
        token_filename = TOKEN_FILE
    )
    if len(CERTBOT_DOMAIN.split(".")) > 2:
        domain_tail = domainTail(CERTBOT_DOMAIN)
        record = TXTRecord(name = f"_acme-challenge.{domain_tail}", txt = CERTBOT_VALIDATION, ttl = TTL)
    else:
        record = TXTRecord(name = "_acme-challenge", txt = CERTBOT_VALIDATION, ttl = TTL)

try:
    if len(CERTBOT_DOMAIN.split(".")) > 2:
        main_domain = mainDomainTail(CERTBOT_DOMAIN)
        api.add_record(record, SERVICE_ID, main_domain)
    else:
        api.add_record(record, SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    logging.error(f"api.add_record error: {err}")

try:
    if len(CERTBOT_DOMAIN.split(".")) > 2:
        main_domain = mainDomainTail(CERTBOT_DOMAIN)
        api.commit(SERVICE_ID, main_domain)
    else:
        api.commit(SERVICE_ID, CERTBOT_DOMAIN)
except Exception as err:
    logging.error(f"api.commit error: {err}")

def getDnsList():
    dns_list = []
    resolver = dns.resolver.Resolver(configure = False)
    resolver.nameservers = ['8.8.8.8']
    answers = dns.resolver.resolve(main_domain, 'NS')
    for rdata in answers:
        rdata = str(rdata)[:-1]
        dns_list.append(rdata)
    dns_list.sort()
    return dns_list

def genDnsList(dns_list):
    new_dns_list = []
    resolver = dns.resolver.Resolver(configure = False)
    for item in dns_list:
        answers = dns.resolver.resolve(item, 'A')
        for rdata in answers:
            rdata = str(rdata)
            new_dns_list.append(rdata)
    return new_dns_list

def resolveDomain(dns_list):
    time.sleep(SLEEP)
    resolver = dns.resolver.Resolver(configure = False)
    i = 1
    dns_size = len(dns_list)
    for server in dns_list:
        resolver.nameservers = [server]
        try:
            resolver.resolve(f'_acme-challenge.{CERTBOT_DOMAIN}', 'TXT')
            return True
        except dns.resolver.NXDOMAIN as err:
            if i >= dns_size:
                return False
            i += 1
            pass

if len(CERTBOT_DOMAIN.split(".")) > 2:
    main_domain = mainDomainTail(CERTBOT_DOMAIN)
else:
    main_domain = CERTBOT_DOMAIN
dns_list = getDnsList()
dns_ip_list = genDnsList(dns_list)
is_resolved = resolveDomain(dns_ip_list)
if not is_resolved:
    logging.error(f"resolver.resolve error: Could not find validation TXT record for {CERTBOT_DOMAIN}")
    raise Exception(f"resolver.resolve error: Could not find validation TXT record {CERTBOT_DOMAIN}")