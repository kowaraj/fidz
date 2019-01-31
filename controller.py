import os
import sys
from subprocess import PIPE, STDOUT
import subprocess

from time import sleep
import datetime
from logger import Logger
from dumper import Dumper

LOG_FILENAME = "fidz_log.rsync"
REM_HOST = "uhams02a.phys.hawaii.edu"
REM_PATH = "/home/cern/amscern/cern_to_hawaii/"
LOC_PATH = "/home/ams/src/test_rsync/data/FRAMES/SCIBPB/RT/"
LOC_FILE = "3770/000"

STORAGE_SIZE = 10 # number of files to keep on REMOTE
BATCH_SIZE = 2 # number of files to rsync at once

class Controller():

    def __init__(self):
        '''
        Invariants :
        - L1: list of files on the LOCAL host
          = self.__get_L1()
        - L2: list of files that have already been synch'ed:
          (files which are not in L1 will be removed from L2)
          = 
        - L3: list of files on the LOCAL host limited by STORAGE_SIZE (most recent)
        - L4: list of files to be synchronized as a batch (BATCH_SIZE) (oldest)
        '''
        
        self.__L2 = []
        
        self.__check_if_process_is_running()
        self.__logger = Logger()
        self.dumper = Dumper(self.__logger)

    def __check_if_process_is_running(self):
        '''
        Create a lock (to aviod running more than one instance of the script)
        '''
        try:
            import socket
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	    ## Create an abstract socket, by prefixing it with null. 
            s.bind( '\0postconnect_gateway_notify_lock') 
            print "Process is NOT running " 
            
        except socket.error as e:
            error_code = e.args[0]
            error_string = e.args[1]
            print "Process already running (%d:%s ). Exiting" % ( error_code, error_string) 
            exit(0)
        
    def log(self, msg):
        self.__logger.log(msg+ '\n')

    def logerror(self, msg):
        self.__logger.logerror(msg+ '\n')

    def run(self):
        self.log("run: going into an infinite loop...")

        fn_list_synched = self.__get_fn_list_remote()

        while (True):
            self.log("\n"+str(datetime.datetime.now()))
            
            fn_list_local = self.__get_L1()
            self.log("L1 : " + str(fn_list_local))

            self.log("L2 : " + str(fn_list_synched))

            fn_list_local_recent = fn_list_local[-STORAGE_SIZE:]
            self.log("L3 : " + str(fn_list_local_recent))

            fn_list_to_sync = [x for x in fn_list_local_recent if x not in fn_list_synched]
            fn_list_to_sync_b = fn_list_to_sync[:BATCH_SIZE]
            self.log("L4 : " + str(fn_list_to_sync_b))
        
            self.__sync(fn_list_to_sync_b)

            fn_list_synched += fn_list_to_sync_b
            self.log("L2': " + str(fn_list_synched))
            
            self.log("run: The end.")
            #exit(0)
            sleep(10)

    def __get_fn_list_remote(self):

        # ssh command:
        KEY = "-i /home/ams/.ssh/ams_fcern2hawaii"
        PORT = "-p 25852"
        USER = "-l amscern"
        HOST = "uhams02a.phys.hawaii.edu"
        CMD = "find " + REM_PATH + " -type f -printf \'%P \'"

        ssh_command = "ssh -q" + ' ' + KEY + ' ' + PORT + ' ' + USER + ' ' + HOST + ' \"' + CMD + '\"'
        self.log("ssh command: " + ssh_command)
        #return ["3770/000 3770/001"]
        
        p = subprocess.Popen(ssh_command, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        
        # check return code
        rc = p.returncode
        if rc != 0:
            self.logerror("Error in __get_fn_list_remote, return code = " + str(rc))
            exit(0)

        # check error output
        if len(err) != 0:
            self.log("error output: " + err)
            self.logerror("Error in __get_fn_list_remote, error len !=0 ")
            exit(0)


        # check output
        self.log("output: " + output)
        fn_list = output.rstrip(' ').split(' ')
        fn_list.sort()
        return fn_list

    
    def __get_L1(self):
        '''
        Return:
        List of filename to be copied to REMOTE, the oldest files (limited by STORE_SIZE)
        which has not yet been copied.
        Size of the list is BATCH_SIZE. 
        
        Return example:
        ["3770/000 3770/001"]

        Command:
        find  ./data/FRAMES/SCIBPB/RT/ -type f -printf "%P\n"
          : -type f       = not to print folders
          : -printf '%P'  = to print file name with the path removed
          :         '%P ' = to insert a 'space'
        '''
        
        cmd = "find " + LOC_PATH + " -type f -printf '%P '"
        p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        output, err = p.communicate()
        
        # check return code
        rc = p.returncode
        if rc != 0:
            self.logerror("Error in __get_fn_list, return code = " + str(rc))
            exit(0)

        # check error output
        if len(err) != 0:
            self.log("error output: " + err)
            self.logerror("Error in __get_fn_list, error len !=0 ")
            exit(0)

        # check output
        fn_list_local = output.rstrip(' ').split(' ')
        fn_list_local.sort()
        return fn_list_local
    
    def __sync(self, fn_list):
        for fn in fn_list:
            self.log("copying: " + fn)
            cmd = "rsync -Rpogt " + LOC_PATH + './' + fn + " " + REM_HOST + ":" + REM_PATH +  " " + '-e "ssh -i /home/ams/.ssh/ams_fcern2hawaii -p 25852 -l amscern"'
            self.__call(cmd)
            self.log("copying: done.")
        
    def __call(self, cmd):
        self.log(" call: " + cmd)
        subprocess.call(cmd, shell=True)


