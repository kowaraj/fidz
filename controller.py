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
TODO:

  - ...

VERSION:

  - 2019.02.06


  
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

    def logsynched(self, fn_list):
        self.__logger.logsynched(fn_list)

    def logdeleted(self, fn_list):
        self.__logger.logdeleted(fn_list)

    def run(self):
        fn_list_synched = self.__get_fn_list_remote()
        while (True):
            self.log("\n"+str(datetime.datetime.now()))

            # 1. Prepare the list of files to be synchronized
            
            fn_list_local = self.__get_fn_list_local() # check local files
            self.log("L1 : (part of) " + str(fn_list_local[-(self.config.storage_size+3):]))

            self.log("L2 : " + str(fn_list_synched)) # check already synchronized files

            fn_list_local_recent = fn_list_local[-self.config.storage_size:] # ignore old local files
            self.log("L3 : " + str(fn_list_local_recent))

            fn_list_to_sync = [x for x in fn_list_local_recent if x not in fn_list_synched] # find files to be synchronized
            fn_list_to_sync_b = fn_list_to_sync[:self.config.batch_size]
            self.log("L4 : " + str(fn_list_to_sync_b))

            if (len(fn_list_to_sync_b)) != 0:

                # 2. Run the synchronization (rsync)

                self.__syncBatch(fn_list_to_sync_b)  # for single file mode: self.__sync(fn_list_to_sync_b)
                fn_list_synched += fn_list_to_sync_b
                self.log("L2': " + str(fn_list_synched))
                
            # 3. Delete oldest files from remote (clean-up)


            fn_list_to_del = fn_list_synched[:-self.config.storage_size] # find too old files on remote
            self.log("L5 : " + str(fn_list_to_del)) # too old files on remote (to be deleted)
            if (len(fn_list_to_del)) != 0:
                self.__delete_remote_files(fn_list_to_del)
                fn_list_synched = [x for x in fn_list_synched if x not in fn_list_to_del] # UPDATE synched list: Find files that were not deleted from remote

            # 4. Nothing to be done: Long wait; else: Short wait.
                
            if ( (len(fn_list_to_sync_b) == 0) and (len(fn_list_to_del) == 0) ):
                self.log("No missing files. Nothing to sync. Waiting...")
                sleep(self.config.connection_freq_whenempty)
            else: 
                sleep(self.config.connection_freq)

    def __get_fn_list_remote(self):
        '''
        Example of a complete command:
          ssh
          -q
          -i /home/ams/.ssh/ams_fcern2hawaii
          -p 25852
          -l amscern
          uhams02a.phys.hawaii.edu
          "find /home/cern/amscern/cern_to_hawaii/
             -regextype sed
             -regex '/home/cern/amscern/cern_to_hawaii/[0-9]\{4\}\/[0-9]\{3\}'
             -type f
             -printf '%P '
          "
        '''
        
        # ssh command:
        KEY = "-i " + self.config.loc_sshkey
        PORT = "-p " + str(self.config.rem_port)
        USER = "-l " + str(self.config.rem_user)
        REGEX = "-regextype sed -regex \'" + self.config.rem_path + "[0-9]\{4\}\/[0-9]\{3\}\'"

        CMD = "find " + self.config.rem_path + ' ' + REGEX  + ' ' + " -type f -printf \'%P \'"

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

        Example of a complete command:
          find
          /Data/FRAMES/SCIBPB/RT/
          -regextype sed
          -regex "/Data/FRAMES/SCIBPB/RT/[0-9]\{4\}\/[0-9]\{3\}"
          -type f
          -printf '%P '
        '''

        REGEX = "-regextype sed -regex \"" + self.config.loc_path + "[0-9]\{4\}\/[0-9]\{3\}\""
        
        cmd = "find" + ' ' + self.config.loc_path + ' '+ REGEX  + ' ' + "-type f -printf '%P '"
        output = self.__popen(cmd)
        fn_list_local = output.rstrip(' ').split(' ')
        fn_list_local.sort()
        return fn_list_local
    
    def __delete_remote_files(self, fn_list_to_del):
        self.logdeleted(fn_list_to_del)
        self.log("TO BE DELETED from REMOTE!!! : \n >>> " + str(fn_list_to_del))
        '''
        Example of a complete command:
          ssh
          -q
          -i /home/ams/.ssh/ams_fcern2hawaii
          -p 25852
          -l amscern
          uhams02a.phys.hawaii.edu
          "rm /home/cern/amscern/cern_to_hawaii/3782/510 /home/cern/amscern/cern_to_hawaii/3782/511 /home/cern/amscern/cern_to_hawaii/3783/.804.iGJ0Al"
        '''
        
        # ssh command:
        KEY = "-i " + self.config.loc_sshkey
        PORT = "-p " + str(self.config.rem_port)
        USER = "-l " + str(self.config.rem_user)

        fn_list = self.config.rem_path + (" " + self.config.rem_path).join(fn_list_to_del)
        CMD = "rm " + fn_list

        ssh_command = "ssh -q" + ' ' + KEY + ' ' + PORT + ' ' + USER + ' ' + self.config.rem_host + ' \"' + CMD + '\"'
        output = self.__popen(ssh_command)
        #self.__logger.send_sms_via_email("deleted: " + str(fn_list_to_del))
        self.log("output:" + output)

        
    def __sync(self, fn_list):
        self.logsynched(fn_list)
        for fn in fn_list:
            ssh_cmd = "ssh -q -i " + self.config.loc_sshkey + " -p " + str(self.config.rem_port) + " -l " + str(self.config.rem_user)
            cmd = "rsync -Rpogt --progress " + self.config.loc_path + './' + fn + " " + self.config.rem_host + ":" + self.config.rem_path +  " " + "-e \'" + ssh_cmd + "\'"
            self.log(" ! RSYNC : " + cmd)
            subprocess.call(cmd, shell=True)

    def __syncBatch(self, fn_list):
        self.logsynched(fn_list)
        
        '''
        Example of a complete command:
          rsync
          -Rpogt
          --progress
          /Data/FRAMES/SCIBPB/RT/./3783/833 /Data/FRAMES/SCIBPB/RT/./3783/834 /Data/FRAMES/SCIBPB/RT/./3783/835
          uhams02a.phys.hawaii.edu:/home/cern/amscern/cern_to_hawaii/
          -e 'ssh
              -q
              -i
              /home/ams/.ssh/ams_fcern2hawaii
              -p 25852
              -l amscern'
        '''

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
            self.log("error output: " + err)
            self.log("output: " + output)
            self.logerror("Error in __popen, return code = " + str(rc))
            self.__logger.send_sms_via_email("output = " + output + ", error = " + err)
            exit(0)

        # check error output
        if len(err) != 0:
            self.log("error output: " + err)
            self.log("output: " + output)
            self.logerror("Error in __popen, error len !=0 ")
            self.__logger.send_sms_via_email("output = " + output + ", error = " + err)
            exit(0)

        # check output
        return output



