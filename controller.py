import os
import sys
import json
import subprocess
from subprocess import PIPE, STDOUT
from time import sleep
import datetime

from logger import Logger
from dumper import Dumper
from config import Config

CHANNEL = 'pcposc1_to_uhams02a'

'''
Todo:
  - files which are not in L1 will be removed from L2
'''

'''
Invariants :
 - L1: list of files on the LOCAL host
   =self.__get_fn_list_local()

 - L2: list of files that have already been synch'ed:
   =self.__get_fn_list_remote()

 - L3: list of files on the LOCAL host limited by STORAGE_SIZE (most recent)
 - L4: list of files to be synchronized as a batch (BATCH_SIZE) (oldest)
 
'''

class Controller():

    def __init__(self):
        self.__logger = Logger()

        self.__check_if_process_is_running()

        self.config = Config(CHANNEL).get()
        self.log(str(self.config))
        
        self.__L2 = []
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
            
            fn_list_local = self.__get_fn_list_local()
            self.log("L1 : " + str(fn_list_local))

            self.log("L2 : " + str(fn_list_synched))

            fn_list_local_recent = fn_list_local[-self.config.storage_size:]
            self.log("L3 : " + str(fn_list_local_recent))

            fn_list_to_sync = [x for x in fn_list_local_recent if x not in fn_list_synched]
            fn_list_to_sync_b = fn_list_to_sync[:self.config.batch_size]
            self.log("L4 : " + str(fn_list_to_sync_b))

            if (len(fn_list_to_sync_b)) == 0:
                sleep(self.config.connection_freq_whenempty)
                continue
            
            #self.__sync(fn_list_to_sync_b)
            self.__syncBatch(fn_list_to_sync_b)

            fn_list_synched += fn_list_to_sync_b
            self.log("L2': " + str(fn_list_synched))

            sleep(self.config.connection_freq)

    def __get_fn_list_remote(self):

        # ssh command:
        KEY = "-i " + self.config.loc_sshkey
        PORT = "-p " + str(self.config.rem_port)
        USER = "-l " + str(self.config.rem_user)
        CMD = "find " + self.config.rem_path + " -type f -printf \'%P \'"

        ssh_command = "ssh -q" + ' ' + KEY + ' ' + PORT + ' ' + USER + ' ' + self.config.rem_host + ' \"' + CMD + '\"'
        output = self.__popen(ssh_command)
        output_str = output.rstrip(' ')
        if (len(output_str)) == 0:
            return []
        
        fn_list = output_str.split(' ')
        fn_list.sort()
        return fn_list


    def __get_fn_list_local(self):
        '''
        Return example: ["3770/000 3770/001"]

        Command: find ./data/FRAMES/SCIBPB/RT/ -type f -printf '%P '"
          : -type f       = not to print folders
          : -printf '%P'  = to print file name with the path removed
          :         '%P ' = to insert a 'space'
        '''
        REGEX = "-regextype sed -regex \"" + self.config.loc_path + "[0-9]\{4\}\/[0-9]\{3\}\""
        
        cmd = "find" + ' ' + self.config.loc_path + ' '+ REGEX  + ' ' + "-type f -printf '%P '"
        output = self.__popen(cmd)
        fn_list_local = output.rstrip(' ').split(' ')
        fn_list_local.sort()
        return fn_list_local
    
    def __sync(self, fn_list):
        for fn in fn_list:
            ssh_cmd = "ssh -q -i " + self.config.loc_sshkey + " -p " + str(self.config.rem_port) + " -l " + str(self.config.rem_user)
            cmd = "rsync -Rpogt --progress " + self.config.loc_path + './' + fn + " " + self.config.rem_host + ":" + self.config.rem_path +  " " + "-e \'" + ssh_cmd + "\'"
            self.log(" ! RSYNC : " + cmd)
            subprocess.call(cmd, shell=True)

    def __syncBatch(self, fn_list):
        self.log(" ! --->  RSYNC : " + cmd)
        fnbatch = (" "+self.config.loc_path+'./').join(fn_list)
        ssh_cmd = "ssh -q -i " + self.config.loc_sshkey + " -p " + str(self.config.rem_port) + " -l " + str(self.config.rem_user)
        cmd = "rsync -Rpogt --progress " + self.config.loc_path+'./'+fnbatch + " " + self.config.rem_host + ":" + self.config.rem_path +  " " + "-e \'" + ssh_cmd + "\'"
        self.log(" ! --->  RSYNC : " + cmd)
        subprocess.call(cmd, shell=True)

    def __popen(self, cmd):
        self.log(" ! CALL : " + cmd)
        p = subprocess.Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
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
        #self.log("output: " + output)
        return output

