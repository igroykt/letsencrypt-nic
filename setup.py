import sys
import os
import re

from cx_Freeze import setup, Executable
import cryptography
from cryptography.fernet import Fernet
from cpuinfo import get_cpu_info
from hashlib import sha256
import json

# generate crypto key
key = Fernet.generate_key()

# generate cpu fingerprint
def make_cpu_fingerprint():
    cpuinfo = get_cpu_info()
    del cpuinfo['python_version']
    fingerprint = sha256(json.dumps(cpuinfo).encode('utf-8')).hexdigest()
    return fingerprint

if os.getenv('LNIC_USE_FINGERPRINT'):
    fprint = make_cpu_fingerprint()

if os.getenv('LNIC_USE_PASSPHRASE'):
    if len(os.getenv('LNIC_USE_PASSPHRASE')) < 6:
        sys.exit('Passphrase must be 6+ symbols.')
    tmp_phrase = os.getenv('LNIC_USE_PASSPHRASE')
    pphrase = sha256(tmp_phrase.encode('utf-8')).hexdigest()

# update entry point
newFile = ''
with open('main.py', 'r') as file:
    fileContent = file.readlines()
    for line in fileContent:
        if 'ENC_KEY =' in line:
            line = f'ENC_KEY = \'{key.decode()}\'\n'
        newFile += line
        if os.getenv('LNIC_USE_FINGERPRINT'):
            if 'CPU_FINGER =' in line:
                line = f'CPU_FINGER = \'{fprint}\'\n'
            newFile += line
        if os.getenv('LNIC_USE_PASSPHRASE'):
            if 'PASSPHRASE =' in line:
                line = f'PASSPHRASE = \'{pphrase}\'\n'
            newFile += line
writeFile = open('main.py', 'w')
writeFile.write(newFile)
writeFile.close()

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["nic_api", "dns.resolver", "tld", "cryptography", "argparse", "slack_webhook", "telegram"],
    "build_exe": "build"
}

setup(
    name = "letsencrypt-nic",
    version = "1.4",
    description = "letsencrypt-nic",
    options = {"build_exe": build_exe_options},
    executables = [Executable("auth.py"), Executable("clean.py"), Executable("main.py")]
)

print('Compile completed!')