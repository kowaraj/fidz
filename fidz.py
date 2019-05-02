#!/usr/bin/python

'''
TODO:
  - Fix move-or-delete to delete incomplete files if any
  - Fix move-or-delete to move when no folder created yet

VERSION:

    2019.03.06

  - Add controller_pull module (to pull data from remote instead of push).
  - Add input argument for config_channel name
  
    2019.02.17

    BUGFIX: find threw an error (due to: fidz executed while old_frames were being deleted from the server)

  
    2019.02.14

  - Changed the mail server to cernmx.cern.ch:25
  - Removed old-never-used dumper.py file and reference to it
  - Add global try-catch to notify with alarm
  
    2019.02.06

  - Add an alert by SMS (via pcposp0 email server).
  
    2019.02.05

  - Add a regex to the command to find the files on the remote host (already synchronized files).
    Otherwise, it finds a partially trasnferred file and throws an error (to be understood why).


INVARIANTS :

  - L1: list of files on the LOCAL host
    see: Controller.__get_fn_list_local()

  - L2: list of files that have already been synch'ed:
    (and not yet deleted from remote due to >=STORAGE_SIZE)
    see: Controller.__get_fn_list_remote()

  - L3: list of files on the LOCAL host limited by STORAGE_SIZE (most recent)
  - L4: list of files to be synchronized as a batch (BATCH_SIZE) (oldest)
  - L5: list of files to be deleted from remove (keep only STORAGE_SIZE)
 

INVARIANTS for PULL-controller:

  - L1: list of files on REMOTE which we are still interested
    see: Controller.__get_fn_list_remote()

  - L2: list of files on the LOCAL host (already rsynch'ed)
    see: Controller.__get_fn_list_local()
    
  - L3: list of files to be synchronized as a batch (BATCH_SIZE)

  '''


import os
import sys
from subprocess import call, Popen, PIPE, STDOUT
from time import sleep

import controller
import controller_pull
from logger import Logger
from config import Config

      
# 0. check arguments
config_channel = "default_channel"

print "Arguments provided:"
for a in sys.argv:
    print "    : ", a
if len(sys.argv) == 2:
    config_channel = sys.argv[1]
    print "Argument given: config_channel = ", config_channel #pcposc1_from_localhost

# 1. check the user is data

import getpass
if getpass.getuser() != 'ams':
	print "switch user to ams"
	exit(0)

# 2. config

logger = Logger()

config = Config(config_channel).get()
logger.log(str(config))

if config.mode == "push":
    c = controller.Controller(logger, config)
elif config.mode == "pull":
    c = controller_pull.Controller(logger, config)
else:
    print "Unknown mode"
    exit(0)


# 3. run
    
try:
    c.run()
except Exception as e:
    print "Exception: " + e
    c.alarm("["+config_channel+"] "+str(e))
    raise
except:
    print "Exception."
    c.alarm("["+config_channel+"] Unknown problem. Goodbye.")
    raise

    
# The End.


	

