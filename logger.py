import os

class Logger():

    def __init__(self):
        self.path = "./"
        self.fn = "logger.log"
        p = self.path + self.fn
        self.f = open(p, 'a')
        if not os.path.isfile(p):
            print "Error: log file not found"
            exit(0)
            

        self.f.write("Logger created @...")

    def log(self, line):
        self.f.write(line)
        self.f.flush()

    def logerror(self, line):
        self.f.write(line)
        self.f.flush()

