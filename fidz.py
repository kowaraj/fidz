#!/usr/bin/python

'''
TODO:

  - Stay alive after a loss of the connection to UH.
  

VERSION:

  - 2019.02.06

    Add an alert by SMS (via pcposp0 email server).
  
  - 2019.02.05

    Add a regex to the command to find the files on the remote host (already synchronized files).
    Otherwise, it finds a partially trasnferred file and throws an error (to be understood why).


INVARIANTS :

  - L1: list of files on the LOCAL host
   =self.__get_fn_list_local()

 - L2: list of files that have already been synch'ed:
   (and not yet deleted from remote due to >=STORAGE_SIZE)
   =self.__get_fn_list_remote()

 - L3: list of files on the LOCAL host limited by STORAGE_SIZE (most recent)
 - L4: list of files to be synchronized as a batch (BATCH_SIZE) (oldest)
 - L5: list of files to be deleted from remove (keep only STORAGE_SIZE)
 
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


	

