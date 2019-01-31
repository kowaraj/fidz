import os
import datetime
import json

class Dumper():

    def __init__(self, logger):
        self.logger = logger
        self.path = "./"

    def dump(self, fn_prefix, fn_list):
        ts = datetime.datetime.now().strftime("%j_%H%M%S.dump")
        p = self.path + fn_prefix + '_' + str(ts)
        if os.path.isfile(p):
            logger.log("Error: file already exists")
            exit(0)

        self.f = open(p, 'a')
        if not os.path.isfile(p):
            logger.log("Error: tracker file not found")
            exit(0)

            
        self.f.write('\n' + str(ts) + '\n')
        for fn in fn_list:
            self.f.write(fn+'\n')
            
        self.f.flush()



