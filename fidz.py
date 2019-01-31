#!/usr/bin/python

'''
# Documentation:
## Functionality
- Keep a 'log.rsynced' file on the REMOTE side. Update after every successful transfer.
  Read this file to obtain the list of the files which have been transferred.
- 
## Usage
- no arguments for now
'''

import os
import sys
from subprocess import call, Popen, PIPE, STDOUT
from time import sleep

import controller

      
# 0. check arguments

print "Arguments provided:"
for a in sys.argv:
	print "    : ", a
if len(sys.argv) != 1:
	print "No arguments expected"
	exit(0)

# 1. check the user is data

import getpass
if getpass.getuser() != 'ams':
	print "switch user to ams"
	exit(0)


# 2. run
	
c = controller.Controller()
c.log("test log")
c.run()




# The End.


	

