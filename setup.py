import sys
import os
import re
import json
from hashlib import sha256
from cpuinfo import get_cpu_info
from cryptography.fernet import Fernet
from cx_Freeze import setup, Executable

# Generate crypto key
key = Fernet.generate_key().decode()

# Generate CPU fingerprint
def make_cpu_fingerprint():
    cpuinfo = get_cpu_info()
    cpuinfo.pop('python_version', None)
    fingerprint = sha256(json.dumps(cpuinfo).encode('utf-8')).hexdigest()
    return fingerprint

# Retrieve environment variables
use_fingerprint = os.getenv('LNIC_USE_FINGERPRINT')
use_passphrase = os.getenv('LNIC_USE_PASSPHRASE')

# Generate fingerprint and passphrase if needed
fprint = make_cpu_fingerprint() if use_fingerprint else None
if use_passphrase:
    if len(use_passphrase) < 6:
        sys.exit('Passphrase must be 6+ symbols.')
    pphrase = sha256(use_passphrase.encode('utf-8')).hexdigest()

# Update entry point
def update_entry_point(file_path):
    with open(file_path, 'r') as file:
        file_content = file.readlines()

    new_content = ''
    for line in file_content:
        if 'ENC_KEY =' in line:
            line = f'ENC_KEY = \'{key}\'\n'
        new_content += line
        if use_fingerprint and 'CPU_FINGER =' in line:
            new_content += f'CPU_FINGER = \'{fprint}\'\n'
        if use_passphrase and 'PASSPHRASE =' in line:
            new_content += f'PASSPHRASE = \'{pphrase}\'\n'

    with open(file_path, 'w') as file:
        file.write(new_content)

update_entry_point('main.py')

# Define build options based on Python version
build_exe_options = {
    "packages": ["nic_api", "dns.resolver", "tld", "cryptography", "argparse", "slack_webhook", "telegram"]
}
if sys.version_info < (3, 8):
    build_exe_options["build_exe"] = "build"

# Setup the build
setup(
    name="letsencrypt-nic",
    version="1.4",
    description="letsencrypt-nic",
    options={"build_exe": build_exe_options},
    executables=[
        Executable("auth.py"),
        Executable("clean.py"),
        Executable("main.py")
    ]
)

print('Compile completed!')
