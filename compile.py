#!/usr/bin/python3

import py_compile
import subprocess
import shutil
import click
import glob
import sys
import os

if click.confirm('Do you want to continue?', default = False):
	pass
else:
	sys.exit()

def list2str(list):
	string = ""
	return (string.join(list))

print('Compiling Python...')
if os.path.isdir('./__pycache__'):
	shutil.rmtree('./__pycache__')
py_compile.compile('auth.py')
authbin = glob.glob('./__pycache__/*.pyc')
authbin = list2str(authbin)
shutil.move(authbin, './auth.pyc')
os.system('chmod +x ./auth.pyc')

py_compile.compile('clean.py')
cleanbin = glob.glob('./__pycache__/*.pyc')
cleanbin = list2str(cleanbin)
shutil.move(cleanbin, './clean.pyc')
os.system('chmod +x ./clean.pyc')

if os.path.isdir('./__pycache__'):
        shutil.rmtree('./__pycache__')

print('Compiling Golang...')
try:
	os.system('go build main.go')
except Exception as e:
	sys.exit(f'Compile error: {e}')

sys.exit('Compile completed!')
