import sys, os, re
from cx_Freeze import setup, Executable
import cryptography
from cryptography.fernet import Fernet

# generate crypto key
key = Fernet.generate_key()

newFile = ''
with open('main.py', 'r') as file:
    fileContent = file.readlines()
    for line in fileContent:
        if 'ENC_KEY =' in line:
            line = f'ENC_KEY = \'{key.decode()}\'\n'
        newFile += line
writeFile = open('main.py', 'w')
writeFile.write(newFile)
writeFile.close()

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["os", "sys", "nic_api", "configparser", "time", "dns.resolver", "tld", "cryptography", "argparse", "slack_webhook", "telegram"],
    #"include_files": ["func"],
    "build_exe": "build"
}

setup(
    name = "letsencrypt-nic",
    version = "1.2",
    description = "letsencrypt-nic",
    options = {"build_exe": build_exe_options},
    executables = [Executable("auth.py"), Executable("clean.py"), Executable("main.py")]
)

print('Compile completed!')